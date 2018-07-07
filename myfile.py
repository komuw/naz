import asyncio
import naz


class ExampleQueue(naz.q.BaseOutboundQueue):
    def __init__(self):
        loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue(maxsize=1000, loop=loop)

    async def enqueue(self, item):
        self.queue.put_nowait(item)

    async def dequeue(self):
        return await self.queue.get()
