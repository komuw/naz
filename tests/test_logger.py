# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html


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
        self.logger = naz.logger.SimpleBaseLogger("myLogger")

    def tearDown(self):
        pass

    def test_can_bind(self):
        self.logger.bind(loglevel="INFO", log_metadata={"customer_id": "34541"})

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
        self.logger.bind(loglevel="INFO", log_metadata={"customer_id": "34541"})
        self.logger.log(level=logging.WARN, log_data="can log string")

    def test_bind_and_log_dict(self):
        self.logger.bind(loglevel="INFO", log_metadata={"customer_id": "34541"})
        self.logger.log(level=logging.WARN, log_data={"name": "Magic Johnson"})
