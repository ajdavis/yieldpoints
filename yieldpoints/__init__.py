from functools import partial

from tornado import gen
from tornado.gen import UnknownKeyError
from tornado.ioloop import IOLoop


version_tuple = (0, 1)

version = '.'.join(map(str, version_tuple))
"""Current version of YieldPoints."""


__all__ = [
    'TimeoutException', 'WaitAny', 'WithTimeout', 'Timeout', 'Cancel',
    'CancelAll'
]


def cancel(runner, key):
    try:
        runner.pending_callbacks.remove(key)
    except KeyError:
        raise UnknownKeyError("key %r is not pending" % key)


class TimeoutException(Exception):
    pass


class WaitAny(gen.YieldPoint):
    """Wait for several keys, and continue when the first of them is complete.

    Inspired by Ben Darnell in `a conversation on the Tornado mailing list
    <https://groups.google.com/d/msg/python-tornado/PCHidled01M/B7sDjNP2OpQJ>`_.
    """
    def __init__(self, keys):
        self.keys = keys

    def start(self, runner):
        self.runner = runner

    def is_ready(self):
        return any(self.runner.is_ready(key) for key in self.keys)

    def get_result(self):
        for key in self.keys:
            if self.runner.is_ready(key):
                return key, self.runner.pop_result(key)
        raise Exception("no results found")


class WithTimeout(gen.YieldPoint):
    """Wait for a YieldPoint or a timeout, whichever comes first.

    :Parameters:
      - `deadline`: A timestamp or timedelta
      - `yield_point`: A ``gen.YieldPoint`` or a key
      - `io_loop`: Optional custom ``IOLoop`` on which to run timeout
    """
    def __init__(self, deadline, yield_point, io_loop=None):
        self.deadline = deadline
        if isinstance(yield_point, gen.YieldPoint):
            self.yield_point = yield_point
        else:
            # yield_point is actually a key, e.g. gen.Callback('key')
            self.yield_point = gen.Wait(yield_point)
        self.expired = False
        self.timeout = None
        self.io_loop = io_loop or IOLoop.instance()

    def start(self, runner):
        self.runner = runner
        self.timeout = self.io_loop.add_timeout(self.deadline, self.expire)
        self.yield_point.start(runner)

    def is_ready(self):
        return self.expired or self.yield_point.is_ready()

    def get_result(self):
        if self.expired:
            raise TimeoutException()

        return self.yield_point.get_result()

    def expire(self):
        self.expired = True
        self.runner.run()


class Cancel(gen.YieldPoint):
    """Cancel a key so ``gen.engine`` doesn't raise a LeakedCallbackError
    """
    def __init__(self, key):
        self.key = key

    def start(self, runner):
        cancel(runner, self.key)

    def is_ready(self):
        return True

    def get_result(self):
        return None


class CancelAll(gen.YieldPoint):
    """Cancel all keys for which the current coroutine has registered callbacks
    """
    def start(self, runner):
        # Copy the set, since cancel() shrinks it during iteration
        for key in runner.pending_callbacks.copy():
            cancel(runner, key)

    def is_ready(self):
        return True

    def get_result(self):
        return None
