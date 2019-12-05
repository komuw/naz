# do not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

import json
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
            version=1,
            smpp_command=naz.SmppCommand.SUBMIT_SM,
            log_id="some-log-id",
            short_message="Hello, thanks for shopping with us.",
            source_addr="254722111111",
            destination_addr="254722999999",
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
            pdu=b"pdu",
        )
        _in_json = proto.to_json()
        _in_dict = json.loads(_in_json)
        _in_dict["pdu"] = _in_dict["pdu"].encode(naz.protocol.Message.ENCODING)

        self.assertEqual(type(proto), type(naz.protocol.Message(**_in_dict)))

    def test_json_serialization_pdu_None(self):
        proto = naz.protocol.Message(
            version=1,
            smpp_command=naz.SmppCommand.BIND_TRANSCEIVER_RESP,
            log_id="some-log-id",
            pdu=None,
        )
        _in_json = proto.to_json()

        self.assertIsNotNone(_in_json)

    def test_json_de_serialization(self):
        x = {
            "version": 1,
            "smpp_command": "bind_transceiver_resp",
            "log_id": "some-log-id",
            "pdu": "pdu",
        }
        _in_json = json.dumps(x)
        proto = naz.protocol.Message.from_json(_in_json)

        self.assertIsInstance(proto, naz.protocol.Message)

    def test_protocol_message_ENCODING(self):
        """
        test that even though `naz.protocol.Message.pdu` make contain smpp fields that are encoded
        using different encoding schemes(ascii, ucs2, struct.pack etc);
        it is still okay to use the `naz.protocol.Message.ENCODING` on them.
        And that when you encode and decode them using `naz.protocol.Message.ENCODING`, they will come out alright.
        """
        # pdu that contains some fields that have been
        # encoded with `ascii` and other fields encoded with `ucs2`
        full_pdu = b"\x00\x00\x00V\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x05CMT\x00\x01\x01254722111111\x00\x01\x01254722999999\x00\x03\x00\x00\x00\x00\x01\x00\x08\x00\x1a\x00H\x00e\x00l\x00l\x00o\x00 \x00W\x00o\x00r\x00l\x00d\x00-\x000"
        self.assertEqual(
            full_pdu.decode(naz.protocol.Message.ENCODING).encode(naz.protocol.Message.ENCODING),
            full_pdu,
        )

        proto = naz.protocol.Message(
            version=1, smpp_command=naz.SmppCommand.SUBMIT_SM, log_id="some-log-id", pdu=full_pdu
        )
        _in_json = proto.to_json()
        self.assertIsNotNone(_in_json)

        new_proto = naz.protocol.Message.from_json(_in_json)
        self.assertEqual(type(proto), type(new_proto))
        self.assertEqual(new_proto.pdu, full_pdu)
