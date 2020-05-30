# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import os
import json
import codecs
import struct
import asyncio
from unittest import TestCase, mock, skip

import naz
import docker


from .utils import AsyncMock, MockStreamWriter, MockStreamReader


class TestClient(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v tests.test_client.TestClient.test_can_connect
    """

    def setUp(self):
        self.broker = naz.broker.SimpleBroker(maxsize=1000)

        smsc_port = 2775
        self.socket_timeout = 0.01
        self.cli = naz.Client(
            smsc_host="127.0.0.1",
            smsc_port=smsc_port,
            system_id="smppclient1",
            password=os.getenv("password", "password"),
            broker=self.broker,
            logger=naz.log.SimpleLogger(
                "TestClient", level="INFO", handler=naz.log.BreachHandler(capacity=100)
            ),  # run tests with debug so as to debug what is going on
            socket_timeout=self.socket_timeout,
        )

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
            ports={"{0}/tcp".format(smsc_port): smsc_port, "8884/tcp": 8884},
            stdout=True,
            stderr=True,
        )

    def tearDown(self):
        if os.environ.get("CI_ENVIRONMENT"):
            self.smpp_server.remove(force=True)
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
                broker="bad-Type",
            )

        self.assertRaises(naz.client.NazClientError, mock_create_client)
        with self.assertRaises(naz.client.NazClientError) as raised_exception:
            mock_create_client()
        self.assertIsInstance(raised_exception.exception.args[0][0], ValueError)
        self.assertIn("`broker` should be of type", str(raised_exception.exception.args[0][0]))

    def test_all_bad_args(self):
        class DummyClientArg:
            pass

        client_args = {
            "smsc_host": DummyClientArg,
            "smsc_port": DummyClientArg,
            "system_id": DummyClientArg,
            "password": DummyClientArg,
            "broker": DummyClientArg,
            "system_type": DummyClientArg,
            "interface_version": DummyClientArg,
            "addr_ton": DummyClientArg,
            "addr_npi": DummyClientArg,
            "address_range": DummyClientArg,
            "sequence_generator": DummyClientArg,
            "custom_codecs": DummyClientArg,
            "enquire_link_interval": DummyClientArg,
            "rate_limiter": DummyClientArg,
            "hook": DummyClientArg,
            "throttle_handler": DummyClientArg,
            "correlation_handler": DummyClientArg,
            "drain_duration": DummyClientArg,
            "socket_timeout": DummyClientArg,
        }

        def mock_create_client():
            naz.Client(**client_args)

        self.assertRaises(naz.client.NazClientError, mock_create_client)
        with self.assertRaises(naz.client.NazClientError) as raised_exception:
            mock_create_client()
        for exc in raised_exception.exception.args[0]:
            self.assertIsInstance(exc, ValueError)

    def test_instantiate_custom_codecs(self):
        def mock_create_client():
            naz.Client(
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                broker=self.broker,
                custom_codecs={"encoding": {"someKey": "someValue"}},
            )

        self.assertRaises(naz.client.NazClientError, mock_create_client)
        with self.assertRaises(naz.client.NazClientError) as raised_exception:
            mock_create_client()

        self.assertIn(
            "`custom_codecs` should be a dictionary of encoding(string) to `codecs.CodecInfo`",
            str(raised_exception.exception),
        )

    def test_instantiate_bad_encoding(self):
        encoding = "unknownSmppEncoding"

        def mock_create_client():
            naz.Client(
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                broker=self.broker,
                custom_codecs={
                    encoding: codecs.CodecInfo(
                        name=encoding,
                        encode=naz.codec.UCS2Codec.encode,
                        decode=naz.codec.UCS2Codec.decode,
                    ),
                },
            )

        self.assertRaises(naz.client.NazClientError, mock_create_client)
        with self.assertRaises(naz.client.NazClientError) as raised_exception:
            mock_create_client()
        self.assertIn(
            "That encoding: `{0}` is not a recognised SMPP encoding".format(encoding),
            str(raised_exception.exception),
        )

    def test_custom_encodings(self):
        """
        tests that any of the encodings allowed by SMPP spec[1] can be used.
        1. https://github.com/komuw/naz/blob/c47f5030b720f3bac400dd6bd457b4415b0d5b7b/naz/state.py#L328
        2. Also see section 5.2.19 of SMPP spec
        """

        class ExampleCodec(codecs.Codec):
            # All the methods have to be staticmethods because they are passed to `codecs.CodecInfo`
            @staticmethod
            def encode(input, errors="strict"):
                return codecs.utf_8_encode(input, errors)

            @staticmethod
            def decode(input, errors="strict"):
                return codecs.utf_8_decode(input, errors)

        for encoding in ["gsm0338", "ucs2", "ascii", "latin_1", "iso2022jp", "iso8859_5"]:
            naz.Client(
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                broker=self.broker,
                logger=naz.log.SimpleLogger(
                    "TestClient", level="DEBUG", handler=naz.log.BreachHandler(capacity=200)
                ),
                socket_timeout=self.socket_timeout,
                custom_codecs={
                    encoding: codecs.CodecInfo(
                        name=encoding, encode=ExampleCodec.encode, decode=ExampleCodec.decode,
                    ),
                },
            )

    def test_can_connect(self):
        self._run(self.cli.connect())
        self.assertTrue(hasattr(self.cli.reader, "read"))
        self.assertTrue(hasattr(self.cli.writer, "write"))

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

    def test_send_message_error(self):
        with self.assertRaises(ValueError):
            self._run(self.cli.send_message("bogusType"))

    def test_send_message_success(self):
        log_id = "12345"
        short_message = "hello"
        msg = naz.protocol.SubmitSM(
            short_message=short_message,
            source_addr="2492",
            destination_addr="8930302",
            log_id=log_id,
        )
        with mock.patch("naz.broker.SimpleBroker.enqueue", new=AsyncMock()) as mock_naz_enqueue:
            self._run(self.cli.connect())
            self._run(self.cli.tranceiver_bind())

            self._run(self.cli.send_message(msg))
            self.assertTrue(mock_naz_enqueue.mock.called)
            self.assertEqual(mock_naz_enqueue.mock.call_args[0][1].log_id, log_id)
            self.assertEqual(
                mock_naz_enqueue.mock.call_args[0][1].smpp_command, naz.SmppCommand.SUBMIT_SM
            )
            self.assertEqual(mock_naz_enqueue.mock.call_args[0][1].short_message, short_message)

    def test_submit_sm_sending(self):
        with mock.patch("naz.broker.SimpleBroker.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            log_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = naz.protocol.SubmitSM(
                version=1,
                log_id=log_id,
                short_message=short_message,
                smpp_command=naz.SmppCommand.SUBMIT_SM,
                source_addr="2547000000",
                destination_addr="254711999999",
            )

            self._run(self.cli.connect())
            # hack to allow sending submit_sm even when state is wrong
            self.cli.current_session_state = "BOUND_TRX"
            self._run(self.cli.dequeue_messages(TESTING=True))
            self.assertTrue(mock_naz_dequeue.mock.called)

    def test_parse_response_pdu(self):
        with mock.patch(
            "naz.Client.command_handlers", new=AsyncMock()
        ) as mock_naz_command_handlers:
            self._run(
                self.cli._parse_response_pdu(
                    pdu=b"\x00\x00\x00\x18\x80\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x06SMPPSim\x00"
                )
            )

            self.assertTrue(mock_naz_command_handlers.mock.called)
            self.assertEqual(mock_naz_command_handlers.mock.call_count, 1)
            self.assertEqual(
                mock_naz_command_handlers.mock.call_args[1]["smpp_command"],
                naz.SmppCommand.BIND_TRANSCEIVER_RESP,
            )

    def test_command_handlers(self):
        with mock.patch(
            "naz.Client.enquire_link_resp", new=AsyncMock()
        ) as mock_naz_enquire_link_resp:
            sequence_number = 3
            self._run(
                self.cli.command_handlers(
                    pdu=b"pdu",
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

    def test_command_handlers_unbind(self):
        with mock.patch("naz.Client.send_data", new=AsyncMock()) as mock_naz_send_data:
            sequence_number = 7
            self._run(
                self.cli.command_handlers(
                    pdu=b"pdu",
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

    def test_command_handlers_deliver_sm(self):
        with mock.patch("naz.broker.SimpleBroker.enqueue", new=AsyncMock()) as mock_naz_enqueue:
            sequence_number = 7
            self._run(
                self.cli.command_handlers(
                    pdu=b"pdu",
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
                mock_naz_enqueue.mock.call_args[0][1].smpp_command, naz.SmppCommand.DELIVER_SM_RESP
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
            self.cli.current_session_state = naz.SmppSessionState.BOUND_TRX
            self._run(self.cli.enquire_link(TESTING=True))
            self.assertTrue(mock_naz_send_data.mock.called)
            self.assertEqual(mock_naz_send_data.mock.call_count, 1)
            self.assertEqual(
                mock_naz_send_data.mock.call_args[1]["smpp_command"], naz.SmppCommand.ENQUIRE_LINK
            )

    def test_no_sending_if_throttler(self):
        with mock.patch("naz.broker.SimpleBroker.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            sample_size = 8.0
            throttle_handler = naz.throttle.SimpleThrottleHandler(
                sampling_period=5.0, sample_size=sample_size, deny_request_at=0.4
            )
            cli = naz.Client(
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                broker=self.broker,
                throttle_handler=throttle_handler,
                logger=naz.log.SimpleLogger("naz.test_no_sending_if_throttler", level="DEBUG"),
            )

            log_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = naz.protocol.SubmitSM(
                version=1,
                log_id=log_id,
                short_message=short_message,
                smpp_command=naz.SmppCommand.SUBMIT_SM,
                source_addr="2547000000",
                destination_addr="254711999999",
            )
            self._run(cli.connect())
            cli.current_session_state = naz.SmppSessionState.BOUND_TRX
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
                self.cli.command_handlers(
                    pdu=b"pdu",
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
                self.cli.command_handlers(
                    pdu=b"pdu",
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
        with mock.patch("naz.hooks.SimpleHook.from_smsc", new=AsyncMock()) as mock_hook_from_smsc:
            self._run(
                self.cli._parse_response_pdu(
                    pdu=b"\x00\x00\x00\x12\x80\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x030\x00"
                )
            )
            self.assertTrue(mock_hook_from_smsc.mock.called)
            self.assertEqual(
                mock_hook_from_smsc.mock.call_args[1]["smpp_command"],
                naz.SmppCommand.SUBMIT_SM_RESP,
            )
            self.assertEqual(mock_hook_from_smsc.mock.call_args[1]["log_id"], "")

    def test_hook_called_with_metadata(self):
        with mock.patch(
            "naz.hooks.SimpleHook.to_smsc", new=AsyncMock()
        ) as mock_hook_to_smsc, mock.patch(
            "naz.broker.SimpleBroker.dequeue", new=AsyncMock()
        ) as mock_naz_dequeue:
            log_id = "12345"
            short_message = "hello smpp"
            _hook_metadata = {"telco": "Verizon", "customer_id": "909090123"}
            hook_metadata = json.dumps(_hook_metadata)
            mock_naz_dequeue.mock.return_value = naz.protocol.SubmitSM(
                version=1,
                log_id=log_id,
                short_message=short_message,
                smpp_command=naz.SmppCommand.SUBMIT_SM,
                source_addr="2547000000",
                destination_addr="254711999999",
                hook_metadata=hook_metadata,
            )

            self._run(self.cli.connect())
            # hack to allow sending submit_sm even when state is wrong
            self.cli.current_session_state = naz.SmppSessionState.BOUND_TRX
            self._run(self.cli.dequeue_messages(TESTING=True))

            self.assertTrue(mock_hook_to_smsc.mock.called)
            self.assertEqual(
                mock_hook_to_smsc.mock.call_args[1]["smpp_command"], naz.SmppCommand.SUBMIT_SM
            )
            self.assertEqual(mock_hook_to_smsc.mock.call_args[1]["log_id"], log_id)
            self.assertEqual(mock_hook_to_smsc.mock.call_args[1]["hook_metadata"], hook_metadata)
            self.assertEqual(
                json.loads(mock_hook_to_smsc.mock.call_args[1]["hook_metadata"]), _hook_metadata
            )

    def test_receving_data(self):
        with mock.patch("asyncio.open_connection", new=AsyncMock()) as mock_naz_connect:
            # TODO: this sample PDU's should be in one place
            submit_sm_resp_pdu = (
                b"\x00\x00\x00\x12\x80\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x030\x00"
            )
            mock_naz_connect.mock.return_value = (
                MockStreamReader(pdu=submit_sm_resp_pdu),
                MockStreamWriter(),
            )

            self._run(self.cli.connect())
            received_pdu = self._run(self.cli.receive_data(TESTING=True))
            self.assertEqual(received_pdu, submit_sm_resp_pdu)

    def test_partial_reads_disconnect(self):
        """
        test that if we are unable to read the full 16byte smpp header,
        then we should close the connection.
        """
        with mock.patch("asyncio.open_connection", new=AsyncMock()) as mock_naz_connect, mock.patch(
            "naz.Client._unbind_and_disconnect", new=AsyncMock()
        ) as mock_naz_unbind_and_disconnect:
            submit_sm_resp_pdu = b"\x00\x00\x00"
            mock_naz_connect.mock.return_value = (
                MockStreamReader(pdu=submit_sm_resp_pdu),
                MockStreamWriter(),
            )

            self._run(self.cli.connect())
            received_pdu = self._run(self.cli.receive_data(TESTING=True))
            self.assertEqual(received_pdu, b"")
            self.assertTrue(mock_naz_unbind_and_disconnect.mock.called)

    def test_enquire_link_resp(self):
        with mock.patch("naz.broker.SimpleBroker.enqueue", new=AsyncMock()) as mock_naz_enqueue:
            sequence_number = 7
            self._run(
                self.cli.command_handlers(
                    pdu=b"pdu",
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
                mock_naz_enqueue.mock.call_args[0][1].smpp_command,
                naz.SmppCommand.ENQUIRE_LINK_RESP,
            )

    def test_retry_after(self):
        self.assertEqual(self.cli._retry_after(current_retries=-23) / 60, 1)
        self.assertEqual(self.cli._retry_after(current_retries=0) / 60, 1)
        self.assertEqual(self.cli._retry_after(current_retries=1) / 60, 2)
        self.assertEqual(self.cli._retry_after(current_retries=2) / 60, 4)
        self.assertEqual(self.cli._retry_after(current_retries=3) / 60, 8)
        self.assertEqual(self.cli._retry_after(current_retries=4) / 60, 16)
        self.assertEqual(self.cli._retry_after(current_retries=5) / 60, 32)
        self.assertEqual(self.cli._retry_after(current_retries=7) / 60, 16)
        self.assertEqual(self.cli._retry_after(current_retries=5432) / 60, 16)

    def test_session_state_ok(self):
        """
        send a `submit_sm` request when session state is `BOUND_TRX`
        """
        with mock.patch(
            "naz.broker.SimpleBroker.dequeue", new=AsyncMock()
        ) as mock_naz_dequeue, mock.patch("asyncio.streams.StreamWriter.write") as mock_naz_writer:
            log_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = naz.protocol.SubmitSM(
                version=1,
                log_id=log_id,
                short_message=short_message,
                smpp_command=naz.SmppCommand.SUBMIT_SM,
                source_addr="2547000000",
                destination_addr="254711999999",
            )

            self._run(self.cli.connect())
            self._run(self.cli.tranceiver_bind())
            self.cli.current_session_state = naz.SmppSessionState.BOUND_TRX
            self._run(self.cli.dequeue_messages(TESTING=True))

            self.assertTrue(mock_naz_writer.called)
            self.assertEqual(mock_naz_writer.call_count, 2)
            self.assertIn(short_message, mock_naz_writer.call_args[0][0].decode())

    def test_broken_broker(self):
        with mock.patch(
            "naz.broker.SimpleBroker.dequeue", new=AsyncMock()
        ) as mock_naz_dequeue, mock.patch("asyncio.streams.StreamWriter.write") as mock_naz_writer:
            mock_naz_dequeue.mock.side_effect = ValueError("This test broker has 99 Problems")
            self._run(self.cli.connect())
            self.cli.current_session_state = naz.SmppSessionState.BOUND_TRX
            res = self._run(self.cli.dequeue_messages(TESTING=True))
            self.assertEqual(res, {"broker_error": "broker_error"})
            self.assertFalse(mock_naz_writer.called)

    def test_session_state(self):
        """
        try sending a `submit_sm` request when session state is `OPEN`
        """
        with mock.patch(
            "naz.broker.SimpleBroker.dequeue", new=AsyncMock()
        ) as mock_naz_dequeue, mock.patch("asyncio.streams.StreamWriter.write") as mock_naz_writer:
            log_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = naz.protocol.SubmitSM(
                version=1,
                log_id=log_id,
                short_message=short_message,
                smpp_command=naz.SmppCommand.SUBMIT_SM,
                source_addr="2547000000",
                destination_addr="254711999999",
            )

            self._run(self.cli.connect())
            self.cli.current_session_state = naz.SmppSessionState.OPEN
            self._run(self.cli.dequeue_messages(TESTING=True))
            self.assertFalse(mock_naz_writer.called)

    def test_submit_with_session_state_closed(self):
        """
        try sending a `submit_sm` request when session state is `CLOSED`
        """
        with mock.patch(
            "naz.broker.SimpleBroker.dequeue", new=AsyncMock()
        ) as mock_naz_dequeue, mock.patch(
            "naz.client.asyncio.sleep", new=AsyncMock()
        ) as mock_sleep:
            log_id = "12345"
            short_message = "hello smpp"
            mock_naz_dequeue.mock.return_value = naz.protocol.SubmitSM(
                version=1,
                log_id=log_id,
                short_message=short_message,
                smpp_command=naz.SmppCommand.SUBMIT_SM,
                source_addr="2547000000",
                destination_addr="254711999999",
            )
            self._run(self.cli.dequeue_messages(TESTING=True))
            self.assertTrue(mock_sleep.mock.called)
            self.assertEqual(mock_sleep.mock.call_args[0][0], self.cli.socket_timeout)

    def test_correlater_put_called(self):
        with mock.patch(
            "naz.correlater.SimpleCorrelater.put", new=AsyncMock()
        ) as mock_correlater_put, mock.patch(
            "naz.broker.SimpleBroker.dequeue", new=AsyncMock()
        ) as mock_naz_dequeue:
            log_id = "12345"
            short_message = "hello smpp"
            _hook_metadata = {"telco": "Verizon", "customer_id": "909090123"}
            hook_metadata = json.dumps(_hook_metadata)
            mock_naz_dequeue.mock.return_value = naz.protocol.SubmitSM(
                version=1,
                log_id=log_id,
                short_message=short_message,
                smpp_command=naz.SmppCommand.SUBMIT_SM,
                source_addr="2547000000",
                destination_addr="254711999999",
                hook_metadata=hook_metadata,
            )

            self._run(self.cli.connect())
            # hack to allow sending submit_sm even when state is wrong
            self.cli.current_session_state = naz.SmppSessionState.BOUND_TRX
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
            mock_correlater_get.mock.return_value = "log_id", "hook_metadata"
            self._run(
                self.cli._parse_response_pdu(
                    pdu=b"\x00\x00\x00\x18\x80\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x06SMPPSim\x00"
                )
            )
            self.assertTrue(mock_correlater_get.mock.called)
            self.assertTrue(mock_correlater_get.mock.call_args[1]["sequence_number"])

    def test_logger_called(self):
        with mock.patch("naz.log.SimpleLogger.log") as mock_logger_log:
            mock_logger_log.return_value = None
            self._run(
                self.cli._parse_response_pdu(
                    pdu=b"\x00\x00\x00\x18\x80\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x06SMPPSim\x00"
                )
            )
            self.assertTrue(mock_logger_log.called)
            self.assertEqual(
                mock_logger_log.call_args[0][1]["event"], "naz.Client._parse_response_pdu"
            )

    def test_parse_deliver_sm(self):
        with mock.patch(
            "naz.Client.command_handlers", new=AsyncMock()
        ) as mock_naz_command_handlers:
            # see: https://github.com/mozes/smpp.pdu
            deliver_sm_pdu = (
                b"\x00\x00\x00M\x00\x00\x00\x05\x00\x00"
                b"\x00\x00\x9f\x88\xf1$AWSBD\x00\x01"
                b"\x0116505551234\x00\x01\x0117735554070"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00"
                b"\x11id:123456 sub:SSS dlvrd:DDD blah blah"
            )
            self._run(self.cli._parse_response_pdu(pdu=deliver_sm_pdu))

            self.assertTrue(mock_naz_command_handlers.mock.called)
            self.assertEqual(mock_naz_command_handlers.mock.call_count, 1)
            self.assertEqual(
                mock_naz_command_handlers.mock.call_args[1]["smpp_command"],
                naz.SmppCommand.DELIVER_SM,
            )

    def test_submit_sm_AND_deliver_sm_correlation(self):
        with mock.patch(
            "naz.sequence.SimpleSequenceGenerator.next_sequence"
        ) as mock_sequence, mock.patch(
            "naz.broker.SimpleBroker.dequeue", new=AsyncMock()
        ) as mock_naz_dequeue:
            mock_sequence_number = 909_012
            mock_sequence.return_value = mock_sequence_number

            log_id = "MyLog_id123456"
            short_message = "hello smpp"
            _hook_metadata = {"telco": "Verizon", "customer_id": "909090123"}
            hook_metadata = json.dumps(_hook_metadata)
            mock_naz_dequeue.mock.return_value = naz.protocol.SubmitSM(
                version=1,
                log_id=log_id,
                short_message=short_message,
                smpp_command=naz.SmppCommand.SUBMIT_SM,
                source_addr="2547000000",
                destination_addr="254711999999",
                hook_metadata=hook_metadata,
            )

            # 1. SEND SUBMIT_SM
            self._run(self.cli.connect())
            # hack to allow sending submit_sm even when state is wrong
            self.cli.current_session_state = naz.SmppSessionState.BOUND_TRX
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
            body = body + submit_sm_resp_smsc_message_id.encode("ascii") + chr(0).encode("ascii")
            command_length = 16 + len(body)  # 16 is for headers
            command_id = 0x80000004  # submit_sm_resp
            command_status = 0x00000000  # success
            header = struct.pack(
                ">IIII", command_length, command_id, command_status, mock_sequence_number
            )  # SUBMIT_SM_RESP should have same sequence_number as SUBMIT_SM
            submit_sm_resp_full_pdu = header + body
            self._run(self.cli._parse_response_pdu(pdu=submit_sm_resp_full_pdu))

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
            with mock.patch(
                "naz.hooks.SimpleHook.from_smsc", new=AsyncMock()
            ) as mock_hook_from_smsc:
                tag = naz.SmppOptionalTag.receipted_message_id
                length = 0x0018  # 24 in length
                tag_n_len = struct.pack(">HH", tag, length)
                # DELIVER_SM has same message_id as SUBMIT_SM_RESP but DIFFERENT sequence_number
                value = submit_sm_resp_smsc_message_id  # 23 in length
                value = value.encode("ascii") + chr(0).encode("ascii")  # 24 in length
                deliver_sm_pdu = (
                    b"\x00\x00\x00M\x00\x00\x00\x05\x00\x00\x00"
                    b"\x00\x9f\x88\xf1$AWSBD\x00\x01\x0116505551234"
                    b"\x00\x01\x0117735554070\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x03\x00\x11id:1618Z-0102G-2333M-25FJF sub:SSS dlvrd:DDD blah blah"
                )
                deliver_sm_pdu = deliver_sm_pdu + tag_n_len + value
                self._run(self.cli._parse_response_pdu(pdu=deliver_sm_pdu))

                self.assertTrue(mock_hook_from_smsc.mock.called)
                self.assertEqual(
                    mock_hook_from_smsc.mock.call_args[1]["smpp_command"],
                    naz.SmppCommand.DELIVER_SM,
                )
                self.assertEqual(mock_hook_from_smsc.mock.call_args[1]["log_id"], log_id)
                self.assertEqual(
                    mock_hook_from_smsc.mock.call_args[1]["hook_metadata"], hook_metadata
                )

    def test_re_establish_conn_bind(self):
        """
        test that `Client.re_establish_conn_bind` calls `Client.connect` & `Client.tranceiver_bind`
        """
        with mock.patch("asyncio.open_connection", new=AsyncMock()) as mock_naz_connect, mock.patch(
            "naz.Client.tranceiver_bind", new=AsyncMock()
        ) as mock_naz_tranceiver_bind:
            submit_sm_resp_pdu = (
                b"\x00\x00\x00\x12\x80\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x030\x00"
            )
            mock_naz_connect.mock.return_value = (
                MockStreamReader(pdu=submit_sm_resp_pdu),
                MockStreamWriter(),
            )

            self._run(
                self.cli.re_establish_conn_bind(
                    smpp_command=naz.SmppCommand.SUBMIT_SM, log_id="log_id", TESTING=True
                )
            )
            self.assertTrue(mock_naz_connect.mock.called)
            self.assertTrue(mock_naz_tranceiver_bind.mock.called)

    def test_send_data_under_disconnection(self):
        """
        test that if sockect is disconnected, `naz` will try to re-connect & re-bind
        """
        with mock.patch("naz.Client.tranceiver_bind", new=AsyncMock()) as mock_naz_tranceiver_bind:
            # do not connect or bind
            self.cli.current_session_state = naz.SmppSessionState.BOUND_TRX
            self._run(
                self.cli.send_data(
                    smpp_command=naz.SmppCommand.SUBMIT_SM, msg=b"someMessage", log_id="log_id"
                )
            )
            self.assertTrue(mock_naz_tranceiver_bind.mock.called)

    def test_issues_67(self):
        """
        test to prove we have fixed: https://github.com/komuw/naz/issues/67
        1. start broker
        2. start naz and run a naz operation like `Client..enquire_link`
        3. kill broker
        4. run a naz operation like `Client..enquire_link`
        """
        with mock.patch("naz.Client.tranceiver_bind", new=AsyncMock()) as mock_naz_tranceiver_bind:
            self.cli.current_session_state = naz.SmppSessionState.BOUND_TRX
            self.cli.writer = None  # simulate a connection loss
            self._run(
                self.cli.send_data(
                    smpp_command=naz.SmppCommand.SUBMIT_SM, msg=b"someMessage", log_id="log_id"
                )
            )
            self.assertTrue(mock_naz_tranceiver_bind.mock.called)

    @skip("TODO:fix this. It does not work.")
    def test_issues_112(self):
        """
        test to prove we have fixed: https://github.com/komuw/naz/issues/112

        Run `Client.enquire_link`. Check if `StreamWriter.write` was called twice(one for `tranceiver_bind` and another for `enquire_link`)
        If `StreamWriter.write` was called, it means that our `enquire_link` call didnt get a:
          enquire_link cannot be sent to SMSC when the client session state is: OPEN error.
        """
        with mock.patch("asyncio.streams.StreamWriter.write") as mock_naz_writer:
            self._run(self.cli.connect())
            self._run(self.cli.tranceiver_bind())
            # self.cli.current_session_state = naz.SmppSessionState.BOUND_TRX
            self._run(self.cli.enquire_link(TESTING=True))
            self.assertTrue(mock_naz_writer.called)
            self.assertEqual(mock_naz_writer.call_count, 2)

    def test_command_id_lookup(self):
        command_id = self.cli._search_by_command_id_code(
            command_id_code=self.cli.command_ids[naz.SmppCommand.BIND_TRANSCEIVER]
        )
        self.assertEqual(command_id, "bind_transceiver")

        command_id = self.cli._search_by_command_id_code(command_id_code=0x00000102)
        self.assertEqual(command_id, "alert_notification")

        command_id = self.cli._search_by_command_id_code(command_id_code=0x00000016)
        self.assertEqual(command_id, "reserved_list_c")

        command_id = self.cli._search_by_command_id_code(command_id_code=0x00000104)
        self.assertEqual(command_id, "reserved_for_smpp_extension_a")

    def test_command_handlers_unkown_command_ids(self):
        """
        test that `Client.command_handlers` behaves okay for unkown command_ids
        """
        with mock.patch("naz.hooks.SimpleHook.from_smsc", new=AsyncMock()) as mock_hook_from_smsc:
            sequence_number = 3
            alert_notification = naz.SmppCommand.ALERT_NOTIFICATION
            self._run(
                self.cli.command_handlers(
                    pdu=b"pdu",
                    body_data=b"body_data",
                    smpp_command=alert_notification,
                    command_status_value=0,
                    sequence_number=sequence_number,
                    log_id="log_id",
                    hook_metadata="hook_metadata",
                )
            )
            self.assertTrue(mock_hook_from_smsc.mock.called)
            self.assertEqual(
                mock_hook_from_smsc.mock.call_args[1]["smpp_command"], alert_notification
            )
            self.assertEqual(mock_hook_from_smsc.mock.call_args[1]["log_id"], "log_id")

            # reserved command_id's
            sequence_number = 4
            reserved_for_smpp_extension_a = naz.SmppCommand.RESERVED_FOR_SMPP_EXTENSION_A
            self._run(
                self.cli.command_handlers(
                    pdu=b"pdu",
                    body_data=b"body_data",
                    smpp_command=reserved_for_smpp_extension_a,
                    command_status_value=0,
                    sequence_number=sequence_number,
                    log_id="log_id",
                    hook_metadata="hook_metadata",
                )
            )
            self.assertTrue(mock_hook_from_smsc.mock.called)
            self.assertEqual(
                mock_hook_from_smsc.mock.call_args[1]["smpp_command"], reserved_for_smpp_extension_a
            )
            self.assertEqual(mock_hook_from_smsc.mock.call_args[1]["log_id"], "log_id")

            # known command_id
            sequence_number = 5
            bind_transceiver = naz.SmppCommand.BIND_TRANSCEIVER
            self._run(
                self.cli.command_handlers(
                    pdu=b"pdu",
                    body_data=b"body_data",
                    smpp_command=bind_transceiver,
                    command_status_value=0,
                    sequence_number=sequence_number,
                    log_id="log_id",
                    hook_metadata="hook_metadata",
                )
            )
            self.assertTrue(mock_hook_from_smsc.mock.called)
            self.assertEqual(
                mock_hook_from_smsc.mock.call_args[1]["smpp_command"], bind_transceiver
            )
            self.assertEqual(mock_hook_from_smsc.mock.call_args[1]["log_id"], "log_id")

    def test_command_status_lookup(self):
        command_status = 411_041_792
        command_status = self.cli._search_by_command_status_value(
            command_status_value=command_status
        )
        self.assertEqual(command_status.code, "Reserved")

        command_status = 0x00000000
        command_status = self.cli._search_by_command_status_value(
            command_status_value=command_status
        )
        self.assertEqual(command_status.code, "ESME_ROK")

        command_status = 0x00000014
        command_status = self.cli._search_by_command_status_value(
            command_status_value=command_status
        )
        self.assertEqual(command_status.code, "ESME_RMSGQFUL")

        command_status = 0x00000400
        command_status = self.cli._search_by_command_status_value(
            command_status_value=command_status
        )
        self.assertEqual(command_status.code, "Reserved")

    def test_SmppCommandStatus(self):
        """
        tests of bugs gotten via benchmarks
        """
        with mock.patch("naz.hooks.SimpleHook.from_smsc", new=AsyncMock()) as mock_hook_from_smsc:
            sequence_number = 1
            bind_transceiver = naz.SmppCommand.BIND_TRANSCEIVER
            command_status = 411_041_792
            full_pdu = b"pdu"
            self._run(
                self.cli.command_handlers(
                    pdu=full_pdu,
                    body_data=b"body_data",
                    smpp_command=bind_transceiver,
                    command_status_value=command_status,
                    sequence_number=sequence_number,
                    log_id="log_id",
                    hook_metadata="hook_metadata",
                )
            )
            self.assertTrue(mock_hook_from_smsc.mock.called)
            self.assertEqual(
                mock_hook_from_smsc.mock.call_args[1]["smpp_command"], bind_transceiver
            )
            self.assertEqual(mock_hook_from_smsc.mock.call_args[1]["log_id"], "log_id")
            self.assertEqual(mock_hook_from_smsc.mock.call_args[1]["pdu"], full_pdu)

    def test_protocol_error(self):
        """
        tests that if we read bytes from connection and naz is unable to parse them,
        it should close connection.
        https://github.com/komuw/naz/issues/135
        """
        with mock.patch(
            "naz.Client._unbind_and_disconnect", new=AsyncMock()
        ) as mock_naz_unbind_and_disconnect:
            self._run(self.cli._parse_response_pdu(pdu=b"\x00\x00\x00\x15\x80"))
            self.assertTrue(mock_naz_unbind_and_disconnect.mock.called)

    def test_enquire_link_resp_sending(self):
        with mock.patch("naz.broker.SimpleBroker.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            mock_naz_dequeue.mock.return_value = naz.protocol.EnquireLinkResp(
                log_id="log_id", sequence_number=34,
            )

            self._run(self.cli.connect())
            # hack to allow sending submit_sm even when state is wrong
            self.cli.current_session_state = "BOUND_TRX"
            self._run(self.cli.dequeue_messages(TESTING=True))
            self.assertTrue(mock_naz_dequeue.mock.called)

    def test_deliver_sm_resp_sending(self):
        with mock.patch("naz.broker.SimpleBroker.dequeue", new=AsyncMock()) as mock_naz_dequeue:
            mock_naz_dequeue.mock.return_value = naz.protocol.DeliverSmResp(
                log_id="mock-id", message_id="message_id", sequence_number=90,
            )

            self._run(self.cli.connect())
            # hack to allow sending submit_sm even when state is wrong
            self.cli.current_session_state = "BOUND_TRX"
            self._run(self.cli.dequeue_messages(TESTING=True))
            self.assertTrue(mock_naz_dequeue.mock.called)

    def test_send_message_with_more_args(self):
        log_id = "12345"
        short_message = "hello"
        msg = naz.protocol.SubmitSM(
            short_message=short_message,
            source_addr="2492",
            destination_addr="8930302",
            log_id=log_id,
            source_addr_ton=0x00000010,  # National
            dest_addr_npi=0x00001110,  # Internet
        )
        with mock.patch("naz.broker.SimpleBroker.enqueue", new=AsyncMock()) as mock_naz_enqueue:
            self._run(self.cli.connect())
            self._run(self.cli.tranceiver_bind())

            self._run(self.cli.send_message(msg))
            self.assertTrue(mock_naz_enqueue.mock.called)
            self.assertEqual(mock_naz_enqueue.mock.call_args[0][1].log_id, log_id)
            self.assertEqual(
                mock_naz_enqueue.mock.call_args[0][1].smpp_command, naz.SmppCommand.SUBMIT_SM
            )
            self.assertEqual(mock_naz_enqueue.mock.call_args[0][1].short_message, short_message)
