'''
This is a pretty complex example. To run:

    ../venv/bin/python example2.py

And do the following:

1) add a line to signals_res.txt

    1 example.com

2) observe mitigations_sub.txt containing

    1 None

3) observe confirms_sub.txt containing

    all_mitigations_enabled None

4) supply that confirmation by entering this to confirms_res.txt file

    all_mitigations_enabled True

5) observe mitigations.txt

    1 example.com

6) add a line to signals_res.txt

    2 flooded.com

7) supply subdomains in subdomains_res.txt

    flooded.com www ns1

8) observe produced mitigations in mitigations_sub.txt:

    1 example.com
    2 flooded.com --except=www --except=ns1
'''

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



confirm_hub = FlatFileQueryHub(c, 'confirms_sub.txt', 'confirms_res.txt')
subdomain_hub = FlatFileQueryHub(c, 'subdomains_sub.txt', 'subdomains_res.txt')


def action(row):
    if not row.value:
        return None

    if confirm_hub.get('all_mitigations_enabled').value != 'True':
        return None


    pattern = row.value

    if pattern == "example.com":
        return pattern


    if pattern.startswith('*.www'):
        return row.value

    s = subdomain_hub.get(pattern).value
    if not s:
        return None

    s = s.split(' ')

    return '%s %s' % (pattern, ' '.join('--except=%s' % (p,) for p in s))


signals = FlatFileReadableHub(c, 'signals_res.txt')
mitigations = FlatFileComputableHub(c, 'mitigations_sub.txt')

# maintain the map relationship
def on_new(_, kind, k, row):
    if kind == 'add':
        mitigations.maintain(k, action, row)

def on_del(_, kind, k, _a):
    if kind == 'delete':
        mitigations.unmaintain(k)

c.subscribe(signals, on_new)
c.subscribe(signals, on_del)


while True:
    confirm_hub.poll()
    subdomain_hub.poll()
    signals.poll()
    time.sleep(1)
