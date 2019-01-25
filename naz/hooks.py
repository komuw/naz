import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import naz


class BaseHook:
    """
    Interface that must be implemented to satisfy naz's hooks.
    User implementations should inherit this class and
    implement the request and response methods with the type signatures shown.

    A hook is class with hook methods that are called before a request is sent to SMSC and
    after a response is received from SMSC.
    """

    async def request(self, smpp_command: str, log_id: str, hook_metadata: str) -> None:
        """
        called before a request is sent to SMSC.

        :param smpp_command:                  (mandatory) [str]
            any one of the SMSC command;
                bind_transceiver, bind_transceiver_resp,
                unbind, unbind_resp,
                submit_sm, submit_sm_resp,
                deliver_sm, deliver_sm_resp,
                enquire_link, enquire_link_resp, generic_nack
        :param log_id:                  (mandatory) [str]
            an ID that a user's application had previously supplied to naz
            to track/correlate different messages.
        :param hook_metadata:                  (optional) [str]
            a string that a user's application had previously supplied to naz
            that it may want to be correlated with the log_id.
        """
        raise NotImplementedError("request method must be implemented.")

    async def response(
        self,
        smpp_command: str,
        log_id: str,
        hook_metadata: str,
        response_status: "naz.client.CommandStatus",
    ) -> None:
        """
        called after a response is received from SMSC.

        :param smpp_command:                  (mandatory) [str]
            any one of the SMSC command;
                bind_transceiver, bind_transceiver_resp,
                unbind, unbind_resp,
                submit_sm, submit_sm_resp,
                deliver_sm, deliver_sm_resp,
                enquire_link, enquire_link_resp, generic_nack
        :param log_id:                  (mandatory) [str]
            an ID that a user's application had previously supplied to naz
            to track/correlate different messages.
        :param hook_metadata:                  (optional) [str]
            a string that a user's application had previously supplied to naz
            that it may want to be correlated with the log_id.
        :param response_status:                  (optional) [naz.client.CommandStatus]
            the response from SMSC.
        """
        raise NotImplementedError("response method must be implemented.")


class SimpleHook(BaseHook):
    """
    class implementing naz's Hook interface.
    """

    def __init__(self, logger) -> None:
        self.logger: logging.Logger = logger

    async def request(self, smpp_command: str, log_id: str, hook_metadata: str) -> None:
        """
        hook method that is called just before a request is sent to SMSC.
        """
        self.logger.info(
            {
                "event": "naz.SimpleHook.request",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "hook_metadata": hook_metadata,
            }
        )

    async def response(
        self,
        smpp_command: str,
        log_id: str,
        hook_metadata: str,
        response_status: "naz.client.CommandStatus",
    ) -> None:
        """
        hook method that is called just after a response is gotten from SMSC.
        """
        import pdb

        pdb.set_trace()
        # type(response_status) ==  naz.client.CommandStatus or
        # type(response_status) ==  naz.CommandStatus
        self.logger.info(
            {
                "event": "naz.SimpleHook.response",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "hook_metadata": hook_metadata,
                "response_status": response_status,
            }
        )
