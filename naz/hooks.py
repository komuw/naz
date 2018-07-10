import typing
import logging


class BaseHook:
    """
    Interface that must be implemented to satisfy naz's hooks.
    User implementations should inherit this class and
    implement the request and response methods with the type signatures shown.

    A hook is class with hook methods that are called before a request is sent to SMSC and
    after a response is received from SMSC.
    """

    async def request(self, smpp_event: str, correlation_id: typing.Optional[str] = None) -> None:
        """
        called before a request is sent to SMSC.

        :param smpp_event:                  (mandatory) [str]
            any one of the SMSC event/command_id;
                bind_transceiver, bind_transceiver_resp,
                unbind, unbind_resp,
                submit_sm, submit_sm_resp,
                deliver_sm, deliver_sm_resp,
                enquire_link, enquire_link_resp, generic_nack
        :param correlation_id:                  (mandatory) [str]
            an ID that a user's application had previously supplied to user
            to track/correlate different messages.
        """
        raise NotImplementedError("request method must be implemented.")

    async def response(self, smpp_event: str, correlation_id: typing.Optional[str] = None) -> None:
        """
        called after a response is received from SMSC.

        :param smpp_event:                  (mandatory) [str]
            any one of the SMSC event/command_id;
                bind_transceiver, bind_transceiver_resp,
                unbind, unbind_resp,
                submit_sm, submit_sm_resp,
                deliver_sm, deliver_sm_resp,
                enquire_link, enquire_link_resp, generic_nack
        :param correlation_id:                  (mandatory) [str]
            an ID that a user's application had previously supplied to user
            to track/correlate different messages.
        """
        raise NotImplementedError("response method must be implemented.")


class SimpleHook(BaseHook):
    """
    class implementing naz's Hook interface.
    """

    def __init__(self, logger) -> None:
        self.logger: logging.Logger = logger

    async def request(self, smpp_event: str, correlation_id: typing.Optional[str] = None) -> None:
        """
        hook method that is called just before a request is sent to SMSC.
        """
        self.logger.info(
            "{}".format(
                {
                    "event": "SimpleHook.request",
                    "stage": "start",
                    "smpp_event": smpp_event,
                    "correlation_id": correlation_id,
                }
            )
        )

    async def response(self, smpp_event: str, correlation_id: typing.Optional[str] = None) -> None:
        """
        hook method that is called just after a response is gotten from SMSC.
        """
        self.logger.info(
            "{}".format(
                {
                    "event": "SimpleHook.response",
                    "stage": "start",
                    "smpp_event": smpp_event,
                    "correlation_id": correlation_id,
                }
            )
        )
