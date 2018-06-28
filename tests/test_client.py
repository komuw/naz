# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import mock
import asyncio
from unittest import TestCase

import naz
import docker


class TestClient(TestCase):
    """
    NB: for most of this tests to run, the smpp-simluator needs to be running.
        You can run the simluator via; docker-compose run
    """

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.cli = naz.Client(
            async_loop=self.loop,
            SMSC_HOST="127.0.0.1",
            SMSC_PORT=2775,
            system_id="smppclient1",
            password="password",
        )

        self.docker_client = docker.from_env()
        smppSimulatorName = "nazTestSmppSimulator"
        running_containers = self.docker_client.containers.list()
        for container in running_containers:
            container.stop()

        self.smpp_simulator = self.docker_client.containers.run(
            "komuw/smpp_server:v0.2",
            name=smppSimulatorName,
            detach=True,
            auto_remove=True,
            labels={"name": "smpp_server", "use": "running_naz_tets"},
            ports={"2775/tcp": 2775, "8884/tcp": 8884},
            stdout=True,
            stderr=True,
        )

    def tearDown(self):
        self.smpp_simulator.stop()

    def _run(self, coro):
        """
        helper function that runs any coroutine in an event loop and passes its return value back to the caller.
        https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
        """
        return self.loop.run_until_complete(coro)

    def test_bad_instantiation(self):
        def mock_create_client():
            cli = naz.Client(
                async_loop=self.loop,
                SMSC_HOST="127.0.0.1",
                SMSC_PORT=2775,
                system_id="smppclient1",
                password="password",
                log_metadata="bad-Type",
            )

        self.assertRaises(ValueError, mock_create_client)
        with self.assertRaises(ValueError) as raised_exception:
            mock_create_client()
        self.assertIn("log_metadata should be of type", str(raised_exception.exception))

    def test_can_connect(self):
        reader, writer = self._run(self.cli.connect())
        self.assertTrue(hasattr(reader, "read"))
        self.assertTrue(hasattr(writer, "write"))
