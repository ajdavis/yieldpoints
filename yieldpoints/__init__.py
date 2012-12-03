from functools import partial

from tornado import gen
from tornado.gen import UnknownKeyError
from tornado.ioloop import IOLoop


version_tuple = (0, 1)

version = '.'.join(map(str, version_tuple))
"""Current version of YieldPoints."""


__all__ = ['YieldPoints', 'Cancel', 'CancelAll', 'Timeout']


class YieldPointsBase(gen.YieldPoint):
    def cancel(self, runner, key):
        try:
            runner.pending_callbacks.remove(key)
        except KeyError:
            raise UnknownKeyError("key %r is not pending" % key)


class WaitAny(YieldPointsBase):
    """Wait for several keys, and continue when the first of them is complete.

    Inspired by Ben Darnell in `a conversation on the Tornado mailing list
    <https://groups.google.com/d/msg/python-tornado/PCHidled01M/B7sDjNP2OpQJ>`_.
    """
    def __init__(self, keys, deadline=None, io_loop=None):
        self.keys = keys
        self.deadline = deadline
        self.expired = False
        self.timeout = None
        self.io_loop = io_loop or IOLoop.instance()

    def start(self, runner):
        self.runner = runner
        if self.deadline is not None:
            self.timeout = self.io_loop.add_timeout(self.deadline, self.expire)

    def is_ready(self):
        return self.expired or any(
            self.runner.is_ready(key) for key in self.keys)

    def get_result(self):
        if self.expired:
            return None, None

        for key in self.keys:
            if self.runner.is_ready(key):
                return key, self.runner.pop_result(key)
        raise Exception("no results found")

    def expire(self):
        self.expired = True
        for key in self.keys:
            self.cancel(self.runner, key)
        self.runner.run()


class Cancel(YieldPointsBase):
    """Cancel a key so ``gen.engine`` doesn't raise a LeakedCallbackError
    """
    def __init__(self, key):
        self.key = key

    def start(self, runner):
        self.cancel(runner, self.key)

    def is_ready(self):
        return True

    def get_result(self):
        return None


class CancelAll(YieldPointsBase):
    """Cancel all keys for which the current coroutine has registered callbacks
    """
    def start(self, runner):
        # Copy the set, since self.cancel() shrinks it during iteration
        for key in runner.pending_callbacks.copy():
            self.cancel(runner, key)

    def is_ready(self):
        return True

    def get_result(self):
        return None


class Timeout(YieldPointsBase):
    """Register a timeout for which the coroutine can later wait with
    ``gen.Wait``.
    """
    def __init__(self, deadline, key, io_loop=None):
        self.deadline = deadline
        self.key = key
        self.io_loop = io_loop or IOLoop.instance()

    def start(self, runner):
        self.runner = runner
        runner.register_callback(self.key)
        self.io_loop.add_timeout(self.deadline, partial(self.expire))

    def expire(self):
        self.runner.set_result(self.key, None)
        self.runner.run()

    def is_ready(self):
        # Like gen.Callback: is_ready() returns True so coroutine can proceed
        return True

    def get_result(self):
        return None
