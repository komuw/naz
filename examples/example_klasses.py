import time
import json
import typing
import asyncio
import functools
import concurrent

import naz
import redis


class MySeqGen(naz.sequence.BaseSequenceGenerator):
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


class MyRateLimiter(naz.ratelimiter.BaseRateLimiter):
    """
    Usage:
        rateLimiter = MyRateLimiter(send_rate=10, max_tokens=25)
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
        self.queue: asyncio.queues.Queue = asyncio.Queue(maxsize=maxsize)

    async def enqueue(self, item: dict) -> None:
        self.queue.put_nowait(item)

    async def dequeue(self) -> typing.Dict[typing.Any, typing.Any]:
        return await self.queue.get()


class ExampleRedisQueue(naz.q.BaseOutboundQueue):
    """
    use redis as our queue.

    This implements a basic FIFO queue using redis.
    Basically we use the redis command LPUSH to push messages onto the queue and BRPOP to pull them off.
    https://redis.io/commands/lpush
    https://redis.io/commands/brpop

    Note that in practice, you would probaly want to use a non-blocking redis
    client eg https://github.com/aio-libs/aioredis
    This example uses concurrent.futures.ThreadPoolExecutor to workaround
    the fact that we are using a blocking/sync redis client.

    Use an async client in real life/code.
    """

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.redis_instance = redis.StrictRedis(host="localhost", port=6379, db=0)
        self.queue_name = "myqueue"

    async def enqueue(self, item):
        with concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix="naz-redis-thread-pool"
        ) as executor:
            await self.loop.run_in_executor(
                executor, functools.partial(self.blocking_enqueue, item=item)
            )

    def blocking_enqueue(self, item):
        self.redis_instance.lpush(self.queue_name, json.dumps(item))

    async def dequeue(self):
        with concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix="naz-redis-thread-pool"
        ) as executor:
            while True:
                item = await self.loop.run_in_executor(
                    executor, functools.partial(self.blocking_dequeue)
                )
                if item:
                    return item
                else:
                    await asyncio.sleep(5)

    def blocking_dequeue(self):
        x = self.redis_instance.brpop(self.queue_name, timeout=3)
        if not x:
            return None
        dequed_item = json.loads(x[1].decode())
        return dequed_item


ExampleSeqGen = MySeqGen()
ExampleRateLimiter = naz.ratelimiter.SimpleRateLimiter(send_rate=2.0)  # MyRateLimiter()
ExampleRedisQueueInstance = ExampleRedisQueue()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for i in range(0, 4_000_000):
        print("submit_sm round:", i)
        item_to_enqueue = {
            "version": "1",
            "smpp_command": naz.SmppCommand.SUBMIT_SM,
            "short_message": "Hello World-{0}".format(str(i)),
            "log_id": "myid1234-{0}".format(str(i)),
            "source_addr": "254722111111",
            "destination_addr": "254722999999",
            "hook_metadata": '{"telco": "verizon", "customer_id": 123456}',
        }
        loop.run_until_complete(ExampleRedisQueueInstance.enqueue(item_to_enqueue))
