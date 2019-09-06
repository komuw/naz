import abc
import logging
import typing

from . import log

if typing.TYPE_CHECKING:
    from . import state  # noqa: F401


class BaseHook(abc.ABC):
    """
    Interface that must be implemented to satisfy naz's hooks.
    User implementations should inherit this class and
    implement the :func:`to_smsc <BaseHook.to_smsc>` and :func:`from_smsc <BaseHook.from_smsc>` methods with the type signatures shown.

    A hook is class with methods that are called just before sending data to SMSC and just after receiving data from SMSC.
    """

    @abc.abstractmethod
    async def to_smsc(self, smpp_command: str, log_id: str, hook_metadata: str, pdu: bytes) -> None:
        """
        called before sending data to SMSC.

        Parameters:
            smpp_command: any one of the SMSC commands eg submit_sm
            log_id: an ID that a user's application had previously supplied to naz to track/correlate different messages.
            hook_metadata: a string that a user's application had previously supplied to naz that it may want to be correlated with the log_id.
            pdu: the full PDU as sent to SMSC
        """
        raise NotImplementedError("to_smsc method must be implemented.")

    @abc.abstractmethod
    async def from_smsc(
        self,
        smpp_command: str,
        log_id: str,
        hook_metadata: str,
        status: "state.CommandStatus",
        pdu: bytes,
    ) -> None:
        """
        called after receiving data from SMSC.

        Parameters:
            smpp_command: any one of the SMSC commands eg submit_sm_resp
            log_id: an ID that a user's application had previously supplied to naz to track/correlate different messages.
            hook_metadata: a string that a user's application had previously supplied to naz that it may want to be correlated with the log_id.
            status: the state of request/response from SMSC.
            pdu: the full PDU as received from SMSC
        """
        raise NotImplementedError("from_smsc method must be implemented.")


class SimpleHook(BaseHook):
    """
    This is an implementation of BaseHook.
    When this class is called by naz, it just logs the request or response.
    """

    def __init__(self, logger: typing.Union[None, log.BaseLogger] = None) -> None:
        if not isinstance(logger, (type(None), log.BaseLogger)):
            raise ValueError(
                "`logger` should be of type:: `None` or `naz.log.BaseLogger` You entered: {0}".format(
                    type(logger)
                )
            )

        if logger is not None:
            self.logger = logger
        else:
            self.logger = log.SimpleLogger("naz.SimpleHook")

    async def to_smsc(self, smpp_command: str, log_id: str, hook_metadata: str, pdu: bytes) -> None:
        self.logger.log(
            logging.NOTSET,
            {
                "event": "naz.SimpleHook.to_smsc",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "hook_metadata": hook_metadata,
                "pdu": pdu,
            },
        )

    async def from_smsc(
        self,
        smpp_command: str,
        log_id: str,
        hook_metadata: str,
        status: "state.CommandStatus",
        pdu: bytes,
    ) -> None:
        self.logger.log(
            logging.NOTSET,
            {
                "event": "naz.SimpleHook.from_smsc",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "hook_metadata": hook_metadata,
                "status": status.description,
                "pdu": pdu,
            },
        )
