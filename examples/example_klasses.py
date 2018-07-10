
import time
import asyncio
import typing

import naz


class ExampleSeqGen(object):
    """
    """

    max_sequence_number = 0x7FFFFFFF

    def __init__(self):
        self.sequence_number = 1

    def next_sequence(self):
        if self.sequence_number == self.max_sequence_number:
            # wrap around
            self.sequence_number = 1
        else:
            self.sequence_number += 1
        return self.sequence_number


class ExampleRateLimiter(naz.ratelimiter.BaseRateLimiter):
    """
    Usage:
        rateLimiter = ExampleRateLimiter(send_rate=10, max_tokens=25)
        await rateLimiter.limit()
        send_messsages()
    """

    def __init__(self, send_rate=1, max_tokens=2, delay_for_tokens=10):
        self.send_rate = send_rate  # rate in seconds
        self.max_tokens = max_tokens  # start tokens
        self.delay_for_tokens = (
            delay_for_tokens
        )  # how long(seconds) to wait before checking for token availability after they had finished
        self.tokens = self.max_tokens
        self.updated_at = time.monotonic()

    async def limit(self):
        while self.tokens < 1:
            print(
                "EXAMPLE_rate_limiting. send_rate={0}. delay_for_tokens={1}".format(
                    self.send_rate, self.delay_for_tokens
                )
            )
            self.add_new_tokens()
            await asyncio.sleep(self.delay_for_tokens)
        self.tokens -= 1

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.send_rate
        if new_tokens > 1:
            self.tokens = min(self.tokens + new_tokens, self.max_tokens)
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
