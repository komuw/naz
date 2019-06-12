import os
import json
import asyncio

import naz
import aioredis


class MyRedisQueue(naz.q.BaseOutboundQueue):
    """
    use redis as our queue.

    DO NOT USE THIS IN PRODUCTION. It is untested.

    This implements a basic FIFO queue using redis.
    Basically we use the redis command LPUSH to push messages onto the queue and BRPOP to pull them off.
    https://redis.io/commands/lpush
    https://redis.io/commands/brpop

    You should use a non-blocking redis client eg https://github.com/aio-libs/aioredis
    """

    def __init__(self):
        host = "localhost"
        port = 6379
        password = None
        if os.environ.get("IN_DOCKER"):
            host = os.environ["REDIS_HOST"]
            port = os.environ["REDIS_PORT"]
            password = os.environ["REDIS_PASSWORD"]

        self.host = host
        self.password = password
        self.port = int(port)
        self.timeout: int = 8
        self.queue_name = "naz_benchmarks_queue"
        self._redis = None

    async def _get_redis(self):
        if self._redis:
            return self._redis
        # cache
        self._redis = await aioredis.create_redis_pool(
            address=(self.host, self.port),
            db=0,
            password=self.password,
            minsize=1,
            maxsize=10,
            timeout=self.timeout,
        )
        return self._redis

    async def enqueue(self, item):
        _redis = await self._get_redis()
        await _redis.lpush(self.queue_name, json.dumps(item))

    async def dequeue(self):
        _redis = await self._get_redis()
        while True:
            item = await _redis.brpop(self.queue_name, timeout=self.timeout)
            if item:
                dequed_item = json.loads(item[1].decode())
                return dequed_item
            else:
                await asyncio.sleep(5)
