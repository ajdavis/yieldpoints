=======================================================
yieldpoints: Synchronization primitives for Tornado coroutines
=======================================================

.. module:: yieldpoints

Simple extensions to Tornado's gen_ module.

.. _gen: http://www.tornadoweb.org/documentation/gen.html

Examples
========

Begin two tasks and handle their results in the order completed:

.. doctest::

    >>> @gen.engine
    ... def f():
    ...     callback0 = yield gen.Callback(0)
    ...     callback1 = yield gen.Callback(1)
    ...
    ...     # Fire callback1 soon, callback0 later
    ...     IOLoop.instance().add_timeout(
    ...         timedelta(seconds=0.1), partial(callback1, 'foo'))
    ...
    ...     IOLoop.instance().add_timeout(
    ...         timedelta(seconds=0.2), partial(callback0, 'bar'))
    ...
    ...     keys = set([0, 1])
    ...     while keys:
    ...         key, result = yield yieldpoints.WaitAny(keys)
    ...         print 'key:', key, ', result:', result
    ...         keys.remove(key)
    ...     IOLoop.instance().stop()
    ...
    >>> f()
    >>> IOLoop.instance().start()
    key: 1 , result: foo
    key: 0 , result: bar

Register a timeout and wait for it later on:

.. doctest::

    >>> @gen.engine
    ... def f():
    ...     start = time.time()
    ...     yield yieldpoints.Timeout(timedelta(seconds=0.1), 'key')
    ...     print 'going to wait'
    ...     yield gen.Wait('key')
    ...     print 'waited, took %.1f seconds' % (time.time() - start)
    ...     IOLoop.instance().stop()
    ...
    >>> f()
    >>> IOLoop.instance().start()
    going to wait
    waited, took 0.1 seconds

Begin a task and decline not to wait for it, while avoiding a
``LeakedCallbackError``:

.. doctest::

    >>> @gen.engine
    ... def f():
    ...     yield gen.Callback('key') # never called
    ...     yield yieldpoints.Cancel('key')
    ...     IOLoop.instance().stop()
    ...
    >>> f()
    >>> IOLoop.instance().start()

Contents
========
.. toctree::
    examples/index
    classes
    faq
    changelog

Source
======
Is on GitHub: https://github.com/ajdavis/yieldpoints

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

