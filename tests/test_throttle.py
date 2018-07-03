# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import sys
import asyncio
import logging
from unittest import TestCase

import naz


logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.DEBUG)


class TestThrottle(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_throttle.TestThrottle.test_something
    """

    def setUp(self):
        self.loop = asyncio.get_event_loop()

        self.logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel("DEBUG")

        self.throttle_handler = naz.throttle.SimpleThrottleHandler(
            logger=self.logger, sampling_period=10, sample_size=12, deny_request_at=1
        )

    def tearDown(self):
        pass

    def _run(self, coro):
        return self.loop.run_until_complete(coro)

    def test_small_sample_size_allows_requests(self):
        for i in range(0, (self.throttle_handler.sample_size - 2)):
            self._run(self.throttle_handler.throttled())
        allow_request = self._run(self.throttle_handler.allow_request())
        self.assertTrue(allow_request)

    def test_enough_sample_size_denies_requests(self):
        for i in range(0, (self.throttle_handler.sample_size * 2)):
            self._run(self.throttle_handler.throttled())
        allow_request = self._run(self.throttle_handler.allow_request())
        self.assertFalse(allow_request)

    def test_enough_sample_size_and_successes_allows_requests(self):
        for i in range(0, self.throttle_handler.sample_size):
            self._run(self.throttle_handler.throttled())
        for i in range(0, (self.throttle_handler.sample_size * 100)):
            self._run(self.throttle_handler.not_throttled())
        allow_request = self._run(self.throttle_handler.allow_request())
        self.assertTrue(allow_request)

    def test_reset(self):
        throttles = 13
        NON_throttles = 25
        for i in range(0, throttles):
            self._run(self.throttle_handler.throttled())
        for i in range(0, NON_throttles):
            self._run(self.throttle_handler.not_throttled())
        self._run(self.throttle_handler.allow_request())

        self.assertEqual(self.throttle_handler.throttle_responses, throttles)
        self.assertEqual(self.throttle_handler.NON_throttle_responses, NON_throttles)

        print("\n\n")
        print(" # todo: remove the sleep from here. maybe mock time?")
        print("\n")
        # todo: remove the sleep from here. maybe mock time?
        # wait for a period longer than sampling_period
        self._run(asyncio.sleep(self.throttle_handler.sampling_period * 1.5))
        self._run(self.throttle_handler.allow_request())
        self.assertEqual(self.throttle_handler.throttle_responses, 0)
        self.assertEqual(self.throttle_handler.NON_throttle_responses, 0)
