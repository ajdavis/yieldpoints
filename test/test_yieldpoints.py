"""
Test YieldPoints.
"""

from __future__ import with_statement

from datetime import timedelta
from functools import partial
import time

from tornado import gen
from tornado.testing import AsyncTestCase, gen_test

import yieldpoints


class TestWaitAny(AsyncTestCase):
    @gen_test
    def test_basic(self):
        keys = list(range(3))
        callbacks = []
        for key in keys:
            callbacks.append((yield gen.Callback(key)))

        loop = self.io_loop
        loop.add_timeout(timedelta(seconds=0.01), callbacks[1])
        loop.add_timeout(timedelta(seconds=0.02), callbacks[0])
        loop.add_timeout(timedelta(seconds=0.03), callbacks[2])

        history = []
        while keys:
            key, response = yield yieldpoints.WaitAny(keys)
            history.append(key)
            keys.remove(key)

        self.assertEqual([1, 0, 2], history)

    @gen_test
    def test_get_result(self):
        # Test that WaitAny.get_result raises an exception if no results are
        # ready - this isn't a case that should ever arise, since gen.engine
        # checks is_ready() before calling get_result(), but let's make sure
        # it works anyway
        gen_callback = gen.Callback('key')
        callback = yield gen_callback
        runner = gen_callback.runner

        wait_any = yieldpoints.WaitAny(['key'])
        wait_any.start(runner)
        self.assertFalse(wait_any.is_ready())
        self.assertRaises(Exception, wait_any.get_result)

        callback('result')
        self.assertTrue(wait_any.is_ready())
        self.assertEqual(('key', 'result'), wait_any.get_result())


# Tests for the WithTimeout class
class TestWithTimeout(AsyncTestCase):
    @gen_test
    def test_timeout(self):
        yield gen.Callback('key')
        start = time.time()

        try:
            yield yieldpoints.WithTimeout(
                timedelta(seconds=0.1), 'key', self.io_loop)
        except yieldpoints.TimeoutException:
            # Expected
            pass
        else:
            self.fail("No TimeoutException raised")

        duration = time.time() - start
        # assertAlmostEquals with 'delta' not available until Python 2.7
        self.assertTrue(abs(duration - 0.1) < 0.01)
        yield yieldpoints.Cancel('key') # avoid LeakedCallbackError

    @gen_test
    def test_callback_after_timeout(self):
        # Check that a canceled callback can still be run without error
        callback = yield gen.Callback('key')

        try:
            yield yieldpoints.WithTimeout(
                timedelta(seconds=0.1), 'key', self.io_loop)
        except yieldpoints.TimeoutException:
            # Expected
            pass
        else:
            self.fail("No TimeoutException raised")

        callback() # No error

    @gen_test
    def test_timeout_cancel(self):
        (yield gen.Callback('key'))('result') # called immediately

        try:
            result = yield yieldpoints.WithTimeout(
                timedelta(seconds=0.1), 'key', self.io_loop)
        except yieldpoints.TimeoutException:
            self.fail("TimeoutException unexpectedly raised")

        self.assertEqual('result', result)

    @gen_test
    def test_timeout_cancel_with_delay(self):
        callback = yield gen.Callback('key')
        start = time.time()
        self.io_loop.add_timeout(
            timedelta(seconds=0.1), partial(callback, 'result'))

        try:
            result = yield yieldpoints.WithTimeout(
                timedelta(seconds=0.2), 'key', self.io_loop)
        except yieldpoints.TimeoutException:
            self.fail("TimeoutException unexpectedly raised")

        duration = time.time() - start
        self.assertTrue(abs(duration - 0.1) < 0.01)
        self.assertEqual('result', result)

    @gen_test
    def test_timeout_and_wait_any(self):
        # Make sure WithTimeout and WaitAny are composable
        yield gen.Callback('key')
        try:
            yield yieldpoints.WithTimeout(
                timedelta(seconds=0.01),
                yieldpoints.WaitAny(['key']),
                self.io_loop)
        except yieldpoints.TimeoutException:
            # Expected
            pass
        else:
            self.fail("No TimeoutException raised")

        yield yieldpoints.Cancel('key')

    @gen_test
    def test_timeout_and_task(self):
        # Make sure WithTimeout and gen.Task are composable
        try:
            yield yieldpoints.WithTimeout(
                timedelta(seconds=0.01),
                gen.Task(self.io_loop.add_callback),
                self.io_loop)
        except yieldpoints.TimeoutException:
            self.fail("TimeoutException unexpectedly raised")

        try:
            yield yieldpoints.WithTimeout(
                timedelta(seconds=0.01),
                gen.Task(self.io_loop.add_timeout, timedelta(seconds=0.1)),
                self.io_loop)
        except yieldpoints.TimeoutException:
            # Expected
            pass
        else:
            self.fail("No TimeoutException raised")


class TestCancel(AsyncTestCase):
    @gen_test
    def test_cancel(self):
        @gen.engine
        def test(callback):
            yield gen.Callback('key') # never called
            yield yieldpoints.Cancel('key')
            callback()

        try:
            yield gen.Task(test)
            pass
        except gen.LeakedCallbackError:
            self.fail("LeakedCallbackError was unexpectedly raised")

    @gen_test
    def test_cancel_unknown_key(self):
        @gen.engine
        def test(callback):
            yield yieldpoints.Cancel('key')
            callback()

        try:
            yield gen.Task(test)
        except gen.UnknownKeyError:
            # Success
            pass
        else:
            self.fail("UnknownKeyError not raised")

    @gen_test
    def test_callback_after_cancel(self):
        # Check that a canceled callback can still be run without error
        key_callback = yield gen.Callback('key')
        yield yieldpoints.Cancel('key')
        key_callback()


class TestCancelAll(AsyncTestCase):
    @gen_test
    def test_timeout(self):
        @gen.engine
        def test(callback):
            for i in range(2):
                yield gen.Callback(i) # never called
            yield yieldpoints.CancelAll()
            callback()

        try:
            yield gen.Task(test)
        except gen.LeakedCallbackError:
            self.fail("LeakedCallbackError was unexpectedly raised")
