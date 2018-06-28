import asyncio


class DefaultOutboundQueue(object):
    """
    this allows users to provide their own queue managers eg redis etc.
    """

    def __init__(self, maxsize, loop):
        """
        maxsize is the max number of items(not size) that can be put in the queue.
        """
        self.queue = asyncio.Queue(maxsize=maxsize, loop=loop)

    async def enqueue(self, item):
        self.queue.put_nowait(item)

    async def dequeue(self):
        return await self.queue.get()
