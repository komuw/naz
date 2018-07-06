import sys
import mock
import asyncio
import logging
from unittest import TestCase

import naz


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
        self.loop = asyncio.get_event_loop()

        self.logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel("DEBUG")

        self.SEND_RATE = 1
        self.MAX_TOKENS = 1
        self.DELAY_FOR_TOKENS = 1
        self.rateLimiter = naz.ratelimiter.SimpleRateLimiter(
            logger=self.logger,
            SEND_RATE=self.SEND_RATE,
            MAX_TOKENS=self.MAX_TOKENS,
            DELAY_FOR_TOKENS=self.DELAY_FOR_TOKENS,
        )

    def tearDown(self):
        pass

    def _run(self, coro):
        return self.loop.run_until_complete(coro)

    def test_no_rlimit(self):
        with mock.patch("naz.ratelimiter.asyncio.sleep", new=AsyncMock()) as mock_sleep:
            for i in range(0, self.MAX_TOKENS):
                self._run(self.rateLimiter.wait_for_token())
            self.assertFalse(mock_sleep.mock.called)

    def test_token_exhaustion_causes_rlimit(self):
        with mock.patch("naz.ratelimiter.asyncio.sleep", new=AsyncMock()) as mock_sleep:
            for i in range(0, self.MAX_TOKENS * 2):
                self._run(self.rateLimiter.wait_for_token())
            self.assertTrue(mock_sleep.mock.called)
            self.assertEqual(mock_sleep.mock.call_args[0][0], self.DELAY_FOR_TOKENS)
