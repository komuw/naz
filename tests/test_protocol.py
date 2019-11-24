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

    def test_success_instanciation(self):
        proto = naz.protocol.Message(
            version=1, smpp_command=naz.SmppCommand.SUBMIT_SM, log_id="some-log-id"
        )
        self.assertIsNotNone(proto)

    def test_pdu_N_shortMsg_exclusive(self):
        with self.assertRaises(ValueError) as raised_exception:
            naz.protocol.Message(
                version=1,
                smpp_command=naz.SmppCommand.SUBMIT_SM,
                log_id="some-log-id",
                pdu=b"some-pdu",
                short_message="some-msg",
            )
        self.assertIsInstance(raised_exception.exception, ValueError)
        self.assertIn(
            "You cannot specify both `pdu` and `short_message`", str(raised_exception.exception)
        )

    def test_json_serialization(self):
        proto = naz.protocol.Message(
            version=1,
            smpp_command=naz.SmppCommand.BIND_TRANSCEIVER_RESP,
            log_id="some-log-id",
            pdu=b"\x00\x00\x00\x18\x80\x00\x00\t\x00\x00\x00\x00\x00\x00\x00\x06SMPPSim\x00",
            codec_class=naz.nazcodec.SimpleNazCodec(),
        )
        print(proto.json())
