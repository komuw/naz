import logging


class BaseLogger:
    """
    Interface that must be implemented to satisfy naz's logger.
    User implementations should inherit this class and
    implement the :func:`register <BaseLogger.register>` and :func:`log <BaseLogger.log>` methods with the type signatures shown.

    A logger is class with methods that are called whenever naz wants to log something.
    This enables developers to implement logging in any way that they want.
    """

    def register(self, loglevel: str, log_metadata: dict) -> None:
        """
        called when a naz client is been instantiated.

        Parameters:
            loglevel: logging level eg DEBUG
            log_metadata: log metadata that can be included in all log statements
        """
        raise NotImplementedError("register method must be implemented.")

    def log(self, level: int, log_data: dict) -> None:
        """
        called by naz everytime it wants to log something.

        Parameters:
            level: logging level eg `logging.INFO`
            log_data: the message to log
        """
        raise NotImplementedError("log method must be implemented.")


class SimpleBaseLogger(BaseLogger):
    """
    This is an implementation of BaseLogger.
    It implements a structured logger that renders logs in a json/dict like manner.

    example usage:

    .. code-block:: python

        logger = SimpleBaseLogger()
        logger.register(loglevel="INFO",
                        log_metadata={"customer_id": "34541"})
        logger.log(logging.INFO,
                   {"event": "web_request", "url": "https://www.google.com/"})
    """

    def register(self, loglevel: str, log_metadata: dict) -> None:
        self._logger = logging.getLogger("naz.client")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self._logger.handlers:
            self._logger.addHandler(handler)
        self._logger.setLevel(loglevel)
        self.logger: logging.LoggerAdapter = NazLoggingAdapter(self._logger, log_metadata)

    def log(self, level: int, log_data: dict) -> None:
        if level >= logging.ERROR:
            self.logger.log(level, log_data, exc_info=True)
        else:
            self.logger.log(level, log_data)


class NazLoggingAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if isinstance(msg, str):
            return msg, kwargs
        else:
            merged_log_event = {**msg, **self.extra}
            return "{0}".format(merged_log_event), kwargs
