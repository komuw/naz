import sys
import time
import asyncio
import logging
from unittest import TestCase

import naz
import mock

logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.DEBUG)


def AsyncMock(*args, **kwargs):
    """
    see: https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
    """
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


class TestRateLimit(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_ratelimit.TestRateLimit.test_something
    """

    def setUp(self):

        self.logger = logging.getLogger("naz.test")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel("DEBUG")

        self.send_rate = 1
        self.max_tokens = 1
        self.delay_for_tokens = 1
        self.rateLimiter = naz.ratelimiter.SimpleRateLimiter(
            logger=self.logger,
            send_rate=self.send_rate,
            max_tokens=self.max_tokens,
            delay_for_tokens=self.delay_for_tokens,
        )

    def tearDown(self):
        pass

    @staticmethod
    def _run(coro):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def test_no_rlimit(self):
        with mock.patch("naz.ratelimiter.asyncio.sleep", new=AsyncMock()) as mock_sleep:
            for _ in range(0, self.max_tokens):
                self._run(self.rateLimiter.limit())
            self.assertFalse(mock_sleep.mock.called)

    def test_token_exhaustion_causes_rlimit(self):
        with mock.patch("naz.ratelimiter.asyncio.sleep", new=AsyncMock()) as mock_sleep:
            for _ in range(0, self.max_tokens * 2):
                self._run(self.rateLimiter.limit())
            self.assertTrue(mock_sleep.mock.called)
            self.assertEqual(mock_sleep.mock.call_args[0][0], self.delay_for_tokens)

    def test_send_rate(self):
        send_rate = 3
        rLimiter = naz.ratelimiter.SimpleRateLimiter(
            logger=self.logger, send_rate=send_rate, max_tokens=3, delay_for_tokens=1
        )
        msgs_delivered = []
        now = time.monotonic()
        for _ in range(0, send_rate * 4):
            z = self._run(rLimiter.limit())
            msgs_delivered.append(z)

        then = time.monotonic()
        time_taken_to_deliver = then - now  # seconds
        total_msgs_delivered = len(msgs_delivered)
        effective_message_rate = total_msgs_delivered / time_taken_to_deliver
        self.assertAlmostEqual(effective_message_rate, send_rate, 0)
