import os
import json
import asyncio
import logging
import functools
import concurrent

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

    Note that in practice, you would probaly want to use a non-blocking redis
    client eg https://github.com/aio-libs/aioredis
    This example uses concurrent.futures.ThreadPoolExecutor to workaround
    the fact that we are using a blocking/sync redis client.

    Use an async client in real life/code.
    """

    def __init__(self):
        host = "localhost"
        port = 6379
        password = None
        if os.environ.get("IN_DOCKER"):
            host = os.environ["REDIS_HOST"]
            port = os.environ["REDIS_PORT"]
            password = os.environ["REDIS_PASSWORD"]
        port = int(port)
        self.redis_instance = redis.StrictRedis(
            host=host,
            port=port,
            password=password,
            db=0,
            socket_connect_timeout=8,
            socket_timeout=8,
        )
        self.loop = asyncio.get_event_loop()
        self.queue_name = "naz_benchmarks_queue"
        self.thread_name_prefix = "naz_benchmarks_redis_thread_pool"
        self.logger = naz.logger.SimpleLogger("naz_benchmarks.MyRedisQueue")

    async def enqueue(self, item):
        self.logger.log(logging.INFO, {"event": "MyRedisQueue.enqueue", "stage": "start"})
        with concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix=self.thread_name_prefix
        ) as executor:
            await self.loop.run_in_executor(
                executor, functools.partial(self.blocking_enqueue, item=item)
            )
        self.logger.log(logging.INFO, {"event": "MyRedisQueue.enqueue", "stage": "end"})

    def blocking_enqueue(self, item):
        self.redis_instance.lpush(self.queue_name, json.dumps(item))

    async def dequeue(self):
        self.logger.log(logging.INFO, {"event": "MyRedisQueue.dequeue", "stage": "start"})
        with concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix=self.thread_name_prefix
        ) as executor:
            while True:
                item = await self.loop.run_in_executor(
                    executor, functools.partial(self.blocking_dequeue)
                )
                if item:
                    return item
                else:
                    self.logger.log(
                        logging.INFO,
                        {"event": "MyRedisQueue.dequeue", "stage": "end", "state": "sleeping"},
                    )
                    await asyncio.sleep(5)
        self.logger.log(logging.INFO, {"event": "MyRedisQueue.dequeue", "stage": "end"})

    def blocking_dequeue(self):
        x = self.redis_instance.brpop(self.queue_name, timeout=3)
        if not x:
            return None
        dequed_item = json.loads(x[1].decode())
        return dequed_item
