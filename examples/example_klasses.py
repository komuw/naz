
import json
import asyncio


import naz
import redis


class MyRateLimiter(naz.ratelimiter.BaseRateLimiter):
    def __init__(self):
        self.count = 0

    async def limit(self):
        self.count += 1
        if self.count % 2 == 0:
            print("\n\t rateLimiter even. sleep={}".format(6))
            await asyncio.sleep(6)
        else:
            print("\n\t rateLimiter odd. sleep={}".format(9))
            await asyncio.sleep(9)


class ExampleQueue(naz.q.BaseOutboundQueue):
    def __init__(self):
        self.redis_instance = redis.StrictRedis(host="localhost", port=6379, db=0)
        self.queue_name = "myqueue"

    async def enqueue(self, item):
        self.redis_instance.lpush(self.queue_name, json.dumps(item))

    async def dequeue(self):
        x = self.redis_instance.brpop(self.queue_name)
        dequed_item = json.loads(x[1].decode())
        return dequed_item


ExampleQueueInstance = ExampleQueue()


def myApp(loop):
    for i in range(0, 12):
        print("enque item {}".format(i))
        item_to_enqueue = {
            "smpp_event": "submit_sm",
            "short_message": "Hello World-{0}".format(str(i)),
            "correlation_id": "myid12345",
            "source_addr": "254722111111",
            "destination_addr": "254722999999",
        }
        loop.run_until_complete(ExampleQueueInstance.enqueue(item_to_enqueue))


# In your Application...
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    myApp(loop)
