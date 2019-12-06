import os
import asyncio

import naz
import aioredis


class RedisExampleBroker(naz.broker.BaseBroker):
    """
    use redis as our broker.

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

    async def enqueue(self, message: naz.protocol.Message) -> None:
        _redis = await self._get_redis()
        await _redis.lpush(self.queue_name, message.to_json())

    async def dequeue(self) -> naz.protocol.Message:
        _redis = await self._get_redis()
        while True:
            item = await _redis.brpop(self.queue_name, timeout=self.timeout)
            if item:
                dequed_item = item[1].decode()
                return naz.protocol.Message.from_json(dequed_item)
            else:
                # print("\n\t queue empty. sleeping.\n")
                await asyncio.sleep(5)


loop = asyncio.get_event_loop()
broker = RedisExampleBroker()
cli = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password=os.getenv("password", "password"),
    broker=broker,
)

# queue messages to send
for i in range(0, 5):
    print("submit_sm round:", i)
    loop.run_until_complete(
        broker.enqueue(
            naz.protocol.SubmitSM(
                short_message="Hello World-{0}".format(str(i)),
                log_id="myid1234-{0}".format(str(i)),
                source_addr="254722111111",
                destination_addr="254722999999",
            )
        )
    )


try:
    # 1. connect to the SMSC host
    # 2. bind to the SMSC host
    # 3. send any queued messages to SMSC
    # 4. read any data from SMSC
    # 5. continually check the state of the SMSC
    tasks = asyncio.gather(
        cli.connect(),
        cli.tranceiver_bind(),
        cli.dequeue_messages(),
        cli.receive_data(),
        cli.enquire_link(),
    )
    loop.run_until_complete(tasks)
except Exception as e:
    print("\n\t error occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.stop()
