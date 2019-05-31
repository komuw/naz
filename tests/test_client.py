# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import os
import json
import struct
import asyncio
from unittest import TestCase, mock

import naz
import docker


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
        self.outboundqueue = naz.q.SimpleOutboundQueue(maxsize=1000)
        self.cli = naz.Client(
            smsc_host="127.0.0.1",
            smsc_port=2775,
            system_id="smppclient1",
            password=os.getenv("password", "password"),
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

    @staticmethod
    def _run(coro):
        """
        helper function that runs any coroutine in an event loop and passes its return value back to the caller.
        https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def test_bad_instantiation(self):
        def mock_create_client():
            naz.Client(
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                log_metadata="bad-Type",
                outboundqueue=self.outboundqueue,
            )

        self.assertRaises(ValueError, mock_create_client)
        with self.assertRaises(ValueError) as raised_exception:
            mock_create_client()
        self.assertIn("`log_metadata` should be of type", str(raised_exception.exception))

    def test_can_connect(self):
        reader, writer = self._run(self.cli.connect())
        self.assertTrue(hasattr(reader, "read"))
        self.assertTrue(hasattr(writer, "write"))

    def test_can_bind(self):
        with mock.patch("naz.Client.send_data", new=AsyncMock()) as mock_naz_send_data:
            self._run(self.cli.tranceiver_bind())
            self.assertTrue(mock_naz_send_data.mock.called)
            self.assertEqual(mock_naz_send_data.mock.call_count, 1)
            self.assertEqual(
                mock_naz_send_data.mock.call_args[1]["smpp_command"],
                naz.SmppCommand.BIND_TRANSCEIVER,
            )
        # todo: test bind_response

    def test_submit_sm_enqueue(self):
        with mock.patch("naz.q.SimpleOutboundQueue.enqueue", new=AsyncMock()) as mock_naz_enqueue:
            reader, writer = self._run(self.cli.connect())
            self._run(self.cli.tranceiver_bind())
            log_id = "12345"
            self._run(
                self.cli.submit_sm(
                    short_message="hello smpp",
                    log_id=log_id,
                    source_addr="9090",
                    destination_addr="254722000111",
                )
            )
            self.assertTrue(mock_naz_enqueue.mock.called)
            self.assertEqual(mock_naz_enqueue.mock.call_args[0][1]["log_id"], log_id)
            self.assertEqual(
                mock_naz_enqueue.mock.call_args[0][1]["smpp_command"], naz.SmppCommand.SUBMIT_SM
            )

    def test_submit_sm_sending(self):
        with mock.patch("naz.q.SimpleOutboundQueue.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            log_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = {
                "version": "1",
                "log_id": log_id,
                "short_message": short_message,
                "smpp_command": naz.SmppCommand.SUBMIT_SM,
                "source_addr": "2547000000",
                "destination_addr": "254711999999",
            }

            self._run(self.cli.connect())
            # hack to allow sending submit_sm even when state is wrong
            self.cli.current_session_state = "BOUND_TRX"
            self._run(self.cli.dequeue_messages(TESTING=True))

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
                mock_naz_speficic_handlers.mock.call_args[1]["smpp_command"],
                naz.SmppCommand.BIND_TRANSCEIVER_RESP,
            )

    def test_speficic_handlers(self):
        with mock.patch(
            "naz.Client.enquire_link_resp", new=AsyncMock()
        ) as mock_naz_enquire_link_resp:
            sequence_number = 3
            self._run(
                self.cli.speficic_handlers(
                    body_data=b"body_data",
                    smpp_command=naz.SmppCommand.ENQUIRE_LINK,
                    command_status_value=0,
                    sequence_number=sequence_number,
                    log_id="log_id",
                    hook_metadata="hook_metadata",
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
                    body_data=b"body_data",
                    smpp_command=naz.SmppCommand.UNBIND,
                    command_status_value=0,
                    sequence_number=sequence_number,
                    log_id="log_id",
                    hook_metadata="hook_metadata",
                )
            )
            self.assertTrue(mock_naz_send_data.mock.called)
            self.assertEqual(mock_naz_send_data.mock.call_count, 1)
            self.assertEqual(
                mock_naz_send_data.mock.call_args[1]["smpp_command"], naz.SmppCommand.UNBIND_RESP
            )

    def test_speficic_handlers_deliver_sm(self):
        with mock.patch("naz.q.SimpleOutboundQueue.enqueue", new=AsyncMock()) as mock_naz_enqueue:
            sequence_number = 7
            self._run(
                self.cli.speficic_handlers(
                    body_data=b"body_data",
                    smpp_command=naz.SmppCommand.DELIVER_SM,
                    command_status_value=0,
                    sequence_number=sequence_number,
                    log_id="log_id",
                    hook_metadata="hook_metadata",
                )
            )
            self.assertTrue(mock_naz_enqueue.mock.called)
            self.assertEqual(
                mock_naz_enqueue.mock.call_args[0][1]["smpp_command"],
                naz.SmppCommand.DELIVER_SM_RESP,
            )

    def test_unbind(self):
        with mock.patch("naz.Client.send_data", new=AsyncMock()) as mock_naz_send_data:
            self._run(self.cli.unbind())
            self.assertTrue(mock_naz_send_data.mock.called)
            self.assertEqual(mock_naz_send_data.mock.call_count, 1)
            self.assertEqual(
                mock_naz_send_data.mock.call_args[1]["smpp_command"], naz.SmppCommand.UNBIND
            )

    def test_enquire_link(self):
        with mock.patch("naz.Client.send_data", new=AsyncMock()) as mock_naz_send_data:
            self._run(self.cli.enquire_link(TESTING=True))
            self.assertTrue(mock_naz_send_data.mock.called)
            self.assertEqual(mock_naz_send_data.mock.call_count, 1)
            self.assertEqual(
                mock_naz_send_data.mock.call_args[1]["smpp_command"], naz.SmppCommand.ENQUIRE_LINK
            )

    def test_no_sending_if_throttler(self):
        with mock.patch("naz.q.SimpleOutboundQueue.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            sample_size = 8.0
            throttle_handler = naz.throttle.SimpleThrottleHandler(
                sampling_period=5.0, sample_size=sample_size, deny_request_at=0.4
            )
            cli = naz.Client(
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                outboundqueue=self.outboundqueue,
                throttle_handler=throttle_handler,
            )

            log_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = {
                "version": "1",
                "log_id": log_id,
                "short_message": short_message,
                "smpp_command": naz.SmppCommand.SUBMIT_SM,
                "source_addr": "2547000000",
                "destination_addr": "254711999999",
            }
            self._run(cli.connect())
            # mock SMSC throttling naz
            for _ in range(0, int(sample_size) * 2):
                self._run(cli.throttle_handler.throttled())

            self._run(cli.dequeue_messages(TESTING=True))

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
                    body_data=b"body_data",
                    smpp_command=naz.SmppCommand.DELIVER_SM,
                    command_status_value=0,
                    sequence_number=sequence_number,
                    log_id="log_id",
                    hook_metadata="hook_metadata",
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
                    body_data=b"body_data",
                    smpp_command=naz.SmppCommand.DELIVER_SM,
                    command_status_value=0x00000058,
                    sequence_number=sequence_number,
                    log_id="log_id",
                    hook_metadata="hook_metadata",
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
            self.assertEqual(
                mock_hook_response.mock.call_args[1]["smpp_command"], naz.SmppCommand.SUBMIT_SM_RESP
            )
            self.assertEqual(mock_hook_response.mock.call_args[1]["log_id"], "")

    def test_hook_called_with_metadata(self):
        with mock.patch(
            "naz.hooks.SimpleHook.request", new=AsyncMock()
        ) as mock_hook_request, mock.patch(
            "naz.q.SimpleOutboundQueue.dequeue", new=AsyncMock()
        ) as mock_naz_dequeue:
            log_id = "12345"
            short_message = "hello smpp"
            _hook_metadata = {"telco": "Verizon", "customer_id": "909090123"}
            hook_metadata = json.dumps(_hook_metadata)
            mock_naz_dequeue.mock.return_value = {
                "version": "1",
                "log_id": log_id,
                "short_message": short_message,
                "smpp_command": naz.SmppCommand.SUBMIT_SM,
                "source_addr": "2547000000",
                "destination_addr": "254711999999",
                "hook_metadata": hook_metadata,
            }

            self._run(self.cli.connect())
            # hack to allow sending submit_sm even when state is wrong
            self.cli.current_session_state = "BOUND_TRX"
            self._run(self.cli.dequeue_messages(TESTING=True))

            self.assertTrue(mock_hook_request.mock.called)
            self.assertEqual(
                mock_hook_request.mock.call_args[1]["smpp_command"], naz.SmppCommand.SUBMIT_SM
            )
            self.assertEqual(mock_hook_request.mock.call_args[1]["log_id"], log_id)
            self.assertEqual(mock_hook_request.mock.call_args[1]["hook_metadata"], hook_metadata)
            self.assertEqual(
                json.loads(mock_hook_request.mock.call_args[1]["hook_metadata"]), _hook_metadata
            )

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
                    body_data=b"body_data",
                    smpp_command=naz.SmppCommand.ENQUIRE_LINK,
                    command_status_value=0,
                    sequence_number=sequence_number,
                    log_id="log_id",
                    hook_metadata="hook_metadata",
                )
            )
            self.assertTrue(mock_naz_enqueue.mock.called)
            self.assertEqual(
                mock_naz_enqueue.mock.call_args[0][1]["smpp_command"],
                naz.SmppCommand.ENQUIRE_LINK_RESP,
            )

    def test__retry_after(self):
        self.assertEqual(self.cli._retry_after(current_retries=-23) / 60, 1)
        self.assertEqual(self.cli._retry_after(current_retries=0) / 60, 1)
        self.assertEqual(self.cli._retry_after(current_retries=1) / 60, 2)
        self.assertEqual(self.cli._retry_after(current_retries=2) / 60, 4)
        self.assertEqual(self.cli._retry_after(current_retries=3) / 60, 8)
        self.assertEqual(self.cli._retry_after(current_retries=4) / 60, 16)
        self.assertEqual(self.cli._retry_after(current_retries=5) / 60, 32)
        self.assertEqual(self.cli._retry_after(current_retries=7) / 60, 16)
        self.assertEqual(self.cli._retry_after(current_retries=5432) / 60, 16)

    def test_session_state(self):
        """
        try sending a `submit_sm` request when session state is `OPEN`
        """
        with mock.patch("naz.q.SimpleOutboundQueue.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            log_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = {
                "version": "1",
                "log_id": log_id,
                "short_message": short_message,
                "smpp_command": naz.SmppCommand.SUBMIT_SM,
                "source_addr": "2547000000",
                "destination_addr": "254711999999",
            }

            self._run(self.cli.connect())
            with self.assertRaises(ValueError) as raised_exception:
                self._run(self.cli.dequeue_messages(TESTING=True))
            self.assertIn(
                "smpp_command: submit_sm cannot be sent to SMSC when the client session state is: OPEN",
                str(raised_exception.exception),
            )

    def test_submit_with_session_state_closed(self):
        """
        try sending a `submit_sm` request when session state is `CLOSED`
        """
        with mock.patch("naz.q.SimpleOutboundQueue.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            log_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = {
                "version": "1",
                "log_id": log_id,
                "short_message": short_message,
                "smpp_command": naz.SmppCommand.SUBMIT_SM,
                "source_addr": "2547000000",
                "destination_addr": "254711999999",
            }
            with self.assertRaises(ValueError) as raised_exception:
                self._run(self.cli.dequeue_messages(TESTING=True))
            self.assertIn(
                "smpp_command: submit_sm cannot be sent to SMSC when the client session state is: CLOSED",
                str(raised_exception.exception),
            )

    def test_correlater_put_called(self):
        with mock.patch(
            "naz.correlater.SimpleCorrelater.put", new=AsyncMock()
        ) as mock_correlater_put, mock.patch(
            "naz.q.SimpleOutboundQueue.dequeue", new=AsyncMock()
        ) as mock_naz_dequeue:
            log_id = "12345"
            short_message = "hello smpp"
            _hook_metadata = {"telco": "Verizon", "customer_id": "909090123"}
            hook_metadata = json.dumps(_hook_metadata)
            mock_naz_dequeue.mock.return_value = {
                "version": "1",
                "log_id": log_id,
                "short_message": short_message,
                "smpp_command": naz.SmppCommand.SUBMIT_SM,
                "source_addr": "2547000000",
                "destination_addr": "254711999999",
                "hook_metadata": hook_metadata,
            }

            self._run(self.cli.connect())
            # hack to allow sending submit_sm even when state is wrong
            self.cli.current_session_state = "BOUND_TRX"
            self._run(self.cli.dequeue_messages(TESTING=True))
            self.assertTrue(mock_correlater_put.mock.called)

            self.assertEqual(mock_correlater_put.mock.call_args[1]["log_id"], log_id)
            self.assertEqual(mock_correlater_put.mock.call_args[1]["hook_metadata"], hook_metadata)
            self.assertEqual(
                json.loads(mock_correlater_put.mock.call_args[1]["hook_metadata"]), _hook_metadata
            )

    def test_correlater_get_called(self):
        with mock.patch(
            "naz.correlater.SimpleCorrelater.get", new=AsyncMock()
        ) as mock_correlater_get:
            mock_correlater_get.return_value = "log_id", "hook_metadata"
            self._run(
                self.cli.parse_response_pdu(
                    pdu=b"\x00\x00\x00\x18\x80\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x06SMPPSim\x00"
                )
            )
            self.assertTrue(mock_correlater_get.mock.called)
            self.assertTrue(mock_correlater_get.mock.call_args[1]["sequence_number"])

    def test_instantiate_bad_encoding(self):
        encoding = "unknownEncoding"

        def mock_create_client():
            naz.Client(
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                encoding=encoding,
                outboundqueue=self.outboundqueue,
            )

        self.assertRaises(ValueError, mock_create_client)
        with self.assertRaises(ValueError) as raised_exception:
            mock_create_client()
        self.assertIn(
            "That encoding:{0} is not recognised.".format(encoding), str(raised_exception.exception)
        )

    def test_logger_called(self):
        with mock.patch("naz.logger.SimpleLogger.log") as mock_logger_log:
            mock_logger_log.return_value = None
            self._run(
                self.cli.parse_response_pdu(
                    pdu=b"\x00\x00\x00\x18\x80\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x06SMPPSim\x00"
                )
            )
            self.assertTrue(mock_logger_log.called)
            self.assertEqual(
                mock_logger_log.call_args[0][1]["event"], "naz.Client.parse_response_pdu"
            )

    def test_parse_deliver_sm(self):
        with mock.patch(
            "naz.Client.speficic_handlers", new=AsyncMock()
        ) as mock_naz_speficic_handlers:
            # see: https://github.com/mozes/smpp.pdu
            deliver_sm_pdu = (
                b"\x00\x00\x00M\x00\x00\x00\x05\x00\x00"
                b"\x00\x00\x9f\x88\xf1$AWSBD\x00\x01"
                b"\x0116505551234\x00\x01\x0117735554070"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00"
                b"\x11id:123456 sub:SSS dlvrd:DDD blah blah"
            )
            self._run(self.cli.parse_response_pdu(pdu=deliver_sm_pdu))

            self.assertTrue(mock_naz_speficic_handlers.mock.called)
            self.assertEqual(mock_naz_speficic_handlers.mock.call_count, 1)
            self.assertEqual(
                mock_naz_speficic_handlers.mock.call_args[1]["smpp_command"],
                naz.SmppCommand.DELIVER_SM,
            )

    def test_submit_sm_AND_deliver_sm_correlation(self):
        with mock.patch(
            "naz.sequence.SimpleSequenceGenerator.next_sequence"
        ) as mock_sequence, mock.patch(
            "naz.q.SimpleOutboundQueue.dequeue", new=AsyncMock()
        ) as mock_naz_dequeue:
            mock_sequence_number = 909_012
            mock_sequence.return_value = mock_sequence_number

            log_id = "MyLog_id123456"
            short_message = "hello smpp"
            _hook_metadata = {"telco": "Verizon", "customer_id": "909090123"}
            hook_metadata = json.dumps(_hook_metadata)
            mock_naz_dequeue.mock.return_value = {
                "version": "1",
                "log_id": log_id,
                "short_message": short_message,
                "smpp_command": naz.SmppCommand.SUBMIT_SM,
                "source_addr": "2547000000",
                "destination_addr": "254711999999",
                "hook_metadata": hook_metadata,
            }

            # 1. SEND SUBMIT_SM
            self._run(self.cli.connect())
            # hack to allow sending submit_sm even when state is wrong
            self.cli.current_session_state = "BOUND_TRX"
            self._run(self.cli.dequeue_messages(TESTING=True))
            self.assertTrue(self.cli.correlation_handler.store[mock_sequence_number])
            self.assertEqual(
                self.cli.correlation_handler.store[mock_sequence_number]["log_id"], log_id
            )
            self.assertEqual(
                self.cli.correlation_handler.store[mock_sequence_number]["hook_metadata"],
                hook_metadata,
            )

            # 2. RECEIVE SUBMIT_SM_RESP
            submit_sm_resp_smsc_message_id = "1618Z-0102G-2333M-25FJF"
            body = b""
            body = body + submit_sm_resp_smsc_message_id.encode() + chr(0).encode()
            command_length = 16 + len(body)  # 16 is for headers
            command_id = 0x80000004  # submit_sm_resp
            command_status = 0x00000000  # success
            header = struct.pack(
                ">IIII", command_length, command_id, command_status, mock_sequence_number
            )  # SUBMIT_SM_RESP should have same sequence_number as SUBMIT_SM
            submit_sm_resp_full_pdu = header + body
            self._run(self.cli.parse_response_pdu(pdu=submit_sm_resp_full_pdu))

            # assert message_id  was stored
            self.assertTrue(self.cli.correlation_handler.store[submit_sm_resp_smsc_message_id])
            self.assertEqual(
                self.cli.correlation_handler.store[submit_sm_resp_smsc_message_id]["log_id"], log_id
            )
            self.assertEqual(
                self.cli.correlation_handler.store[submit_sm_resp_smsc_message_id]["hook_metadata"],
                hook_metadata,
            )

            # 3. RECEIVE DELIVER_SM
            with mock.patch("naz.hooks.SimpleHook.response", new=AsyncMock()) as mock_hook_response:
                tag = naz.SmppOptionalTag.receipted_message_id
                length = 0x0018  # 24 in length
                tag_n_len = struct.pack(">HH", tag, length)
                # DELIVER_SM has same message_id as SUBMIT_SM_RESP but DIFFERENT sequence_number
                value = submit_sm_resp_smsc_message_id  # 23 in length
                value = value.encode() + chr(0).encode()  # 24 in length
                deliver_sm_pdu = (
                    b"\x00\x00\x00M\x00\x00\x00\x05\x00\x00\x00"
                    b"\x00\x9f\x88\xf1$AWSBD\x00\x01\x0116505551234"
                    b"\x00\x01\x0117735554070\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x03\x00\x11id:1618Z-0102G-2333M-25FJF sub:SSS dlvrd:DDD blah blah"
                )
                deliver_sm_pdu = deliver_sm_pdu + tag_n_len + value
                self._run(self.cli.parse_response_pdu(pdu=deliver_sm_pdu))

                self.assertTrue(mock_hook_response.mock.called)
                self.assertEqual(
                    mock_hook_response.mock.call_args[1]["smpp_command"], naz.SmppCommand.DELIVER_SM
                )
                self.assertEqual(mock_hook_response.mock.call_args[1]["log_id"], log_id)
                self.assertEqual(
                    mock_hook_response.mock.call_args[1]["hook_metadata"], hook_metadata
                )
