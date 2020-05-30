import os
import signal
import asyncio
from unittest import TestCase, mock

import cli
import naz
import docker

from .utils import AsyncMock, MockStreamWriter, MockArgumentParser
from examples.example_klasses import ExampleRedisBroker, MySeqGen, MyRateLimiter


NAZ_CLIENT = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    broker=ExampleRedisBroker(),
    sequence_generator=MySeqGen(),
    logger=naz.log.SimpleLogger(
        "naz.client", level="INFO", log_metadata={"environment": "production", "release": "canary"}
    ),
    enquire_link_interval=30.00,
    rate_limiter=MyRateLimiter(),
)

BAD_NAZ_CLIENT = MySeqGen()


class TestCli(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_cli.TestCli.test_bad_args
    """

    def setUp(self):
        self.parser = cli.cli.make_parser()

        self.docker_client = docker.from_env()
        smppSimulatorName = "nazTestSmppSimulator"
        running_containers = self.docker_client.containers.list()
        for container in running_containers:
            container.stop()

        self.smpp_server = self.docker_client.containers.run(
            "komuw/smpp_server:v0.3",
            name=smppSimulatorName,
            detach=True,
            auto_remove=True,
            labels={"name": "smpp_server", "use": "running_naz_tets"},
            ports={"2775/tcp": 2775, "8884/tcp": 8884},
            stdout=True,
            stderr=True,
        )
        self.naz_config = "tests.test_cli.NAZ_CLIENT"
        self.bad_naz_config = "tests.test_cli.BAD_NAZ_CLIENT"

    def tearDown(self):
        if os.environ.get("CI_ENVIRONMENT"):
            self.smpp_server.remove(force=True)
        else:
            pass

    def test_bad_args(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["naz-cli", "-someBad", "-arguments"])

    def test_cli_success(self):
        with mock.patch("argparse.ArgumentParser") as mock_ArgumentParser:
            mock_ArgumentParser.return_value = MockArgumentParser(naz_config=self.naz_config)
            cli.cli.main()

    def test_cli_failure(self):
        with self.assertRaises(SystemExit):
            with mock.patch("argparse.ArgumentParser") as mock_ArgumentParser:
                mock_ArgumentParser.return_value = MockArgumentParser(
                    naz_config=self.bad_naz_config
                )
                cli.cli.main()

    def test_load_class_error(self):
        with self.assertRaises(SystemExit):
            with mock.patch("argparse.ArgumentParser") as mock_ArgumentParser:
                mock_ArgumentParser.return_value = MockArgumentParser(naz_config="nonExistent.Path")
                cli.cli.main()


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
            broker=naz.broker.SimpleBroker(),
            drain_duration=0.001,
        )
        self.loop = asyncio.get_event_loop()
        self.logger = naz.log.SimpleLogger("naz.TestCliSigHandling")

    def tearDown(self):
        pass

    def _run(self, coro):
        return self.loop.run_until_complete(coro)

    def test_success_signal_handling(self):
        self._run(cli.utils.sig._signal_handling(logger=self.logger, client=self.client))

    def test_success_handle_termination_signal(self):
        with mock.patch("naz.Client.shutdown", new=AsyncMock()) as mock_naz_shutdown:
            self._run(
                cli.utils.sig._handle_termination_signal(
                    logger=self.logger, _signal=signal.SIGTERM, client=self.client
                )
            )
            self.assertTrue(mock_naz_shutdown.mock.called)

    def test_termination_call_client_shutdown(self):
        with mock.patch("naz.Client.unbind", new=AsyncMock()) as mock_naz_unbind:
            self.client.writer = MockStreamWriter()
            self._run(
                cli.utils.sig._handle_termination_signal(
                    logger=self.logger, _signal=signal.SIGTERM, client=self.client
                )
            )
            self.assertTrue(mock_naz_unbind.mock.called)
