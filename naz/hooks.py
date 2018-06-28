import logging


class DefaultHook:
    """
    class with hook methods that are called before a request is sent to SMSC and
    after a response is received from SMSC.

    User's can provide their own hook classes
    """

    def __init__(self, logger=None, LOG_LEVEL="DEBUG"):
        self.LOG_LEVEL = LOG_LEVEL
        self.logger = logger
        if not self.logger:
            self.logger = logging.getLogger()
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            if not self.logger.handlers:
                self.logger.addHandler(handler)
            self.logger.setLevel(self.LOG_LEVEL)

    async def request(self, event, correlation_id=None):
        """
        hook method that is called just before a request is sent to SMSC.
        """
        self.logger.debug(
            "request_hook_called. event={0}. correlation_id={1}".format(event, correlation_id)
        )

    async def response(self, event, correlation_id=None):
        """
        hook method that is called just after a response is gotten from SMSC.
        """
        self.logger.debug(
            "response_hook_called. event={0}. correlation_id={1}".format(event, correlation_id)
        )
