import time
import asyncio
import logging


class BaseRateLimiter:
    """
    Interface that must be implemented to satisfy naz's rate limiter.
    User implementations should inherit this class and
    implement the limit method with the type signatures shown.
    """

    async def limit(self) -> None:
        raise NotImplementedError("limit method must be implemented.")


class SimpleRateLimiter(BaseRateLimiter):
    """
    simple implementation of a token bucket rate limiting algo.
    https://en.wikipedia.org/wiki/Token_bucket
    todo: check that the algo actually works.

    Usage:
        rateLimiter = SimpleRateLimiter(logger=myLogger, send_rate=10, max_tokens=25)
        await rateLimiter.limit()
        send_messsages()
    """

    def __init__(
        self,
        logger: logging.Logger,
        send_rate: float = 1000,
        max_tokens: float = 1000,
        delay_for_tokens: float = 1,
    ) -> None:
        """
        :param send_rate:                  (optional) [float]
            the maximum rate, in messages/second, at which naz can send messages to SMSC.
        :param max_tokens:                  (optional) [int]
            the total number of mesages naz can send before rate limiting kicks in.
        :param delay_for_tokens:                  (optional) [float]
            the duration in seconds which to wait for before checking for token availability after they had finished.

        send_rate and max_tokens should generally be of equal value.
        """
        self.send_rate: float = send_rate
        self.max_tokens: float = max_tokens
        self.delay_for_tokens: float = (delay_for_tokens)
        self.tokens: float = self.max_tokens
        self.updated_at: float = time.monotonic()

        self.logger = logger
        self.messages_delivered: int = 0
        self.effective_send_rate: float = 0

    async def limit(self) -> None:
        self.logger.info("{}".format({"event": "SimpleRateLimiter.limit", "stage": "start"}))
        while self.tokens < 1:
            self.add_new_tokens()
            # todo: sleep in an exponetial manner upto a maximum then wrap around.
            await asyncio.sleep(self.delay_for_tokens)
            self.logger.info(
                "{}".format(
                    {
                        "event": "SimpleRateLimiter.limit",
                        "stage": "end",
                        "state": "limiting rate",
                        "send_rate": self.send_rate,
                        "delay": self.delay_for_tokens,
                        "effective_send_rate": self.effective_send_rate,
                    }
                )
            )

        self.messages_delivered += 1
        self.tokens -= 1

    def add_new_tokens(self) -> None:
        now = time.monotonic()
        time_since_update = now - self.updated_at
        self.effective_send_rate = self.messages_delivered / time_since_update
        new_tokens = time_since_update * self.send_rate
        if new_tokens > 1:
            self.tokens = min(self.tokens + new_tokens, self.max_tokens)
            self.updated_at = now
            self.messages_delivered = 0
