import abc
import time
import typing
import logging
import collections
from logging import handlers


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

    def __init__(
        self, logger_name: str, handler: logging.Handler = logging.StreamHandler()
    ) -> None:
        """
        Parameters:
            logger_name: name of the logger. it should be unique per logger.
        """
        if not isinstance(logger_name, str):
            raise ValueError(
                "`logger_name` should be of type:: `str` You entered: {0}".format(type(logger_name))
            )
        if not isinstance(handler, logging.Handler):
            raise ValueError(
                "`handler` should be of type:: `logging.Handler` You entered: {0}".format(
                    type(handler)
                )
            )

        self.logger_name = logger_name
        self.handler = handler
        self.logger: typing.Union[None, logging.LoggerAdapter] = None

    def bind(self, level: typing.Union[str, int], log_metadata: dict) -> None:
        level = self._nameToLevel(level=level)

        self._logger = logging.getLogger(self.logger_name)
        formatter = logging.Formatter("%(message)s")
        self.handler.setFormatter(formatter)
        self.handler.setLevel(level)
        if not self._logger.handlers:
            self._logger.addHandler(self.handler)
        self._logger.setLevel(level)
        self.logger = _NazLoggingAdapter(self._logger, log_metadata)

    def log(self, level: typing.Union[str, int], log_data: typing.Union[str, dict]) -> None:
        level = self._nameToLevel(level=level)

        if not self.logger:
            self.bind(level=level, log_metadata={})
        if typing.TYPE_CHECKING:
            # make mypy happy; https://github.com/python/mypy/issues/4805
            assert isinstance(self.logger, logging.LoggerAdapter)

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


class _NazLoggingAdapter(logging.LoggerAdapter):
    _converter = time.localtime
    _formatter = logging.Formatter()

    def process(
        self, msg: typing.Union[str, dict], kwargs: typing.MutableMapping[str, typing.Any]
    ) -> typing.Tuple[str, typing.MutableMapping[str, typing.Any]]:
        timestamp = self.formatTime()

        if isinstance(msg, str):
            str_merged_msg = "{0} {1} {2}".format(timestamp, msg, self.extra)
            if self.extra == {}:
                str_merged_msg = "{0} {1}".format(timestamp, msg)
            return str_merged_msg, kwargs
        else:
            _timestamp = {"timestamp": timestamp}
            # _timestamp should appear first in resulting dict
            dict_merged_msg = {**_timestamp, **msg, **self.extra}
            return "{0}".format(dict_merged_msg), kwargs

    def formatTime(self) -> str:
        """
        Return the creation time of the specified log event as formatted text.

        This code is borrowed from:
        https://docs.python.org/3/library/logging.html#logging.Formatter.formatTime

        The basic behaviour is as follows: an ISO8601-like (or RFC 3339-like) format is used.
        This function uses `time.localtime()` to convert the creation time to a tuple.
        """
        now = time.time()
        msecs = (now - int(now)) * 1000

        ct = self._converter(now)  # type: ignore
        t = time.strftime(self._formatter.default_time_format, ct)
        s = self._formatter.default_msec_format % (t, msecs)
        return s


class BreachHandler(handlers.MemoryHandler):
    """
    This is an implementation of `logging.Handler` that puts logs in an in-memory ring buffer.
    When a trigger condition(eg a certain log level) is met;
    then all the logs in the buffer are flushed into a given stream(file, stdout etc)

    It is a bit like
    `logging.handlers.MemoryHandler <https://docs.python.org/3/library/logging.handlers.html#logging.handlers.MemoryHandler>`_
    except that it does not flush when the ring-buffer capacity is met but only when/if the trigger is met.

    It is inspired by the article
    `Triggering Diagnostic Logging on Exception <https://tersesystems.com/blog/2019/07/28/triggering-diagnostic-logging-on-exception/>`_

    example usage:

    .. highlight:: python
    .. code-block:: python

        import naz, logging

        _handler = naz.log.BreachHandler()
        logger = naz.log.SimpleLogger("aha", handler=_handler)
        logger.bind(level="INFO", log_metadata={"id": "123"})

        logger.log(logging.INFO, {"name": "Jayz"})
        logger.log(logging.ERROR, {"msg": "Houston, we got 99 problems."})

        # or alternatively, to use it with python stdlib logger
        logger = logging.getLogger("my-logger")
        handler = naz.log.BreachHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        handler.setLevel("DEBUG")
        if not logger.handlers:
            logger.addHandler(handler)
        logger.setLevel("DEBUG")

        logger.info("I did records for Tweet before y'all could even tweet - Dr. Missy Elliot")
        logger.error("damn")
    """

    def __init__(
        self,
        flushLevel: int = logging.WARNING,
        capacity: int = 1_000,
        target: logging.Handler = logging.StreamHandler(),
        flushOnClose: bool = False,
        heartbeatInterval: typing.Union[None, float] = None,
        targetLevel: str = "DEBUG",
    ) -> None:
        """
        Parameters:
            flushLevel: the log level that will trigger this handler to flush logs to :py:attr:`~target`
            capacity: the maximum number of log records to store in the ring buffer
            target: the ultimate `log handler <https://docs.python.org/3/library/logging.html#logging.Handler>`_ that will be used.
            flushOnClose: whether to flush the buffer when the handler is closed even if the flush level hasn't been exceeded
            heartbeatInterval: can be a float or None. If it is a float, then a heartbeat log record will be emitted every :py:attr:`~heartbeatInterval` seconds.
                               If it is None(the default), then no heartbeat log record is emitted.
                               If you do decide to set it, a good value is at least 1800(ie 30 minutes).
            targetLevel: the log level to be applied/set to :py:attr:`~target`
        """
        self._validate_args(
            flushLevel=flushLevel,
            capacity=capacity,
            target=target,
            flushOnClose=flushOnClose,
            heartbeatInterval=heartbeatInterval,
            targetLevel=targetLevel,
        )
        # call `logging.handlers.MemoryHandler` init
        super(BreachHandler, self).__init__(  # type: ignore
            capacity=capacity,
            flushLevel=flushLevel,
            target=target,
            flushOnClose=flushOnClose,  # pytype: disable=wrong-keyword-args
        )
        self.buffer: collections.deque = collections.deque(
            maxlen=self.capacity  # type: ignore
        )  # pytype: disable=attribute-error
        # assuming each log record is 250 bytes, then the maximum
        # memory used by `buffer` will always be == 250*10_000/(1000*1000) == 2.5MB

        self.heartbeatInterval = heartbeatInterval
        if self.heartbeatInterval:
            self.heartbeatInterval = heartbeatInterval  # seconds
            self._s_time = time.monotonic()

        self.targetLevel: int = logging._nameToLevel[targetLevel.upper()]
        self.target.setLevel(self.targetLevel)  # type: ignore

    def shouldFlush(self, record: logging.LogRecord) -> bool:
        """
        Check for record at the flushLevel or higher.
        Implementation is mostly taken from `logging.handlers.MemoryHandler`
        """
        return record.levelno >= self.flushLevel  # type: ignore # pytype: disable=attribute-error

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record.
        Append the record. If shouldFlush() tells us to, call flush() to process
        the buffer.

        Implementation is taken from `logging.handlers.MemoryHandler`
        """
        self._heartbeat()

        if record.levelno >= self.targetLevel:
            self.buffer.append(record)
        if self.shouldFlush(record):
            self.flush()

    def _heartbeat(self) -> None:
        if not self.heartbeatInterval:
            return

        # check if `heartbeatInterval` seconds have passed.
        # if they have, emit a heartbeat log record to the target handler
        _now = time.monotonic()
        _diff = _now - self._s_time
        if _diff >= self.heartbeatInterval:
            self._s_time = _now
            # see: https://docs.python.org/3/library/logging.html#logging.LogRecord
            record = logging.makeLogRecord(
                {
                    "level": logging.INFO,
                    "name": "BreachHandler",
                    "pathname": ".../naz/naz/log.py",
                    "func": "BreachHandler._heartbeat",
                    "msg": {
                        "event": "naz.BreachHandler.heartbeat",
                        "heartbeatInterval": self.heartbeatInterval,
                    },
                }
            )
            self.target.emit(record=record)  # type: ignore # pytype: disable=attribute-error

    @staticmethod
    def _validate_args(
        flushLevel: int,
        capacity: int,
        target: logging.Handler,
        flushOnClose: bool,
        heartbeatInterval: typing.Union[None, float],
        targetLevel: str,
    ) -> None:
        if not isinstance(flushLevel, int):
            raise ValueError(
                "`flushLevel` should be of type:: `int` You entered: {0}".format(type(flushLevel))
            )
        if not isinstance(capacity, int):
            raise ValueError(
                "`capacity` should be of type:: `int` You entered: {0}".format(type(capacity))
            )

        if not isinstance(target, logging.Handler):
            raise ValueError(
                "`target` should be of type:: `logging.Handler` You entered: {0}".format(
                    type(target)
                )
            )
        if not isinstance(flushOnClose, bool):
            raise ValueError(
                "`flushOnClose` should be of type:: `bool` You entered: {0}".format(
                    type(flushOnClose)
                )
            )
        if not isinstance(heartbeatInterval, (type(None), float)):
            raise ValueError(
                "`heartbeatInterval` should be of type:: `None` or `float` You entered: {0}".format(
                    type(heartbeatInterval)
                )
            )
        if not isinstance(targetLevel, str):
            raise ValueError(
                "`targetLevel` should be of type:: `str` You entered: {0}".format(type(targetLevel))
            )
        if targetLevel.upper() not in ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(
                """`targetLevel` should be one of; 'NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'. You entered: {0}""".format(
                    targetLevel
                )
            )
