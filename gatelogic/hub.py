import copy

from .xcontroller import Cell, ComputedCell


class _GenericHub(object):
    def __init__(self, controller):
        self.extra = {}
        self._ns = {}
        self._controller = controller

    def keys(self):
        return self._ns.keys()

    def has_key(self, key):
        return key in self._ns

    def _add(self, key, cell):
        self._ns[key] = cell
        if isinstance(cell, ComputedCell):
            cell._first_run()
        self._controller.subscribe(cell, self._on_change, key)
        self._controller._dirty(self, 'add', key, cell)
        return cell

    def _delete(self, key):
        cell = self._ns[key]
        del self._ns[key]
        self._controller.unsubscribe(cell, self._on_change, key)
        self._controller._dirty(self, 'delete', key, None)

    def _update(self, data, partial, extra):
        self.extra = copy.deepcopy(extra)

        read = dict(data)
        old = set(self._ns.iterkeys())
        new = set(read.iterkeys())

        # 0) if changed, update
        for k in old & new:
            # it is possible that during update of previus cell an _ns
            # item was removed.
            if k in self._ns and self._ns[k].value != read[k]:
                self._ns[k].value = read[k]

        if partial:
            return

        # 1) we do care about extra data
        for k in new - old:
            if k not in self._ns:
                cell = Cell(self._controller)
                cell.value = read[k]
                self._add(k, cell)
            else:
                self._ns[k].value = read[k]

        # 2) delete the deleted stuff
        for k in old - new:
            if k in self._ns:
                self._delete(k)

    def _on_change(self, obj, kind, _key, value, key):
        # Value of a cell was modified.
        # TODO: maybe fill key in this message
        assert kind in ('set',)
        self._controller._dirty(self, kind, key, obj)

    def dump(self):
        return dict((k, v._value) for k, v in self._ns.iteritems())


class ReadableHub(_GenericHub):
    def update(self, data, extra={}):
        """ Update all the keys and values using data from the given dictionary. """
        with self._controller._w( (None,), 'update'):
            self._update(data, False, extra)

    def get(self, key):
        """ Get Cell for a ``key``. Raise exception if key doesn't exist. """
        if key not in self._ns:
            raise KeyError(key)
        return self._ns[key]


class ComputableHub(_GenericHub):
    def maintain(self, key, fun, *args, **kwargs):
        """ Set ``key`` to be a ComputedCell with given function to
        compute the value."""
        if key in self._ns:
            raise KeyError(key)
        with self._controller._w( (None, 'update'), 'update'):
            v = self._add(key, ComputedCell(self._controller, fun, *args, **kwargs))
            return v

    def unmaintain(self, key):
        """ Remove ComputedCell for ``key``. """
        if key not in self._ns:
            raise KeyError(key)
        v = self._ns[key]
        self._delete(key)
        v._destroy()

    def get(self, key):
        """ Get ComputedCell for a ``key``. Raise exception if key doesn't exist. """
        if key not in self._ns:
            raise KeyError(key)
        return self._ns[key]


class QueryHub(_GenericHub):
    _last_data = None

    def get(self, key, default=None):
        """ Get Cell for a ``key``. During a computation cycle create
        one if it doesn't exist yet."""
        already_present = False
        if self._last_data:
            if key in self._last_data:
                default = self._last_data[key]
                already_present = True

        if key not in self._ns:
            if self._controller.cycle not in ('running',) and already_present == False:
                # key error if not within a running stage
                raise KeyError(key)
            cell = Cell(self._controller, default)
            self._add(key, cell)
            def fun():
                if len(self._controller._referenced_by(cell)) == 1:
                    self._delete(key)
            cell._on_lost_reference = fun
            return cell
        return self._ns[key]

    def update(self, data, extra={}):
        """ Update all the keys and values using data from the given dictionary. """
        with self._controller._w( (None,), 'update'):
            self._last_data = copy.deepcopy(data)
            self._update(data, True, extra)
