import time
import asyncio

import naz
import aioredis


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
        rate_limiter = MyRateLimiter(send_rate=10, max_tokens=25)
        await rate_limiter.limit()
        send_messsages()
    """

    def __init__(self, send_rate=1, max_tokens=2, delay_for_tokens=10):
        self.send_rate = send_rate  # rate in seconds
        self.max_tokens = max_tokens  # start tokens
        self.delay_for_tokens = delay_for_tokens  # how long(seconds) to wait before checking for token availability after they had finished
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


class ExampleBroker(naz.broker.BaseBroker):
    def __init__(self, maxsize: int = 1000) -> None:
        """
        maxsize is the max number of items(not size) that can be put in the queue.
        """
        self.queue: asyncio.queues.Queue = asyncio.Queue(maxsize=maxsize)

    async def enqueue(self, message: naz.protocol.Message) -> None:
        self.queue.put_nowait(message)

    async def dequeue(self) -> naz.protocol.Message:
        return await self.queue.get()


class ExampleRedisBroker(naz.broker.BaseBroker):
    """
    use redis as our queue.

    This implements a basic FIFO queue using redis.
    Basically we use the redis command LPUSH to push messages onto the queue and BRPOP to pull them off.
    https://redis.io/commands/lpush
    https://redis.io/commands/brpop

    You should use a non-blocking redis client eg https://github.com/aio-libs/aioredis
    """

    def __init__(self):
        self.queue_name = "myqueue"
        self.timeout: int = 8
        self._redis = None

    async def _get_redis(self):
        if self._redis:
            return self._redis
        # cache
        self._redis = await aioredis.create_redis_pool(
            address=("localhost", 6379), db=0, minsize=1, maxsize=10, timeout=self.timeout
        )
        return self._redis

    async def enqueue(self, message: naz.protocol.Message):
        _redis = await self._get_redis()
        await _redis.lpush(self.queue_name, message.to_json())

    async def dequeue(self) -> naz.protocol.Message:
        _redis = await self._get_redis()
        while True:
            item = await _redis.brpop(self.queue_name, timeout=self.timeout)
            if item:
                dequed_item = item[1].decode()
                return naz.protocol.json_to_Message(dequed_item)
            else:
                # print("\n\t queue empty. sleeping.\n")
                await asyncio.sleep(5)


if __name__ == "__main__":
    my_broker = ExampleRedisBroker()
    loop = asyncio.get_event_loop()
    for i in range(0, 4):
        print("submit_sm round:", i)
        loop.run_until_complete(
            my_broker.enqueue(
                naz.protocol.SubmitSM(
                    short_message="Hello World-{0}".format(str(i)),
                    log_id="myid1234-{0}".format(str(i)),
                    source_addr="254722111111",
                    destination_addr="254722999999",
                    hook_metadata='{"telco": "verizon", "customer_id": 123456}',
                    user_message_reference=34,
                )
            )
        )
