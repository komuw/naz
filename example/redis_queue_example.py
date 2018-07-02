import json
import asyncio

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
    """

    def __init__(self):
        self.redis_instance = redis.StrictRedis(host="localhost", port=6379, db=0)
        self.queue_name = "myqueue"

    async def enqueue(self, item):
        self.redis_instance.lpush(self.queue_name, json.dumps(item))

    async def dequeue(self):
        x = self.redis_instance.brpop(self.queue_name)
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
        "event": "submit_sm",
        "short_message": "Hello World-{0}".format(str(i)),
        "correlation_id": "myid12345",
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
    gathering = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(gathering)
    loop.run_forever()
except Exception as e:
    import traceback

    traceback.print_exc()
finally:
    loop.run_until_complete(cli.unbind())
    loop.close()
