# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import os
import sys
import asyncio
import logging
from unittest import TestCase

import naz
import mock
import docker


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


class MockStreamReader:
    """
    This is a mock of python's StreamReader;
    https://docs.python.org/3.6/library/asyncio-stream.html#asyncio.StreamReader

    We mock the reader having a succesful submit_sm_resp PDU.
    For the first read we return the first 4bytes,
    the second read, we return the remaining bytes.
    """

    def __init__(self, pdu):
        self.pdu = pdu

    async def read(self, n_index=-1):
        if n_index == 0:
            return b""
        blocks = []
        blocks.append(self.pdu)
        data = b"".join(blocks)
        if n_index == 4:
            return data[:n_index]
        else:
            return data[4:]


class TestClient(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_client.TestClient.test_can_connect
    """

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.outboundqueue = naz.q.SimpleOutboundQueue(maxsize=1000, loop=self.loop)
        self.cli = naz.Client(
            async_loop=self.loop,
            smsc_host="127.0.0.1",
            smsc_port=2775,
            system_id="smppclient1",
            password="password",
            outboundqueue=self.outboundqueue,
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
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def test_bad_instantiation(self):
        def mock_create_client():
            naz.Client(
                async_loop=self.loop,
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password="password",
                log_metadata="bad-Type",
                outboundqueue=self.outboundqueue,
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
            self.assertEqual(mock_naz_send_data.mock.call_args[1]["smpp_event"], "bind_transceiver")
        # todo: test bind_response

    def test_submit_sm_enqueue(self):
        with mock.patch("naz.q.SimpleOutboundQueue.enqueue", new=AsyncMock()) as mock_naz_enqueue:
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
            self.assertEqual(mock_naz_enqueue.mock.call_args[0][1]["smpp_event"], "submit_sm")

    def test_submit_sm_sending(self):
        with mock.patch("naz.q.SimpleOutboundQueue.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            correlation_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = {
                "version": "1",
                "correlation_id": correlation_id,
                "short_message": short_message,
                "smpp_event": "submit_sm",
                "source_addr": "2547000000",
                "destination_addr": "254711999999",
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
                mock_naz_speficic_handlers.mock.call_args[1]["smpp_event"], "bind_transceiver_resp"
            )

    def test_speficic_handlers(self):
        with mock.patch(
            "naz.Client.enquire_link_resp", new=AsyncMock()
        ) as mock_naz_enquire_link_resp:
            sequence_number = 3
            self._run(
                self.cli.speficic_handlers(
                    smpp_event="enquire_link",
                    correlation_id="correlation_id",
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
        with mock.patch("naz.Client.send_data", new=AsyncMock()) as mock_naz_send_data:
            sequence_number = 7
            self._run(
                self.cli.speficic_handlers(
                    smpp_event="unbind",
                    correlation_id="correlation_id",
                    command_status=0,
                    sequence_number=sequence_number,
                    unparsed_pdu_body=b"Doesnt matter",
                    total_pdu_length=16,
                )
            )
            self.assertTrue(mock_naz_send_data.mock.called)
            self.assertEqual(mock_naz_send_data.mock.call_count, 1)
            self.assertEqual(mock_naz_send_data.mock.call_args[1]["smpp_event"], "unbind_resp")

    def test_speficic_handlers_deliver_sm(self):
        with mock.patch("naz.q.SimpleOutboundQueue.enqueue", new=AsyncMock()) as mock_naz_enqueue:
            sequence_number = 7
            self._run(
                self.cli.speficic_handlers(
                    smpp_event="deliver_sm",
                    correlation_id="correlation_id",
                    command_status=0,
                    sequence_number=sequence_number,
                    unparsed_pdu_body=b"Doesnt matter",
                    total_pdu_length=16,
                )
            )
            self.assertTrue(mock_naz_enqueue.mock.called)
            self.assertEqual(mock_naz_enqueue.mock.call_args[0][1]["smpp_event"], "deliver_sm_resp")

    def test_unbind(self):
        with mock.patch("naz.Client.send_data", new=AsyncMock()) as mock_naz_send_data:
            self._run(self.cli.unbind())
            self.assertTrue(mock_naz_send_data.mock.called)
            self.assertEqual(mock_naz_send_data.mock.call_count, 1)
            self.assertEqual(mock_naz_send_data.mock.call_args[1]["smpp_event"], "unbind")

    def test_enquire_link(self):
        with mock.patch("naz.Client.send_data", new=AsyncMock()) as mock_naz_send_data:
            self._run(self.cli.enquire_link(TESTING=True))
            self.assertTrue(mock_naz_send_data.mock.called)
            self.assertEqual(mock_naz_send_data.mock.call_count, 1)
            self.assertEqual(mock_naz_send_data.mock.call_args[1]["smpp_event"], "enquire_link")

    def test_no_sending_if_throttler(self):
        with mock.patch("naz.q.SimpleOutboundQueue.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            logger = logging.getLogger("naz.test")
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            if not logger.handlers:
                logger.addHandler(handler)
            logger.setLevel("DEBUG")

            sample_size = 8
            throttle_handler = naz.throttle.SimpleThrottleHandler(
                logger=logger, sampling_period=5, sample_size=sample_size, deny_request_at=0.4
            )
            cli = naz.Client(
                async_loop=self.loop,
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password="password",
                outboundqueue=self.outboundqueue,
                throttle_handler=throttle_handler,
            )

            correlation_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = {
                "version": "1",
                "correlation_id": correlation_id,
                "short_message": short_message,
                "smpp_event": "submit_sm",
                "source_addr": "2547000000",
                "destination_addr": "254711999999",
            }
            reader, writer = self._run(cli.connect())
            # mock SMSC throttling naz
            for i in range(0, sample_size * 2):
                self._run(cli.throttle_handler.throttled())

            self._run(cli.send_forever(TESTING=True))

            self.assertFalse(mock_naz_dequeue.mock.called)

    def test_okay_smsc_response(self):
        with mock.patch(
            "naz.throttle.SimpleThrottleHandler.not_throttled", new=AsyncMock()
        ) as mock_not_throttled, mock.patch(
            "naz.throttle.SimpleThrottleHandler.throttled", new=AsyncMock()
        ) as mock_throttled:
            sequence_number = 7
            self._run(
                self.cli.speficic_handlers(
                    smpp_event="deliver_sm",
                    correlation_id="correlation_id",
                    command_status=0,
                    sequence_number=sequence_number,
                    unparsed_pdu_body=b"Doesnt matter",
                    total_pdu_length=16,
                )
            )
            self.assertTrue(mock_not_throttled.mock.called)
            self.assertEqual(mock_not_throttled.mock.call_count, 1)
            self.assertFalse(mock_throttled.mock.called)

    def test_throttling_smsc_response(self):
        with mock.patch(
            "naz.throttle.SimpleThrottleHandler.not_throttled", new=AsyncMock()
        ) as mock_not_throttled, mock.patch(
            "naz.throttle.SimpleThrottleHandler.throttled", new=AsyncMock()
        ) as mock_throttled:
            sequence_number = 7
            self._run(
                self.cli.speficic_handlers(
                    smpp_event="deliver_sm",
                    correlation_id="correlation_id",
                    command_status=0x00000058,
                    sequence_number=sequence_number,
                    unparsed_pdu_body=b"Doesnt matter",
                    total_pdu_length=16,
                )
            )
            self.assertTrue(mock_throttled.mock.called)
            self.assertEqual(mock_throttled.mock.call_count, 1)
            self.assertFalse(mock_not_throttled.mock.called)

    def test_response_hook_called(self):
        with mock.patch("naz.hooks.SimpleHook.response", new=AsyncMock()) as mock_hook_response:
            self._run(
                self.cli.parse_response_pdu(
                    pdu=b"\x00\x00\x00\x12\x80\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x030\x00"
                )
            )
            self.assertTrue(mock_hook_response.mock.called)
            self.assertEqual(mock_hook_response.mock.call_args[1]["smpp_event"], "submit_sm_resp")
            self.assertEqual(mock_hook_response.mock.call_args[1]["correlation_id"], None)

    def test_receving_data(self):
        with mock.patch("naz.Client.connect", new=AsyncMock()) as mock_naz_connect:
            submit_sm_resp_pdu = (
                b"\x00\x00\x00\x12\x80\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x030\x00"
            )

            # TODO: also create a MockStreamWriter
            mock_naz_connect.mock.return_value = (
                MockStreamReader(pdu=submit_sm_resp_pdu),
                "MockStreamWriter",
            )

            reader, writer = self._run(self.cli.connect())
            self.cli.reader = reader
            self.cli.writer = writer
            received_pdu = self._run(self.cli.receive_data(TESTING=True))
            self.assertEqual(received_pdu, submit_sm_resp_pdu)

    def test_enquire_link_resp(self):
        with mock.patch("naz.q.SimpleOutboundQueue.enqueue", new=AsyncMock()) as mock_naz_enqueue:
            sequence_number = 7
            self._run(
                self.cli.speficic_handlers(
                    smpp_event="enquire_link",
                    correlation_id="correlation_id",
                    command_status=0,
                    sequence_number=sequence_number,
                    unparsed_pdu_body=b"Doesnt matter",
                    total_pdu_length=16,
                )
            )
            self.assertTrue(mock_naz_enqueue.mock.called)
            self.assertEqual(
                mock_naz_enqueue.mock.call_args[0][1]["smpp_event"], "enquire_link_resp"
            )
