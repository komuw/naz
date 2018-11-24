mport asyncio, naz, redis

class RedisExampleQueue(naz.q.BaseOutboundQueue):
    def __init__(self):
        self.redis_instance = redis.StrictRedis(host="localhost", port=6379, db=0)
        self.queue_name = "myqueue"
    async def enqueue(self, item):
        self.redis_instance.lpush(self.queue_name, json.dumps(item))
    async def dequeue(self):
        val = self.redis_instance.brpop(self.queue_name)
        dequed_item = json.loads(val[1].decode())
        return dequed_item

myQueue = RedisExampleQueue()

loop = asyncio.get_event_loop()
cli = naz.Client(
    async_loop=loop,
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=myQueue,
)

# in your app
import asyncio

myQueue = RedisExampleQueue()
message_data = {
    "smpp_event": "submit_sm",
    "short_message": "Hello, Thank you for subscribing to our Service.",
    "correlation_id": "myid12345",
    "source_addr": "254722111111",
    "destination_addr": "254722999999",
}
loop = asyncio.get_event_loop()
loop.run_until_complete(myQueue.enqueue(message_data))