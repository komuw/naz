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

    async def request(self, event: str, correlation_id: typing.Optional[str] = None) -> None:
        """
        called before a request is sent to SMSC
        """
        raise NotImplementedError("request method must be implemented.")

    async def response(self, event: str, correlation_id: typing.Optional[str] = None) -> None:
        """
        called after a response is received from SMSC.
        """
        raise NotImplementedError("response method must be implemented.")


class SimpleHook(BaseHook):
    """
    class implementing naz's Hook interface.
    """

    def __init__(self, logger) -> None:
        self.logger: logging.Logger = logger

    async def request(self, event: str, correlation_id: typing.Optional[str] = None) -> None:
        """
        hook method that is called just before a request is sent to SMSC.
        """
        self.logger.info(
            "{}".format(
                {"event": "SimpleHook.request", "stage": "start", "correlation_id": correlation_id}
            )
        )

    async def response(self, event: str, correlation_id: typing.Optional[str] = None) -> None:
        """
        hook method that is called just after a response is gotten from SMSC.
        """
        self.logger.info(
            "{}".format(
                {"event": "SimpleHook.response", "stage": "start", "correlation_id": correlation_id}
            )
        )
