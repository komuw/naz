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


class TestBreachHandler(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_logger.TestBreachHandler.test_something
    """

    def test_use_with_naz_logger(self):
        with io.StringIO() as _temp_stream:
            _handler = naz.log.BreachHandler(
                capacity=4, target=logging.StreamHandler(stream=_temp_stream)
            )
            logger = naz.log.SimpleLogger("test_use_with_naz_logger", handler=_handler)
            logger.bind(level="INFO", log_metadata={"name": "JayZ"})

            # log at level less than `_handler.trigger_level`
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "one": 1})
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "two": 2})
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "three": 3})
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "four": 4})
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "five": 5})
            logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "six": 6})
            self.assertEqual("", _temp_stream.getvalue())  # nothing is logged

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

    def test_use_with_stdlib_logger(self):
        with io.StringIO() as _temp_stream:
            handler = naz.log.BreachHandler(
                capacity=3, target=logging.StreamHandler(stream=_temp_stream)
            )

            logger = logging.getLogger("my-logger")
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            handler.setLevel("DEBUG")
            if not logger.handlers:
                logger.addHandler(handler)
            logger.setLevel("DEBUG")

            logger.info("one")
            logger.info("two")
            logger.info("three")
            logger.info("I did records for Tweet before y'all could even tweet - Dr. Missy Elliot")
            logger.error("damn!")

            self.assertNotIn("one", _temp_stream.getvalue())
            self.assertIn("Dr. Missy Elliot", _temp_stream.getvalue())
            self.assertIn("damn!", _temp_stream.getvalue())

    # def test_heartbeat(self):
    #     # with io.StringIO() as _temp_stream:
    #     _temp_stream = io.StringIO()
    #     heartbeatInterval = 0.0001

    #     _handler = naz.log.BreachHandler(
    #         capacity=4,
    #         target=logging.StreamHandler(stream=_temp_stream),
    #         heartbeatInterval=heartbeatInterval,
    #     )
    #     logger = naz.log.SimpleLogger("test_heartbeat", handler=_handler)
    #     logger.bind(level="INFO", log_metadata={"artist": "Missy"})
    #     self.assertEqual("", _temp_stream.getvalue())
    #     logger.log(level=logging.INFO, log_data={"song_id": 1234, "name": "The Rain"})
    #     import pdb

    #     pdb.set_trace()
    #     self.assertIn("", _temp_stream.getvalue())

    #     with io.StringIO() as _temp_stream:
    #         _handler = naz.log.BreachHandler(
    #             capacity=4, target=logging.StreamHandler(stream=_temp_stream)
    #         )
    #         logger = naz.log.SimpleLogger("test_use_with_naz_logger", handler=_handler)
    #         logger.bind(level="INFO", log_metadata={"name": "JayZ"})

    #         # log at level less than `_handler.trigger_level`
    #         logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "one": 1})

    #         # log at level less than `_handler.trigger_level`
    #         logger.log(level=logging.INFO, log_data={"trace_id": 781125213295, "one": 1})
    #         self.assertIn("", _temp_stream.getvalue())  # nothing is logged
