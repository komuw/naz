
import time
import asyncio
import typing

import naz


class ExampleSeqGen(object):
    """
    """

    MAX_SEQUENCE_NUMBER = 0x7FFFFFFF

    def __init__(self):
        self.sequence_number = 1

    def next_sequence(self):
        if self.sequence_number == self.MAX_SEQUENCE_NUMBER:
            # wrap around
            self.sequence_number = 1
        else:
            self.sequence_number += 1
        return self.sequence_number


class ExampleRateLimiter:
    """
    Usage:
        rateLimiter = RateLimiter(SEND_RATE=10, MAX_TOKENS=25)
        await rateLimiter.wait_for_token()
        send_messsages()
    """

    def __init__(self, SEND_RATE=1, MAX_TOKENS=2, DELAY_FOR_TOKENS=10):
        self.SEND_RATE = SEND_RATE  # rate in seconds
        self.MAX_TOKENS = MAX_TOKENS  # start tokens
        self.DELAY_FOR_TOKENS = (
            DELAY_FOR_TOKENS
        )  # how long(seconds) to wait before checking for token availability after they had finished
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()

    async def wait_for_token(self):
        while self.tokens < 1:
            print(
                "EXAMPLE_rate_limiting. SEND_RATE={0}. DELAY_FOR_TOKENS={1}".format(
                    self.SEND_RATE, self.DELAY_FOR_TOKENS
                )
            )
            self.add_new_tokens()
            await asyncio.sleep(self.DELAY_FOR_TOKENS)
        self.tokens -= 1

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.SEND_RATE
        if new_tokens > 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now


class ExampleQueue(naz.q.BaseOutboundQueue):
    def __init__(self, maxsize: int = 1000) -> None:
        """
        maxsize is the max number of items(not size) that can be put in the queue.
        """
        loop: asyncio.events.AbstractEventLoop = asyncio.get_event_loop()
        self.queue: asyncio.queues.Queue = asyncio.Queue(maxsize=maxsize, loop=loop)

    async def enqueue(self, item: dict) -> None:
        self.queue.put_nowait(item)

    async def dequeue(self) -> typing.Dict[typing.Any, typing.Any]:
        return await self.queue.get()


ExampleQueueInstance = ExampleQueue(maxsize=433)
