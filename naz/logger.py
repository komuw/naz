import abc
import time
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
    def bind(self, level: typing.Union[str, int], log_metadata: dict) -> None:
        """
        called when a naz client is been instantiated so that the logger can be
        notified of loglevel & log_metadata that a user supplied to a naz client.
        The logger can choose to bind these log_metadata to itself.

        Parameters:
            loglevel: logging level eg DEBUG
            log_metadata: log metadata that can be included in all log statements
        """
        raise NotImplementedError("`bind` method must be implemented.")

    @abc.abstractmethod
    def log(self, level: typing.Union[str, int], log_data: dict) -> None:
        """
        called by naz everytime it wants to log something.

        Parameters:
            level: logging level eg `logging.INFO`
            log_data: the message to log
        """
        raise NotImplementedError("`log` method must be implemented.")


class SimpleLogger(BaseLogger):
    """
    This is an implementation of BaseLogger.
    It implements a structured logger that renders logs as a dict.

    example usage:

    .. highlight:: python
    .. code-block:: python

        logger = SimpleLogger("myLogger")
        logger.bind(level="INFO",
                    log_metadata={"customer_id": "34541"})
        logger.log(logging.INFO,
                   {"event": "web_request", "url": "https://www.google.com/"})
    """

    def __init__(self, logger_name: str):
        """
        Parameters:
            logger_name: name of the logger. it should be unique per logger.
        """
        if not isinstance(logger_name, str):
            raise ValueError(
                "`logger_name` should be of type:: `str` You entered: {0}".format(type(logger_name))
            )

        self.logger_name = logger_name
        self.logger: typing.Any = None

    def bind(self, level: typing.Union[str, int], log_metadata: dict) -> None:
        level = self._nameToLevel(level=level)

        self._logger = logging.getLogger(self.logger_name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(level)
        if not self._logger.handlers:
            self._logger.addHandler(handler)
        self._logger.setLevel(level)
        self.logger: logging.LoggerAdapter = NazLoggingAdapter(self._logger, log_metadata)

    def log(self, level: typing.Union[str, int], log_data: dict) -> None:
        level = self._nameToLevel(level=level)

        if not self.logger:
            self.bind(level=level, log_metadata={})
        if level >= logging.ERROR:
            self.logger.log(level, log_data, exc_info=True)
        else:
            self.logger.log(level, log_data)

    @staticmethod
    def _nameToLevel(level: typing.Union[str, int]) -> int:
        try:
            if isinstance(level, str):
                # please mypy
                _level: int = logging._nameToLevel[level.upper()]
            else:
                _level = level
            return _level
        except KeyError as e:
            raise ValueError(
                "`level` should be one of; 'NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'"
            ) from e


class NazLoggingAdapter(logging.LoggerAdapter):
    _converter = time.localtime
    _formatter = logging.Formatter()

    def process(self, msg, kwargs):
        timestamp = self.formatTime()

        if isinstance(msg, str):
            merged_msg = "{0} {1} {2}".format(timestamp, msg, self.extra)
            if self.extra == {}:
                merged_msg = "{0} {1}".format(timestamp, msg)
            return merged_msg, kwargs
        else:
            _timestamp = {"timestamp": timestamp}
            # _timestamp should appear first in resulting dict
            merged_msg = {**_timestamp, **msg, **self.extra}
            return "{0}".format(merged_msg), kwargs

    def formatTime(self):
        """
        Return the creation time of the specified log event as formatted text.

        This code is borrowed from:
        https://docs.python.org/3/library/logging.html#logging.Formatter.formatTime

        The basic behaviour is as follows: an ISO8601-like (or RFC 3339-like) format is used.
        This function uses `time.localtime()` to convert the creation time to a tuple.
        """
        now = time.time()
        msecs = (now - int(now)) * 1000

        ct = self._converter(now)
        t = time.strftime(self._formatter.default_time_format, ct)
        s = self._formatter.default_msec_format % (t, msecs)
        return s
