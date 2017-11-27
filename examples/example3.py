'''
'''

import sys
sys.path.append("..")
sys.path.append(".")

import gatelogic
import os
import time

c = gatelogic.Controller()

def read_in(fname):
    if not os.path.exists(fname):
        with open(fname, 'wb') as fd:
            fd.write('')

    with open(fname, 'rb') as fd:
        data = fd.read()
    dd = {}
    for line in data.split('\n'):
        if not line:
            continue
        k, v = line.split(' ', 1)
        if k:
            dd[k] = v
    return dd

def write_out(fname, dd):
    with open(fname, 'wb') as fd:
        for k in sorted(dd.keys()):
            fd.write('%s %s\n' % (k, dd[k]))


class FlatFileQueryHub(gatelogic.QueryHub):
    def __init__(self, c, req_fname, res_fname):
        gatelogic.QueryHub.__init__(self, c)
        self.req_fname = req_fname
        self.res_fname = res_fname

        c.subscribe(self, self.write_out)

    def write_out(self, *args):
        write_out(self.req_fname, self.dump())

    def poll(self):
        self.update(read_in(self.res_fname))

class FlatFileReadableHub(gatelogic.ReadableHub):
    def __init__(self, c, fname):
        gatelogic.ReadableHub.__init__(self, c)
        self.fname = fname

    def poll(self):
        self.update(read_in(self.fname))

class FlatFileComputableHub(gatelogic.ComputableHub):
    def __init__(self, c, fname):
        gatelogic.ComputableHub.__init__(self, c)
        self.fname = fname
        c.subscribe(self, self.write_out)

    def write_out(self, *args):
        write_out(self.fname, self.dump())



plan_hub = FlatFileQueryHub(c, 'plan_sub.txt', 'plan_res.txt')
subdomain_hub = FlatFileQueryHub(c, 'subdomain_sub.txt', 'subdomain_res.txt')
toggle_hub = FlatFileQueryHub(c, 'toggle_sub.txt', 'toggle_res.txt')


def action(row, plan_hub, subdomain_hub, toggle_hub):
    domain = row.value
    if not domain:
        return None

    if toggle_hub.get('all_mitigations_disabled').value != 'True':
        return None

    qps = 100
    if plan_hub.get(domain).value in ('business', 'b'):
        qps = 500

    sd = (subdomain_hub.get(domain).value or '').split(' ')

    mitigation = \
                 domain + \
                 ' --qps=%s' % qps + \
                 ' '.join('--except=%s' % s for s in sd)

    return mitigation


signals = FlatFileReadableHub(c, 'signals_res.txt')
mitigations = FlatFileComputableHub(c, 'mitigations_sub.txt')

# maintain the map relationship
def on_new(_, kind, k, row):
    if kind == 'add':
        mitigations.maintain(k, action, row, plan_hub, subdomain_hub, toggle_hub)

def on_del(_, kind, k, _a):
    if kind == 'delete':
        mitigations.unmaintain(k)

c.subscribe(signals, on_new)
c.subscribe(signals, on_del)


while True:
    plan_hub.poll()
    subdomain_hub.poll()
    toggle_hub.poll()
    signals.poll()
    time.sleep(1)
