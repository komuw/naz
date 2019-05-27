import os
import uuid
import signal
import asyncio
import argparse
from unittest import TestCase, mock

import cli
import naz


def AsyncMock(*args, **kwargs):
    """
    see: https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
    """
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


class TestCliSigHandling(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_cli.TestCliSigHandling.test_something
    """

    def setUp(self):
        self.client = naz.Client(
            smsc_host="smsc_host",
            smsc_port=6767,
            system_id="system_id",
            password=os.environ.get("password", "password"),
            outboundqueue=naz.q.SimpleOutboundQueue(),
        )
        self.loop = asyncio.get_event_loop()
        self.logger = naz.logger.SimpleLogger("naz.TestCliSigHandling")

    def tearDown(self):
        pass

    def _run(self, coro):
        return self.loop.run_until_complete(coro)

    def test_success_signal_handling(self):
        self._run(
            cli.utils.sig._signal_handling(logger=self.logger, client=self.client, loop=self.loop)
        )

    def test_success_handle_termination_signal(self):
        with mock.patch("naz.Client.shutdown", new=AsyncMock()) as mock_naz_shutdown:
            self._run(
                cli.utils.sig._handle_termination_signal(
                    logger=self.logger, _signal=signal.SIGTERM, client=self.client
                )
            )
            self.assertTrue(mock_naz_shutdown.mock.called)
