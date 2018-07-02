# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import os
import mock
import asyncio
from unittest import TestCase

import naz
import docker


import sys
import logging

logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.DEBUG)


def AsyncMock(*args, **kwargs):
    """
    see: https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
    """
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


class TestClient(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_client.TestClient.test_can_connect
    """

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.cli = naz.Client(
            async_loop=self.loop,
            smsc_host="127.0.0.1",
            smsc_port=2775,
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
        if os.environ.get("CI_ENVIRONMENT"):
            print("\n\nrunning in CI env.\n")
            self.smpp_simulator.remove(force=True)
        else:
            pass

    def _run(self, coro):
        """
        helper function that runs any coroutine in an event loop and passes its return value back to the caller.
        https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
        """
        return self.loop.run_until_complete(coro)

    def test_bad_instantiation(self):
        def mock_create_client():
            naz.Client(
                async_loop=self.loop,
                smsc_host="127.0.0.1",
                smsc_port=2775,
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

    def test_can_bind(self):
        with mock.patch("naz.Client.send_data", new=AsyncMock()) as mock_naz_send_data:
            self._run(self.cli.tranceiver_bind())
            self.assertTrue(mock_naz_send_data.mock.called)
            self.assertEqual(mock_naz_send_data.mock.call_count, 1)
            self.assertEqual(mock_naz_send_data.mock.call_args[0][1], "bind_transceiver")
        # todo: test bind_response

    def test_submit_sm_enqueue(self):
        with mock.patch("naz.q.DefaultOutboundQueue.enqueue", new=AsyncMock()) as mock_naz_enqueue:
            reader, writer = self._run(self.cli.connect())
            self._run(self.cli.tranceiver_bind())
            correlation_id = "12345"
            self._run(
                self.cli.submit_sm(
                    short_message="hello smpp",
                    correlation_id=correlation_id,
                    source_addr="9090",
                    destination_addr="254722000111",
                )
            )
            self.assertTrue(mock_naz_enqueue.mock.called)
            self.assertEqual(
                mock_naz_enqueue.mock.call_args[0][1]["correlation_id"], correlation_id
            )
            self.assertEqual(mock_naz_enqueue.mock.call_args[0][1]["event"], "submit_sm")

    def test_submit_sm_sending(self):
        with mock.patch("naz.q.DefaultOutboundQueue.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            correlation_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = {
                "correlation_id": correlation_id,
                "pdu": short_message,
                "event": "submit_sm",
            }
            reader, writer = self._run(self.cli.connect())
            self._run(self.cli.send_forever(TESTING=True))

            self.assertTrue(mock_naz_dequeue.mock.called)

    def test_parse_response_pdu(self):
        with mock.patch(
            "naz.Client.speficic_handlers", new=AsyncMock()
        ) as mock_naz_speficic_handlers:
            self._run(
                self.cli.parse_response_pdu(
                    pdu=b"\x00\x00\x00\x18\x80\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x06SMPPSim\x00"
                )
            )

            self.assertTrue(mock_naz_speficic_handlers.mock.called)
            self.assertEqual(mock_naz_speficic_handlers.mock.call_count, 1)
            self.assertEqual(
                mock_naz_speficic_handlers.mock.call_args[1]["command_id_name"],
                "bind_transceiver_resp",
            )

    def test_speficic_handlers(self):
        with mock.patch(
            "naz.Client.enquire_link_resp", new=AsyncMock()
        ) as mock_naz_enquire_link_resp:
            sequence_number = 3
            self._run(
                self.cli.speficic_handlers(
                    command_id_name="enquire_link",
                    command_status=0,
                    sequence_number=sequence_number,
                    unparsed_pdu_body=b"Doesnt matter",
                    total_pdu_length=16,
                )
            )
            self.assertTrue(mock_naz_enquire_link_resp.mock.called)
            self.assertEqual(
                mock_naz_enquire_link_resp.mock.call_args[1]["sequence_number"], sequence_number
            )

    def test_speficic_handlers_unbind(self):
        with mock.patch("naz.Client.unbind_resp", new=AsyncMock()) as mock_naz_unbind_resp:
            sequence_number = 7
            self._run(
                self.cli.speficic_handlers(
                    command_id_name="unbind",
                    command_status=0,
                    sequence_number=sequence_number,
                    unparsed_pdu_body=b"Doesnt matter",
                    total_pdu_length=16,
                )
            )

            self.assertTrue(mock_naz_unbind_resp.mock.called)
            self.assertEqual(
                mock_naz_unbind_resp.mock.call_args[1]["sequence_number"], sequence_number
            )
