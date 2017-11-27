Gatelogic - somewhat reactive programming framework
=========

Gatelogic is a functional reactive programming / software
transactional memory inspired framework.

In classic FRP programming model, the signal graph is defined on the
start and doesn't change during the lifetime of a program. For our
usage we needed something more dynamic. We also wanted to do express
the computable code in an easy to understand Python, as opposed to a
classic composition of pure functions.

The idea is to write pretty simple, side-effect free functions that
describe some business logic, while allowing them to dynamically
"subscribe" arbitrary signal sources.

For example, a basic "action" code could look like:

    def action(row):
        if confirm_hub.get('all_mitigations_enabled').value != 'True':
            return None

This will actually "subscribe" to
`confirm_hub/all_mitigations_enabled` input signal. Note, that this
subscription is _declared_ in the code, as opposed to predefined as
input. Change of that input signal value will trigger recomputation of
all dependent action functions.

To run the tests type:

    make

Usage
-----

The Gatelogic code is a library, which lacks integration with any
external systems. You can review the examples directory, to see
simplistic integration with flat files, but for anything more serious
you probably need to write an intermediate database integration layer.

To dig into the code look at:

Very simple example:

    ./venv/bin/python example/example1.py

Larger example:

    ./venv/bin/python example/example2.py

The tests:

    tests/test_basic.py


The closest thing available in Python world is Trellis:

 - http://peak.telecommunity.com/DevCenter/Trellis

If you are interested in FRP, please also take a look at ELM and
Flapjax.



Introduction
------------

We wanted to write a piece of Python in reactive programming
style. Unfortunately, in the usual RP style you can't create dynamic
subscriptions, which we badly needed. We needed express logic like
this:

```.py
  def action():
        if checkbox_one == True:
            if checkbox_two == True:
                return "option two"
        return "option one"
```

This code is supposed to:

1) show the user ``checkbox_one``
2) for time being the return value of our function is ``option one``
3) the function should automatically recompute when the user sets the checkbox
4) then show the user ``checkbox_two``
5) if checkbox two is set, the value will be ``option two``
6) if the ``checkbox_one`` is unset, the ``checkbox_two`` should dissapear

Basically, I wanted two things:
 - recompute the function when any of the inputs change
 - support dynamic subscriptions from the pseudo-reactive code


The code has two abstraction layers. First there are primary objects:

 * `gatelogic.Controller`: A class (should be used as a
   singleton) storing the subscriptions. It's responsible to recompute
   cells when needed.
 * `gatelogic.Cell`: A cell that holds an immediate value. You
   can subscribe to get updates.
 * `gatelogic.ComputedCell`: A cell that holds a computed
   value. You can subscribe to get updates.


More important are the higher level abstractions, the hubs. A hub is a
dictionary that holds `Cells` or `ComputedCells`. You can subscribe to
a hub to get notified on insertions, deletions or changes of values.
There are three types of hubs:

 * `gatelogic.ReadableHub`: A hub that is controlled outside
   the application. For example it can contain data from a file or
   database.

 * `gatelogic.ComputableHub`: A hub that contains
   `ComputedCells`, and is managed by our application. Most often data
   from this hub is copied over to an external resource, like a file.

 * `gatelogic.QueryHub`: A hub that is responsible for a
   request-response type of communication. A `ComputedCell` can
   request a Cell from that hub, the Cell will be automatically
   created. And a change in that Cell value will trigger recomputation
   of the ComputedCells that rely on it.

Cells can technically live outside of Hubs but there currently isn't a
need for that.

When using the library there are two internal modes of execution:

 * "update" cycle
 * normal code, outside of either previous

The presence of "update" cycle is there to ensure the hubs don't
change values from your code. For example you can't modify ReadableHub
from within a computation.
