import abc
import time
from typing import Tuple


class BaseCorrelater(abc.ABC):
    """
    Interface that must be implemented to satisfy naz's Correlater.
    User implementations should inherit this class and
    implement the :func:`get <BaseCorrelater.get>` and :func:`put <BaseCorrelater.put>` methods with the type signatures shown.

    A Correlater is class that naz uses to store relations between SMPP sequence numbers
    and user applications' log_id's and/or hook_metadata.

    Note: This correlation is on a BEST effort basis; it is not guaranteed to be reliable.
    One reason is that the SMPP specifiation mandates sequence numbers to wrap around after ≈ 2billion.
    """

    @abc.abstractmethod
    async def put(self, sequence_number: int, log_id: str, hook_metadata: str) -> None:
        """
        called by naz to put/store the correlation of a given SMPP sequence number to log_id and/or hook_metadata.

        Parameters:
            sequence_number: SMPP sequence_number
            log_id: an ID that a user's application had previously supplied to naz to track/correlate different messages.
            hook_metadata: a string that a user's application had previously supplied to naz that it may want to be correlated with the log_id.
        """
        raise NotImplementedError("put method must be implemented.")

    @abc.abstractmethod
    async def get(self, sequence_number: int) -> Tuple[str, str]:
        """
        called by naz to get the correlation of a given SMPP sequence number to log_id and/or hook_metadata.

        Parameters:
            sequence_number: SMPP sequence_number

        Returns:
            log_id and hook_metadata
        """
        raise NotImplementedError("get method must be implemented.")


class SimpleCorrelater(BaseCorrelater):
    """
    A simple implementation of BaseCorrelater.
    It stores the correlation/relation between a given SMPP sequence_number and a user supplied log_id and/or hook_metadata.

    SimpleCorrelater also features an auto-expiration of dictionary keys(and their values) based on time.

     The storage is done in memory using a python dictionary. The storage looks like:

    .. code-block:: python

       {
            "sequence_number1": {
                "log_id": "log_id1",
                "hook_metadata": "hook_metadata1",
                "stored_at": 681.109023565
            },
           "sequence_number1": {
            "log_id": "log_id2",
            "hook_metadata": "hook_metadata2",
            "stored_at": 682.109023565
           }
           ...
        }
    """

    def __init__(self, max_ttl: float = 60 * 60) -> None:
        """
        Parameters:
            max_ttl: The time in seconds that an item is going to be stored.
                    After the expiration of max_ttl seconds, that item will be deleted.
        """
        self.store: dict = {}
        self.max_ttl: float = max_ttl

    async def put(self, sequence_number: int, log_id: str, hook_metadata: str) -> None:
        stored_at = time.monotonic()
        self.store[sequence_number] = {
            "log_id": log_id,
            "hook_metadata": hook_metadata,
            "stored_at": stored_at,
        }
        # garbage collect
        await self.delete_after_ttl()

    async def get(self, sequence_number: int) -> Tuple[str, str]:
        item = self.store.get(sequence_number)
        if not item:
            # garbage collect
            await self.delete_after_ttl()
            return "", ""

        # garbage collect
        await self.delete_after_ttl()
        return item["log_id"], item["hook_metadata"]

    async def delete_after_ttl(self) -> None:
        """
        iterate over all stored items and delete any that are
        older than self.max_ttl seconds
        """
        now = time.monotonic()
        for key in list(self.store.keys()):
            stored_at = self.store[key]["stored_at"]
            time_diff = now - stored_at
            if time_diff > self.max_ttl:
                del self.store[key]
