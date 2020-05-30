# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import asyncio
from unittest import TestCase

import naz


class TestThrottle(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_throttle.TestThrottle.test_something
    """

    def setUp(self):
        self.throttle_handler = naz.throttle.SimpleThrottleHandler(
            sampling_period=0.50, sample_size=12.00, deny_request_at=1.00
        )

    def tearDown(self):
        pass

    @staticmethod
    def _run(coro):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def test_small_sample_size_allows_requests(self):
        for _ in range(0, (int(self.throttle_handler.sample_size) - 2)):
            self._run(self.throttle_handler.throttled())
        allow_request = self._run(self.throttle_handler.allow_request())
        self.assertTrue(allow_request)

    def test_enough_sample_size_denies_requests(self):
        for _ in range(0, (int(self.throttle_handler.sample_size) * 2)):
            self._run(self.throttle_handler.throttled())
        allow_request = self._run(self.throttle_handler.allow_request())
        self.assertFalse(allow_request)

    def test_enough_sample_size_and_successes_allows_requests(self):
        for _ in range(0, int(self.throttle_handler.sample_size)):
            self._run(self.throttle_handler.throttled())
        for _ in range(0, (int(self.throttle_handler.sample_size) * 100)):
            self._run(self.throttle_handler.not_throttled())
        allow_request = self._run(self.throttle_handler.allow_request())
        self.assertTrue(allow_request)

    def test_reset(self):
        throttles = 13
        NON_throttles = 25
        for _ in range(0, throttles):
            self._run(self.throttle_handler.throttled())
        for _ in range(0, NON_throttles):
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
