import abc
import typing
import logging


class BaseLogger(abc.ABC):
    """
    Interface that must be implemented to satisfy naz's logger.
    User implementations should inherit this class and
    implement the :func:`bind <BaseLogger.bind>` and :func:`log <BaseLogger.log>` methods with the type signatures shown.

    A logger is class with methods that are called whenever naz wants to log something.
    This enables developers to implement logging in any way that they want.
    """

    @abc.abstractmethod
    def bind(self, loglevel: str, log_metadata: dict) -> None:
        """
        called when a naz client is been instantiated so that the logger can be
        notified of loglevel & log_metadata that a user supplied to a naz client.
        The logger can choose to bind these log_metadata to itself.

        Parameters:
            loglevel: logging level eg DEBUG
            log_metadata: log metadata that can be included in all log statements
        """
        raise NotImplementedError("bind method must be implemented.")

    @abc.abstractmethod
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

        logger = SimpleBaseLogger("myLogger")
        logger.bind(loglevel="INFO",
                    log_metadata={"customer_id": "34541"})
        logger.log(logging.INFO,
                   {"event": "web_request", "url": "https://www.google.com/"})
    """

    def __init__(self, logger_name: str):
        """
        Parameters:
            logger_name: name of the logger
        """
        self.logger_name = logger_name
        self.logger: typing.Any = None

    def bind(self, loglevel: str, log_metadata: dict) -> None:
        self._logger = logging.getLogger(self.logger_name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self._logger.handlers:
            self._logger.addHandler(handler)
        self._logger.setLevel(loglevel)
        self.logger: logging.LoggerAdapter = NazLoggingAdapter(self._logger, log_metadata)

    def log(self, level: int, log_data: dict) -> None:
        if not self.logger:
            self.bind(loglevel="DEBUG", log_metadata={})
        if level >= logging.ERROR:
            self.logger.log(level, log_data, exc_info=True)
        else:
            self.logger.log(level, log_data)


class NazLoggingAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if isinstance(msg, str):
            merged_msg = "{0} {1}".format(msg, self.extra)
            return merged_msg, kwargs
        else:
            merged_msg = {**msg, **self.extra}
            return "{0}".format(merged_msg), kwargs
