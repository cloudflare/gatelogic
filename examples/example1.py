'''
Simple example. To run:

    ../venv/bin/python example1.py

And observe the printed values. That's it.
'''

import gatelogic

c = gatelogic.Controller()


ingress = gatelogic.ReadableHub(c)
hub = gatelogic.QueryHub(c)
egress = gatelogic.ComputableHub(c)


def action(cell):
    v = cell.value
    if v == None:
        return
    return (hub.get(v).value or 1) * (hub.get(v).value or 1)


def ensure_map(_, kind, key, cell):
    if kind == 'add':
        egress.maintain(key, action, cell)
    if kind == 'delete':
        egress.unmaintain(key)

c.subscribe(ingress, ensure_map)


def sync(*args):
    print egress.dump()
c.subscribe(egress, sync)



ingress.update({1:1})
hub.update({1:2})
ingress.update({1:1, 2:2})
hub.update({2:2})

ingress.update({})

c.unsubscribe(egress, sync)
c.unsubscribe(ingress, ensure_map)
assert c.is_empty()
