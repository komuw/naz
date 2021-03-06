import time
import asyncio
from unittest import TestCase, mock

import naz

from .utils import AsyncMock


class TestRateLimit(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_ratelimit.TestRateLimit.test_something
    """

    def setUp(self):
        self.send_rate = 1.0
        self.rate_limiter = naz.ratelimiter.SimpleRateLimiter(send_rate=self.send_rate)

    def tearDown(self):
        pass

    @staticmethod
    def _run(coro):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def test_no_rlimit(self):
        with mock.patch("naz.ratelimiter.asyncio.sleep", new=AsyncMock()) as mock_sleep:
            for _ in range(0, int(self.send_rate)):
                self._run(self.rate_limiter.limit())
            self.assertFalse(mock_sleep.mock.called)

    def test_token_exhaustion_causes_rlimit(self):
        with mock.patch("naz.ratelimiter.asyncio.sleep", new=AsyncMock()) as mock_sleep:
            for _ in range(0, int(self.send_rate) * 2):
                self._run(self.rate_limiter.limit())
            self.assertTrue(mock_sleep.mock.called)
            self.assertEqual(mock_sleep.mock.call_args[0][0], self.rate_limiter.delay_for_tokens)

    def test_send_rate(self):
        send_rate = 3.0
        rLimiter = naz.ratelimiter.SimpleRateLimiter(send_rate=send_rate)
        msgs_delivered = []
        now = time.monotonic()
        for _ in range(0, int(send_rate) * 4):
            z = self._run(rLimiter.limit())
            msgs_delivered.append(z)

        then = time.monotonic()
        time_taken_to_deliver = then - now  # seconds
        total_msgs_delivered = len(msgs_delivered)
        effective_message_rate = total_msgs_delivered / time_taken_to_deliver
        self.assertAlmostEqual(effective_message_rate, send_rate, 0)
