# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import sys
import json
import time
import asyncio
import logging
from unittest import TestCase

import naz


logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.DEBUG)


class TestCorrelater(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_correlater.TestCorrelater.test_something
    """

    def setUp(self):
        self.logger = logging.getLogger("naz.test")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel("DEBUG")

        self.max_ttl = 0.2  # sec
        self.correlater = naz.correlater.SimpleCorrelater(max_ttl=self.max_ttl)

    def tearDown(self):
        pass

    def _run(self, coro):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def test_put(self):
        length = 7
        for i in range(0, length):
            self._run(
                self.correlater.put(
                    sequence_number=str(i),
                    log_id="log_id-" + str(i),
                    hook_metadata="hook_metadata-" + str(i),
                )
            )
        self.assertEqual(len(self.correlater.store.keys()), length)
        self.assertEqual(self.correlater.store["0"]["log_id"], "log_id-0")
        self.assertEqual(self.correlater.store["4"]["hook_metadata"], "hook_metadata-4")

    def test_put_max_ttl(self):
        length = 5
        for i in range(0, length):
            self._run(
                self.correlater.put(
                    sequence_number=str(i),
                    log_id="log_id-" + str(i),
                    hook_metadata="hook_metadata-" + str(i),
                )
            )
        self.assertEqual(len(self.correlater.store.keys()), length)

        time.sleep(self.max_ttl + 0.2)
        self._run(
            self.correlater.put(
                sequence_number="end_ttl",
                log_id="log_id-end_ttl",
                hook_metadata="hook_metadata-end_ttl",
            )
        )
        self.assertEqual(len(self.correlater.store.keys()), 1)
        self.assertEqual(self.correlater.store["end_ttl"]["hook_metadata"], "hook_metadata-end_ttl")

    def test_get(self):
        self._run(
            self.correlater.put(
                sequence_number="sequence_number", log_id="MyLogID", hook_metadata="MyHookMetadata"
            )
        )
        self.assertEqual(len(self.correlater.store.keys()), 1)
        log_id, hook_metadata = self._run(self.correlater.get(sequence_number="sequence_number"))
        self.assertEqual(log_id, "MyLogID")
        self.assertEqual(hook_metadata, "MyHookMetadata")


class TestBenchmarkCorrelater(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_correlater.TestBenchmarkCorrelater.test_something
    """

    def setUp(self):
        self.logger = logging.getLogger("naz.test")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel("DEBUG")

        self.max_ttl = 0.2  # sec
        self.correlater = naz.correlater.SimpleCorrelater(max_ttl=self.max_ttl)

    def tearDown(self):
        pass

    def _run(self, coro):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def test_put_benchmark(self):
        now = time.monotonic()
        far_back = now - (self.max_ttl * 10)

        # first store 100K items
        f = open("tests/correlater_store_with_100K_items.json", "r")
        x = f.read()
        f.close()
        y = json.loads(x)
        for key in list(y.keys()):
            y[key]["stored_at"] = far_back
        self.correlater.store = y

        # wait for all 100K items to reach max ttl
        time.sleep(self.max_ttl + 0.2)
        # then try to put in a new item thus triggering a delete of all 100K items
        # and check how long that operation takes
        start = time.monotonic()
        self._run(
            self.correlater.put(
                sequence_number="end_ttl",
                log_id="log_id-end_ttl",
                hook_metadata="hook_metadata-end_ttl",
            )
        )
        end = time.monotonic()
        diff = end - start
        print(
            "putting 1 item while the store already has 100K items that have reached max_ttl took {0} seconds.".format(
                diff
            )
        )
        self.assertTrue(
            diff < 0.1,
            msg="putting 1 item while the store already has 100K items that have reached max_ttl should not take longer than 0.1 seconds",
        )
        self.assertEqual(len(self.correlater.store.keys()), 1)
        self.assertEqual(self.correlater.store["end_ttl"]["hook_metadata"], "hook_metadata-end_ttl")
