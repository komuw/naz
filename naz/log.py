import time
import json
import typing
import logging
import collections
from logging import handlers


class SimpleLogger(logging.Logger):
    """
    It implements a structured logger that renders logs as json.

    example usage:

    .. highlight:: python
    .. code-block:: python

        logger = SimpleLogger("myLogger")
        logger.log(logging.INFO,
                   {"event": "web_request", "url": "https://www.google.com/"})
    """

    def __init__(
        self,
        logger_name: str,
        level: typing.Union[str, int] = logging.INFO,
        log_metadata: typing.Union[None, dict] = None,
        handler: typing.Union[None, logging.Handler] = None,
    ) -> None:
        """
        Parameters:
            logger_name: name of the logger. it should be unique per logger.
            level: the level at which to log
            log_metadata: metadata that will be included in all log statements
            handler: python logging `handler <https://docs.python.org/3/library/logging.html#logging.Handler>`_ to be attached to this logger.
                     By default, `logging.StreamHandler` is used.
        """
        super(SimpleLogger, self).__init__(name=logger_name, level=self._nameToLevel(level))
        if not isinstance(logger_name, str):
            raise ValueError(
                "`logger_name` should be of type:: `str` You entered: {0}".format(type(logger_name))
            )
        if not isinstance(level, (int, str)):
            raise ValueError(
                "`level` should be of type:: `str` or `int` You entered: {0}".format(type(level))
            )
        if isinstance(level, str):
            if level.upper() not in ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                raise ValueError(
                    """`level` should be one of; 'NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'. You entered: {0}""".format(
                        level
                    )
                )
        if not isinstance(log_metadata, (type(None), dict)):
            raise ValueError(
                "`log_metadata` should be of type:: `None` or `dict` You entered: {0}".format(
                    type(log_metadata)
                )
            )
        if not isinstance(handler, (type(None), logging.Handler)):
            raise ValueError(
                "`log_metadata` should be of type:: `None` or `logging.Handler` You entered: {0}".format(
                    type(handler)
                )
            )
        self.logger_name = logger_name
        self.level = self._nameToLevel(level)
        if log_metadata is not None:
            self.log_metadata = log_metadata
        else:
            self.log_metadata = {}

        if handler is not None:
            self.handler = handler
        else:
            self.handler = logging.StreamHandler()

        self._set_logger_details()

    def _set_logger_details(self) -> None:
        formatter = logging.Formatter("%(message)s")
        self.handler.setFormatter(formatter)
        self.handler.setLevel(self.level)
        self.addHandler(self.handler)
        self.setLevel(self.level)

    def log(self, level, msg, *args, **kwargs):
        """
        Log 'msg % args' with the integer severity 'level'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.log(level, "We have a %s", "mysterious problem", exc_info=1)
        """
        if self._nameToLevel(level) >= logging.ERROR:
            kwargs.update(dict(exc_info=True))

        new_msg = self._process_msg(msg)
        return super(SimpleLogger, self).log(level, new_msg, *args, **kwargs)

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

    def _process_msg(self, msg: typing.Union[str, dict]) -> str:
        timestamp = self._formatTime()
        if isinstance(msg, dict):
            _timestamp = {"timestamp": timestamp}
            # _timestamp should appear first in resulting dict
            dict_merged_msg = {**_timestamp, **msg, **self.log_metadata}
            return self._to_json(dict_merged_msg)
        else:
            str_merged_msg = "{0} {1} {2}".format(timestamp, msg, self.log_metadata)
            if self.log_metadata == {}:
                str_merged_msg = "{0} {1}".format(timestamp, msg)
            return self._to_json(str_merged_msg)

    def _formatTime(self) -> str:
        """
        Return the creation time of the specified log event as formatted text.

        This code is borrowed from:
        https://docs.python.org/3/library/logging.html#logging.Formatter.formatTime

        The basic behaviour is as follows: an ISO8601-like (or RFC 3339-like) format is used.
        This function uses `time.localtime()` to convert the creation time to a tuple.
        """
        _converter = time.localtime
        _formatter = logging.Formatter()

        now = time.time()
        msecs = (now - int(now)) * 1000

        ct = _converter(now)  # type: ignore
        t = time.strftime(_formatter.default_time_format, ct)
        s = _formatter.default_msec_format % (t, msecs)
        return s

    def _to_json(self, input_msg):
        """
        tries to convert the input message to json and returns it.
        if it fails, it returns the error in string(not json) format
        """
        msg = ""
        try:
            msg = json.dumps(input_msg)
        except Exception as e:
            msg = "naz.SimpleLogger error: {0}".format(str(e))
        return msg


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
        logger = naz.log.SimpleLogger("aha", handler=_handler, log_metadata={"id": "123"})

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
        target: typing.Union[None, logging.Handler] = None,
        flushOnClose: bool = False,
        heartbeatInterval: typing.Union[None, float] = None,
        targetLevel: str = "DEBUG",
    ) -> None:
        """
        Parameters:
            flushLevel: the log level that will trigger this handler to flush logs to :py:attr:`~target`
            capacity: the maximum number of log records to store in the ring buffer
            target: the `log handler <https://docs.python.org/3/library/logging.html#logging.Handler>`_ that will be used.
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
        if target is None:
            target = logging.StreamHandler()

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
        target: typing.Union[None, logging.Handler],
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
        if not isinstance(target, (type(None), logging.Handler)):
            raise ValueError(
                "`target` should be of type:: `None` or `logging.Handler` You entered: {0}".format(
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
