import asyncio

import typing


class BaseOutboundQueue:
    """
    Interface that must be implemented to satisfy naz's outbound queue.
    User implementations should inherit this class and
    implement the enqueue and dequeue methods with the type signatures shown.
    """

    async def enqueue(self, item: dict) -> None:
        raise NotImplementedError("enqueue method must be implemented.")

    async def dequeue(self) -> typing.Dict[typing.Any, typing.Any]:
        raise NotImplementedError("dequeue method must be implemented.")


class SimpleOutboundQueue(BaseOutboundQueue):
    """
    this allows users to provide their own queue managers eg redis etc.
    """

    def __init__(self, maxsize: int, loop: asyncio.events.AbstractEventLoop) -> None:
        """
        maxsize is the max number of items(not size) that can be put in the queue.
        """
        self.queue: asyncio.queues.Queue = asyncio.Queue(maxsize=maxsize, loop=loop)

    async def enqueue(self, item: dict) -> None:
        self.queue.put_nowait(item)

    async def dequeue(self) -> typing.Dict[typing.Any, typing.Any]:
        return await self.queue.get()
