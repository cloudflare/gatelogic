import gatelogic
import os
import unittest


class TestBasic(unittest.TestCase):
    def test_basic(self):
        c = gatelogic.Controller()

        egress = gatelogic.ComputableHub(c)
        hub = gatelogic.QueryHub(c)

        def action():
            if hub.get('item').value == None:
                return None

            return hub.get('item').value + 1

        egress.maintain('1', action)

        self.assertEqual(hub.keys(), ['item'])
        self.assertEqual(egress.keys(), ['1'])

        self.assertTrue(hub.get('item').value is None)
        self.assertTrue(egress.get('1').value is None)

        hub.get('item').value = 41
        self.assertTrue(hub.get('item').value is 41)
        self.assertTrue(egress.get('1').value is 42)

        # test GC
        egress.unmaintain('1')
        self.assertTrue(c.is_empty())


    def test_dynamic(self):
        c = gatelogic.Controller()

        egress = gatelogic.ComputableHub(c)
        hub = gatelogic.QueryHub(c)

        def action():
            if hub.get('one').value:
                if hub.get('two').value:
                    return 'a'

            return hub.get('three').value

        egress.maintain('1', action)

        self.assertEqual(hub.keys(), ['three', 'one'])
        self.assertEqual(egress.keys(), ['1'])
        self.assertEqual(egress.get('1').value, None)

        hub.get('one').value = True

        self.assertEqual(hub.keys(), ['three', 'two','one'])
        self.assertEqual(egress.get('1').value, None)

        hub.get('two').value = True

        self.assertEqual(hub.keys(), ['two', 'one'])
        self.assertEqual(egress.get('1').value, 'a')

        egress.unmaintain('1')
        self.assertTrue(c.is_empty())


    def test_two_layers(self):
        c = gatelogic.Controller()

        egress = gatelogic.ComputableHub(c)
        mid = gatelogic.ComputableHub(c)
        hub = gatelogic.QueryHub(c)

        def action1():
            if hub.get('one').value:
                if hub.get('two').value:
                    return 'a'
            return 'b'

        def action2():
            if hub.get('three').value:
                return '%s-%s' % (hub.get('three').value, mid.get('1').value)
            return 'c'

        mid.maintain('1', action1)
        egress.maintain('2', action2)

        self.assertEqual(hub.keys(), ['three', 'one'])
        self.assertEqual(mid.keys(), ['1'])
        self.assertEqual(egress.keys(), ['2'])

        hub.get('one').value = True
        self.assertEqual(hub.keys(), ['three', 'two','one'])
        self.assertEqual(mid.get('1').value, 'b')
        self.assertEqual(egress.get('2').value, 'c')

        hub.get('three').value = 'x'
        self.assertEqual(hub.keys(), ['three', 'two','one'])
        self.assertEqual(mid.get('1').value, 'b')
        self.assertEqual(egress.get('2').value, 'x-b')

        hub.get('two').value = True

        self.assertEqual(hub.keys(), ['three', 'two', 'one'])
        self.assertEqual(mid.get('1').value, 'a')
        self.assertEqual(egress.get('2').value, 'x-a')

        egress.unmaintain('2')
        self.assertFalse(c.is_empty())
        egress.maintain('2', action2)

        mid.unmaintain('1')
        self.assertFalse(c.is_empty())

        egress.unmaintain('2')
        self.assertTrue(c.is_empty())


    def test_no_recount(self):
        c = gatelogic.Controller()

        egress = gatelogic.ComputableHub(c)
        hub = gatelogic.QueryHub(c)

        counter = [0]

        def action():
            counter[0] += 1
            if hub.get('item').value == None:
                return None

            return hub.get('item').value + 1

        self.assertEqual(counter[0], 0)
        egress.maintain('1', action)
        self.assertEqual(counter[0], 1)

        hub.get('item').value = 41
        self.assertEqual(counter[0], 2)
        hub.get('item').value = 41
        self.assertEqual(counter[0], 2)


    def test_coverage(self):
        c = gatelogic.Controller()
        egress = gatelogic.ComputableHub(c)

        def action():
            pass
        egress.maintain('1', action)

        with self.assertRaises(KeyError):
            egress.maintain('1', None)

        with self.assertRaises(KeyError):
            egress.unmaintain('xxxx1')

        with self.assertRaises(KeyError):
            egress.get('xxxx1')

        repr(egress.get('1'))
        str(egress.get('1'))
        self.assertTrue(egress.has_key('1'))
        self.assertFalse(egress.has_key('2'))

        rh = gatelogic.ReadableHub(c)
        with self.assertRaises(KeyError):
            rh.get(1)
        rh.update({1:2})
        self.assertEqual(rh.get(1).value, 2)


    def test_update(self):
        c = gatelogic.Controller()

        hub = gatelogic.ReadableHub(c)
        hub.update({1:2})
        self.assertFalse(c.is_empty())

        hub.update({1:2})
        self.assertFalse(c.is_empty())

        hub.update({1:3})
        self.assertFalse(c.is_empty())
        self.assertEqual(hub.dump(), {1:3})

        hub.update({})
        self.assertTrue(c.is_empty())

        self.assertEqual(hub.dump(), {})


    def test_update_complex(self):
        c = gatelogic.Controller()

        egress = gatelogic.ComputableHub(c)
        hub = gatelogic.QueryHub(c)

        def action():
            if hub.get('item').value == None:
                return None

            return hub.get('item').value + 1

        egress.maintain('1', action)

        self.assertEqual(hub.keys(), ['item'])
        self.assertEqual(egress.keys(), ['1'])

        self.assertTrue(hub.get('item').value is None)
        self.assertTrue(egress.get('1').value is None)

        hub.get('item').value = 41
        self.assertTrue(hub.get('item').value is 41)
        self.assertTrue(egress.get('1').value is 42)

        hub.update({'other':2})
        self.assertEqual(hub.keys(), ['item'])
        self.assertEqual(egress.keys(), ['1'])

        egress.unmaintain('1')
        self.assertTrue(c.is_empty())


    def test_update_conflict(self):
        c = gatelogic.Controller()

        egress = gatelogic.ComputableHub(c)
        hub = gatelogic.QueryHub(c)

        def action():
            if hub.get('item0').value == None:
                hub.get('item1').value
                hub.get('item2').value
                return None

            return hub.get('item0').value + 1

        egress.maintain('1', action)

        self.assertEqual(set(hub.keys()), set(['item1', 'item2', 'item0']))
        self.assertEqual(egress.keys(), ['1'])

        self.assertTrue(hub.get('item0').value is None)
        self.assertTrue(hub.get('item1').value is None)
        self.assertTrue(hub.get('item2').value is None)
        self.assertTrue(egress.get('1').value is None)

        # Failure of this test depends on the order of sets:
        # >>> set(['item0', 'item1', 'item2', 'other'])
        # set(['item2', 'item0', 'item1', 'other'])
        hub.update({'item0':1, 'item1':1, 'item2': 2, 'other':3})
        self.assertEqual(hub.keys(), ['item0'])
        self.assertEqual(egress.keys(), ['1'])
        self.assertTrue(egress.get('1').value is 2)

        egress.unmaintain('1')
        self.assertTrue(c.is_empty())

    def test_forever(self):
        c = gatelogic.Controller()

        egress = gatelogic.ComputableHub(c)
        hub = gatelogic.QueryHub(c)

        def action():
            r = hub.get('1').value or 0
            g = egress.get('1').value or 0
            return r + g

        egress.maintain('1', action)

        with self.assertRaises(RuntimeError):
            hub.get('1').value = 41

