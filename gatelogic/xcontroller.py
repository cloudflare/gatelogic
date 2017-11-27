import collections


class Cell(object):
    """ A Cell holds a ``value``. """
    def __init__(self, controller, default=None):
        self._controller = controller
        self._value = default

    def _get_value(self):
        self._controller._register_read(self)
        return self._value

    def _set_value(self, value):
        with self._controller._w( (None, 'update',), 'update'):
            if self._value == value:
                return

            if self._value is not value:
                self._value = value
                self._controller._dirty(self, 'set', None, value)

    """ Property containing the value of the Cell. You can read and set it. """
    value = property(_get_value, _set_value)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.value))

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self.value))

    def _destroy(self):
        self._controller.unsubscribe_all(self)


class ComputedCell(Cell):
    """ A ComputedCell holds a ``value`` which is computed by a given
    function. """
    def __init__(self, controller, fun, *args, **kwargs):
        self._controller = controller
        self._fun = (fun, args, kwargs)
        self._value = None

    def _run(self):
        with self._controller._w( ('update',), 'running'):
            self._controller._read = set()

            fun, args, kwargs = self._fun
            value = fun(*args, **kwargs)

            touched, self._controller._read = \
                self._controller._read, None

        self._controller._fix_subscriptions(self, touched)
        if self._value is not value:
            self._value = value
            self._controller._dirty(self, 'set', None, value)

    def _first_run(self):
        self._run()

    def __call__(self, _a, _b, _c, _d):
        self._run()


class Controller(object):
    cycle = None

    def __init__(self):
        self._read = None
        self._links = collections.defaultdict(set)
        self._rev_links = collections.defaultdict(set)

    def _dirty(self, obj, kind, k, v):
        assert kind in ('add', 'delete', 'set'), kind
        if obj in self._links:
            # copy to avoid changing size
            for fun in frozenset(self._links[obj]):
                fun, args = fun
                fun(obj, kind, k, v, *args)

    def _register_read(self, obj):
        if self.cycle == 'running':
            self._read.add( (obj, tuple()) )

    def subscribe(self, obj, fun, *args):
        self._links[obj].add( (fun, args) )
        self._rev_links[fun].add( (obj, args) )

    def unsubscribe(self, obj, fun, *args):
        dropped_objs = [obj]

        assert obj in self._links
        assert fun in self._rev_links
        self._links[obj].remove( (fun, args) )
        if not self._links[obj]:
            del self._links[obj]
        self._rev_links[fun].remove( (obj, args) )
        if not self._rev_links[fun]:
            del self._rev_links[fun]
            dropped_objs.append(fun)

        for obj in set(dropped_objs):
            if hasattr(obj, '_on_lost_reference'):
                obj._on_lost_reference()

    def unsubscribe_all(self, obj):
        while obj in self._rev_links:
            funs = list(self._rev_links[obj])
            if len(funs) < 1:
                print "ERROR: _rev_links desynchronized!"
                break
            fun, args = funs[0]
            self.unsubscribe(fun, obj, *args)

    def _fix_subscriptions(self, fun, new_subscribed):
        old_subscribed = self._rev_links.get(fun, set())

        for obj, args in new_subscribed - old_subscribed:
            self.subscribe(obj, fun, *args)
        for obj, args in old_subscribed - new_subscribed:
            self.unsubscribe(obj, fun, *args)

    def _w(self, ok_cycles, new_cycle):
        o = self
        ok_cycles = set(ok_cycles)
        class controlled_execution:
            def __enter__(self):
                self.old_cycle = o.cycle
                if self.old_cycle not in ok_cycles:
                    raise Exception("Cycle %r is not in %r" % (self.old_cycle, ok_cycles))
                # print "cycle = %r -> %r" % (self.old_cycle, new_cycle)
                o.cycle = new_cycle

            def __exit__(self, type, value, traceback):
                # print "rcycle %r -> %r" % (o.cycle, self.old_cycle,)
                o.cycle = self.old_cycle
        return controlled_execution()

    def _referenced_by(self, obj):
        if obj in self._links:
            return set(self._links[obj])
        return set()

    def is_empty(self):
        return not bool(self._links)
