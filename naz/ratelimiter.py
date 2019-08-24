import abc
import time
import typing
import asyncio
import logging

from . import log


class BaseRateLimiter(abc.ABC):
    """
    This is the interface that must be implemented to satisfy naz's rate limiting.
    User implementations should inherit this class and
    implement the :func:`limit <BaseRateLimiter.limit>` methods with the type signatures shown.

    It may be important to control the rate at which the client(naz) sends requests to an SMSC/server.
    naz lets you do this, by allowing you to specify a custom rate limiter.
    """

    @abc.abstractmethod
    async def limit(self) -> None:
        """
        rate limit sending of messages to SMSC.
        """
        raise NotImplementedError("limit method must be implemented.")


class SimpleRateLimiter(BaseRateLimiter):
    """
    This is an implementation of BaseRateLimiter.

    It does rate limiting using a `token bucket rate limiting algorithm <https://en.wikipedia.org/wiki/Token_bucket>`_

    example usage:

    .. highlight:: python
    .. code-block:: python

        rateLimiter = SimpleRateLimiter(send_rate=10)
        await rateLimiter.limit()
        send_messsages()
    """

    def __init__(
        self, send_rate: float = 100_000.00, logger: typing.Union[None, log.BaseLogger] = None
    ) -> None:
        """
        Parameters:
            send_rate: the maximum rate, in messages/second, at which naz can send messages to SMSC.
        """
        if not isinstance(send_rate, float):
            raise ValueError(
                "`send_rate` should be of type:: `float` You entered: {0}".format(type(send_rate))
            )
        if not isinstance(logger, (type(None), log.BaseLogger)):
            raise ValueError(
                "`logger` should be of type:: `None` or `naz.log.BaseLogger` You entered: {0}".format(
                    type(logger)
                )
            )

        self.send_rate: float = send_rate
        self.max_tokens: float = self.send_rate
        self.tokens: float = self.max_tokens
        self.delay_for_tokens: float = 1.0
        self.updated_at: float = time.monotonic()

        self.messages_delivered: int = 0
        self.effective_send_rate: float = 0.00
        if logger is not None:
            self.logger = logger
        else:
            self.logger = log.SimpleLogger("naz.SimpleRateLimiter")

    async def limit(self) -> None:
        self.logger.log(logging.DEBUG, {"event": "naz.SimpleRateLimiter.limit", "stage": "start"})
        while self.tokens < 1:
            self._add_new_tokens()
            # todo: sleep in an exponetial manner upto a maximum then wrap around.
            await asyncio.sleep(self.delay_for_tokens)
            self.logger.log(
                logging.INFO,
                {
                    "event": "naz.SimpleRateLimiter.limit",
                    "stage": "end",
                    "state": "limiting rate",
                    "send_rate": self.send_rate,
                    "delay": self.delay_for_tokens,
                    "effective_send_rate": self.effective_send_rate,
                },
            )

        self.messages_delivered += 1
        self.tokens -= 1

    def _add_new_tokens(self) -> None:
        now = time.monotonic()
        time_since_update = now - self.updated_at
        self.effective_send_rate = self.messages_delivered / time_since_update
        new_tokens = time_since_update * self.send_rate
        if new_tokens > 1:
            self.tokens = min(self.tokens + new_tokens, self.max_tokens)
            self.updated_at = now
            self.messages_delivered = 0
