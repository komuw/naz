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
        proto = naz.protocol.SubmitSM(
            version=1,
            smpp_command=naz.SmppCommand.SUBMIT_SM,
            log_id="some-log-id",
            short_message="Hello, thanks for shopping with us.",
            source_addr="254722111111",
            destination_addr="254722999999",
        )
        self.assertIsNotNone(proto)

    def test_json_serialization(self):
        proto = naz.protocol.SubmitSM(
            version=1,
            log_id="some-log-id",
            short_message="hello",
            source_addr="546464",
            destination_addr="24292",
        )
        _in_json = proto.to_json()
        _in_dict = json.loads(_in_json)
        self.assertEqual(type(proto), type(naz.protocol.SubmitSM(**_in_dict)))

    def test_json_serialization_pdu_None(self):
        proto = naz.protocol.DeliverSmResp(
            version=1,
            smpp_command=naz.SmppCommand.DELIVER_SM_RESP,
            log_id="some-log-id",
            sequence_number=599,
            message_id="900",
        )
        _in_json = proto.to_json()
        self.assertIsNotNone(_in_json)

    def test_json_de_serialization(self):
        x = {
            "version": 1,
            "smpp_command": naz.SmppCommand.SUBMIT_SM,
            "log_id": "some-log-id",
            "short_message": "hello",
            "source_addr": "546464",
            "destination_addr": "24292",
        }
        _in_json = json.dumps(x)
        proto = naz.protocol.json_to_Message(_in_json)

        self.assertIsInstance(proto, naz.protocol.Message)

    def test_serialize_n_deserialize(self):
        proto = naz.protocol.EnquireLinkResp(log_id="some-log-id", sequence_number=294)
        _in_json = proto.to_json()
        self.assertIsNotNone(_in_json)

        new_proto = naz.protocol.json_to_Message(_in_json)
        self.assertEqual(type(proto), type(new_proto))
        self.assertEqual(new_proto.log_id, proto.log_id)
        self.assertEqual(new_proto.sequence_number, proto.sequence_number)
        self.assertEqual(new_proto.smpp_command, naz.state.SmppCommand.ENQUIRE_LINK_RESP)
        self.assertEqual(new_proto.smpp_command, naz.state.SmppCommand.ENQUIRE_LINK_RESP)
