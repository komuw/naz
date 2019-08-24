# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html


import io
import logging
import datetime
from unittest import TestCase

import naz


class TestLogger(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_logger.TestLogger.test_something
    """

    def setUp(self):
        self.logger = naz.log.SimpleLogger("myLogger")

    def tearDown(self):
        pass

    def test_can_bind(self):
        self.logger.bind(level="INFO", log_metadata={"customer_id": "34541"})

    def test_can_log_string(self):
        self.logger.log(level=logging.WARN, log_data="can log string")

    def test_can_log_dict(self):
        log_id = 234_255
        now = datetime.datetime.now()
        self.logger.log(
            level=logging.WARN,
            log_data={"event": "myEvent", "stage": "start", "log_id": log_id, "now": now},
        )

    def test_bind_and_log_string(self):
        self.logger.bind(level="INFO", log_metadata={"customer_id": "34541"})
        self.logger.log(level=logging.WARN, log_data="can log string")

    def test_bind_and_log_dict(self):
        self.logger.bind(level="INFO", log_metadata={"customer_id": "34541"})
        self.logger.log(level=logging.WARN, log_data={"name": "Magic Johnson"})

    def test_custom_handler(self):
        with io.StringIO() as _temp_stream:
            _handler = logging.StreamHandler(stream=_temp_stream)
            logger = naz.log.SimpleLogger("yo", handler=_handler)
            logger.bind(level="INFO", log_metadata={"name": "JayZ"})
            logger.log(level=logging.WARN, log_data={"someKey": "someValue"})

            self.assertIn("JayZ", _temp_stream.getvalue())

        _file_name = "/{0}/naz_test_custom_handler".format("tmp")  # fool bandit
        _handler = logging.FileHandler(filename=_file_name)
        logger = naz.log.SimpleLogger("yolo", handler=_handler)
        logger.bind(level="INFO", log_metadata={"name": "JayZ"})
        logger.log(level=logging.WARN, log_data={"someKey": "someValue"})

        with open(_file_name) as f:
            content = f.read()
            self.assertIn("JayZ", content)

    def test_breach_handler(self):
        with io.StringIO() as _temp_stream:
            _handler = naz.log.BreachHandler(buffer_size=4, stream=_temp_stream)
            logger = naz.log.SimpleLogger("aha", handler=_handler)
            logger.bind(level="INFO", log_metadata={"name": "JayZ"})

            # log at level less than `_handler.trigger_level`
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "one": 1})
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "two": 2})
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "three": 3})
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "four": 4})
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "five": 5})
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "six": 6})
            self.assertIn("", _temp_stream.getvalue())  # nothing is logged

            # log at level greater than or equal to `_handler.trigger_level`
            logger.log(level=logging.WARN, log_data={"trace_id": 781125213295, "seven": 7})

            # assert that the handler used a circular buffer
            self.assertNotIn("one", _temp_stream.getvalue())
            self.assertNotIn("two", _temp_stream.getvalue())
            self.assertNotIn("three", _temp_stream.getvalue())

            # assert everything in the buffer after trigger level is reached
            # is flushed to `_handler.stream`
            self.assertIn("five", _temp_stream.getvalue())
            self.assertIn("six", _temp_stream.getvalue())
            self.assertIn("seven", _temp_stream.getvalue())
            self.assertIn(str(781125213295), _temp_stream.getvalue())


class KVlogger(naz.log.BaseLogger):
    """
    A simple implementation of a key=value
    log renderer.
    """

    def __init__(self):
        self.logger = logging.getLogger("myKVlogger")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel("DEBUG")

    def bind(self, level, log_metadata):
        pass

    def log(self, level, log_data):
        # implementation of key=value log renderer
        message = ", ".join("{0}={1}".format(k, v) for k, v in log_data.items())
        self.logger.log(level, message)


class TestCustomLogger(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_logger.TestCustomLogger.test_something
    """

    def setUp(self):
        self.kvLog = KVlogger()

    def tearDown(self):
        pass

    def test_can_bind(self):
        self.kvLog.bind(level="INFO", log_metadata={"customer_id": "34541"})

    def test_can_log_dict(self):
        log_id = 234_255
        now = datetime.datetime.now()
        self.kvLog.log(
            level=logging.WARN,
            log_data={"event": "myEvent", "stage": "start", "log_id": log_id, "now": now},
        )
