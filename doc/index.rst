=======================================================
YieldPoints: Simple extensions to Tornado's gen module.
=======================================================

.. module:: yieldpoints

.. image:: _static/yield.png
    :align: center

Simple extensions to Tornado's gen_ module.

.. _gen: http://www.tornadoweb.org/documentation/gen.html

Examples
========
Use :class:`~yieldpoints.WaitAny` to begin two tasks and handle their results
in the order completed:

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

If you begin a task but don't wait for it, use :class:`~yieldpoints.Cancel`
or to :class:`~yieldpoints.CancelAll` avoid a ``LeakedCallbackError``:

.. doctest::

    >>> @gen.engine
    ... def f():
    ...     yield gen.Callback('key') # never called
    ...     yield yieldpoints.Cancel('key')
    ...     IOLoop.instance().stop()
    ...
    >>> f()
    >>> IOLoop.instance().start()

Wait with a timeout. :class:`~yieldpoints.WithTimeout` can take a
``YieldPoint`` or a key name as its second argument:

.. doctest::

    >>> @gen.engine
    ... def f():
    ...     callback = yield gen.Callback('key') # never called
    ...     try:
    ...         key, result = yield yieldpoints.WithTimeout(
    ...             timedelta(seconds=0.1), 'key')
    ...     except yieldpoints.TimeoutException:
    ...         print 'Timeout!'
    ...         IOLoop.instance().stop()
    ...
    >>> f()
    >>> IOLoop.instance().start()
    Timeout!

Contents
========
.. toctree::
    examples/index
    classes
    changelog

Source
======
Is on GitHub: https://github.com/ajdavis/yieldpoints

Bug Reports and Feature Requests
================================
Also on GitHub: https://github.com/ajdavis/yieldpoints/issues

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

