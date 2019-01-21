import json
import asyncio
import functools
import concurrent

import naz
import redis


class RedisExampleQueue(naz.q.BaseOutboundQueue):
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


loop = asyncio.get_event_loop()
outboundqueue = RedisExampleQueue()
cli = naz.Client(
    async_loop=loop,
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
)

# queue messages to send
for i in range(0, 5):
    print("submit_sm round:", i)
    item_to_enqueue = {
        "version": "1",
        "smpp_command": naz.SmppCommand.SUBMIT_SM,
        "short_message": "Hello World-{0}".format(str(i)),
        "log_id": "myid12345",
        "source_addr": "254722111111",
        "destination_addr": "254722999999",
    }
    loop.run_until_complete(outboundqueue.enqueue(item_to_enqueue))

# connect to the SMSC host
reader, writer = loop.run_until_complete(cli.connect())
# bind to SMSC as a tranceiver
loop.run_until_complete(cli.tranceiver_bind())

try:
    # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
    tasks = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
    loop.run_forever()
except Exception as e:
    print("\n\t error occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.stop()
