import os
import json
import asyncio

import naz
import aioredis


class RedisExampleQueue(naz.q.BaseOutboundQueue):
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
                # print("\n\t queue empty. sleeping.\n")
                await asyncio.sleep(5)


loop = asyncio.get_event_loop()
outboundqueue = RedisExampleQueue()
cli = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password=os.getenv("password", "password"),
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
    tasks = asyncio.gather(cli.dequeue_messages(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
    loop.run_forever()
except Exception as e:
    print("\n\t error occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.stop()
