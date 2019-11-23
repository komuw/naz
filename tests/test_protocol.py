# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import asyncio
from unittest import TestCase

import naz


class TestProtocol(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_protocol.TestProtocol.test_something
    """

    def setUp(self):
        self.msg_protocol = naz.protocol.Message(
            version=1, smpp_command=naz.SmppCommand.SUBMIT_SM, log_id="some-log-id"
        )

    def tearDown(self):
        pass

    @staticmethod
    def _run(coro):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def test_something(self):
        # TODO: rename this.
        self.assertEqual(8, 9)
