import abc
import asyncio

from . import protocol


class BaseBroker(abc.ABC):
    """
    This is the interface that must be implemented to satisfy naz's broker.
    User implementations should inherit this class and
    implement the :func:`enqueue <BaseBroker.enqueue>` and :func:`dequeue <BaseBroker.dequeue>` methods with the type signatures shown.

    naz calls an implementation of this class to enqueue and/or dequeue an item.
    """

    @abc.abstractmethod
    async def enqueue(self, message: protocol.Message) -> None:
        """
        enqueue/save an item.

        Parameters:
            item: The item to be enqueued/saved
                  The item/message is a `naz.protocol.Message` class instance;
                  It is up to the broker implementation to do the serialization(if neccesary) in order to be able to store it.
                  `naz.protocol.Message` has a `to_json()` method that you can use to serialize a `naz.protocol.Message` class instance into json.
        """
        raise NotImplementedError("enqueue method must be implemented.")

    @abc.abstractmethod
    async def dequeue(self) -> protocol.Message:
        """
        dequeue an item.

        Returns:
            item that was dequeued.
            The item has to be returned as a `naz.protocol.Message` class instance.
            It is up to the broker implementation to do the de-serialization(if neccesary).
            `naz.protocol.Message` has a `from_json()` method that you can use to de-serialize a json string into `naz.protocol.Message` class instance.
        """
        raise NotImplementedError("dequeue method must be implemented.")


class SimpleBroker(BaseBroker):
    """
    This is an in-memory implementation of BaseBroker.

    Note: It should only be used for tests and demo purposes.
    """

    def __init__(self, maxsize: int = 2500) -> None:
        """
        Parameters:
            maxsize: the maximum number of items(not size) that can be put in the queue.
        """
        if not isinstance(maxsize, int):
            raise ValueError(
                "`maxsize` should be of type:: `int` You entered: {0}".format(type(maxsize))
            )
        self.queue: asyncio.queues.Queue = asyncio.Queue(maxsize=maxsize)

    async def enqueue(self, message: protocol.Message) -> None:
        self.queue.put_nowait(message)

    async def dequeue(self) -> protocol.Message:
        return await self.queue.get()
