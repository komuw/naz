import time
import asyncio


class RateLimiter:
    """
    simple implementation of a token bucket rate limiting algo.
    https://en.wikipedia.org/wiki/Token_bucket
    todo: check that the algo actually works.

    Usage:
        rateLimiter = RateLimiter(SEND_RATE=10, MAX_TOKENS=25)
        await rateLimiter.wait_for_token()
        send_messsages()
    """

    def __init__(self, logger, SEND_RATE=10, MAX_TOKENS=25, DELAY_FOR_TOKENS=1):
        self.SEND_RATE = SEND_RATE  # rate in seconds
        self.MAX_TOKENS = MAX_TOKENS  # start tokens
        self.DELAY_FOR_TOKENS = (
            DELAY_FOR_TOKENS
        )  # how long(seconds) to wait before checking for token availability after they had finished
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()

        self.logger = logger

    async def wait_for_token(self):
        while self.tokens < 1:
            self.logger.info(
                "rate_limiting. SEND_RATE={0}. DELAY_FOR_TOKENS={1}".format(
                    self.SEND_RATE, self.DELAY_FOR_TOKENS
                )
            )
            self.add_new_tokens()
            # todo: sleep in an exponetial manner upto a maximum then wrap around.
            await asyncio.sleep(self.DELAY_FOR_TOKENS)
        self.tokens -= 1

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.SEND_RATE
        if new_tokens > 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now
