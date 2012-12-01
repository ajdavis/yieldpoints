"""
Test YieldPoints.
"""

from __future__ import with_statement

from datetime import timedelta
from functools import partial
import time
import unittest

from tornado import gen
from tornado.ioloop import IOLoop

import yieldpoints
from test.async_test_engine import async_test_engine


class TestWaitAny(unittest.TestCase):
    @async_test_engine()
    def test_basic(self, done):
        keys = list(range(3))
        callbacks = [(yield gen.Callback(key)) for key in keys]
        loop = IOLoop.instance()
        loop.add_timeout(timedelta(seconds=0.01), callbacks[1])
        loop.add_timeout(timedelta(seconds=0.02), callbacks[0])
        loop.add_timeout(timedelta(seconds=0.03), callbacks[2])

        history = []
        while keys:
            key, response = yield yieldpoints.WaitAny(keys)
            history.append(key)
            keys.remove(key)

        self.assertEqual([1, 0, 2], history)
        done()

    @async_test_engine()
    def test_timeout(self, done):
        @gen.engine
        def test(callback):
            yield gen.Callback('key') # never called
            start = time.time()
            key, result = yield yieldpoints.WaitAny(
                ['key'], deadline=timedelta(seconds=0.1))
            duration = time.time() - start
            self.assertEqual(None, key)
            self.assertEqual(None, result)
            # assertAlmostEquals with 'delta' not available until Python 2.7
            self.assertTrue(abs(duration - 0.1) < 0.01)
            callback()

        try:
            yield gen.Task(test)
        except gen.LeakedCallbackError:
            self.fail("LeakedCallbackError was unexpectedly raised")
        else:
            # Success
            done()

    @async_test_engine()
    def test_timeout_cancel(self, done):
        @gen.engine
        def test(callback):
            (yield gen.Callback('key'))('result') # called immediately
            start = time.time()
            key, result = yield yieldpoints.WaitAny(
                ['key'], deadline=timedelta(seconds=0.1))
            duration = time.time() - start
            self.assertEqual('key', key)
            self.assertEqual('result', result)
            self.assertTrue(duration < 0.01)
            callback()

        try:
            yield gen.Task(test)
        except gen.LeakedCallbackError:
            self.fail("LeakedCallbackError was unexpectedly raised")
        else:
            done()

    @async_test_engine()
    def test_timeout_cancel_with_delay(self, done):
        @gen.engine
        def test(callback):
            callback0 = yield gen.Callback('key') # called soon
            IOLoop.instance().add_timeout(timedelta(seconds=0.1),
                partial(callback0, 'result'))
            start = time.time()
            key, result = yield yieldpoints.WaitAny(
                ['key'], deadline=timedelta(seconds=0.2))
            duration = time.time() - start
            self.assertEqual('key', key)
            self.assertEqual('result', result)
            self.assertTrue(abs(duration - 0.1) < 0.01)
            callback()

        try:
            yield gen.Task(test)
        except gen.LeakedCallbackError:
            self.fail("LeakedCallbackError was unexpectedly raised")
        else:
            done()

class TestTimeout(unittest.TestCase):
    @async_test_engine()
    def test_timeout(self, done):
        yield yieldpoints.Timeout(timedelta(seconds=0.1), 'key')
        start = time.time()
        result = yield gen.Wait('key')
        duration = time.time() - start
        self.assertEqual(None, result)
        self.assertTrue(abs(duration - 0.1) < 0.01)
        done()


class TestCancel(unittest.TestCase):
    @async_test_engine()
    def test_timeout(self, done):
        @gen.engine
        def test(callback):
            yield gen.Callback('key') # never called
            yield yieldpoints.Cancel('key')
            callback()

        try:
            yield gen.Task(test)
        except gen.LeakedCallbackError:
            self.fail("LeakedCallbackError was unexpectedly raised")
        else:
            done()


class TestCancelAll(unittest.TestCase):
    @async_test_engine()
    def test_timeout(self, done):
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
        else:
            done()