import abc
import json
import typing

from . import state


NAZ_MESSAGE_PROTOCOL_VERSION = 1
"""
The messages that are published to a queue by either naz
or user application should be versioned.
This version will enable naz to be able to evolve in future;
eg a future version of naz could add/remove the number of required items in a message.
This is a bit similar to: http://docs.celeryproject.org/en/latest/internals/protocol.html
"""


class Message(abc.ABC):
    """
    The message protocol for `naz`. It is the code representation of what
    gets queued into a naz broker.
    This is the interface that must be implemented to satisfy naz's message protocol.

    Users should only ever have to deal with the :class:`SubmitSM <SubmitSM>` implementation
    """

    @abc.abstractmethod
    def __init__(
        self, version: int, smpp_command: str, log_id: str, hook_metadata: str = ""
    ) -> None:
        """
        Parameters:
            version: This indicates the current version of the naz message protocol.
                     This version will enable naz to be able to evolve in future; a future version of `naz` may ship with a different message protocol.
            smpp_command: any one of the SMSC commands eg submit_sm
            log_id: a unique identify of this request
            hook_metadata: a string that to will later on be passed to `naz.Client.hook`. Your application can use it for correlation.
        """
        if not isinstance(version, int):
            raise ValueError(
                "`version` should be of type:: `int` You entered: {0}".format(type(version))
            )
        if version != NAZ_MESSAGE_PROTOCOL_VERSION:
            raise ValueError(
                "`naz` currently only supports naz protocol version {0}".format(
                    NAZ_MESSAGE_PROTOCOL_VERSION
                )
            )
        if not isinstance(smpp_command, str):
            raise ValueError(
                "`smpp_command` should be of type:: `str` You entered: {0}".format(
                    type(smpp_command)
                )
            )
        if not isinstance(log_id, str):
            raise ValueError(
                "`log_id` should be of type:: `str` You entered: {0}".format(type(log_id))
            )
        if not isinstance(hook_metadata, str):
            raise ValueError(
                "`hook_metadata` should be of type:: `str` You entered: {0}".format(
                    type(hook_metadata)
                )
            )
        self.version = version
        self.smpp_command = smpp_command
        self.log_id = log_id
        self.hook_metadata = hook_metadata

    @abc.abstractmethod
    def to_json(self) -> str:
        """
        Serializes the message protocol to json. You can use this method if you would
        like to save the `Message` into a broker like redis/rabbitmq/postgres etc.
        """
        raise NotImplementedError("to_json method must be implemented.")

    @staticmethod
    @abc.abstractmethod
    def from_json(json_message: str) -> "Message":
        """
        Deserializes the message protocol from json.

        Parameters:
            json_message: `naz.protocol.Message` in json format.
        """
        raise NotImplementedError("from_json method must be implemented.")


class SubmitSM(Message):
    """
    The code representation of the `submit_sm` pdu that will get queued into a broker.

    Usage:

    .. highlight:: python
    .. code-block:: python

        import os
        import naz

        broker = naz.broker.SimpleBroker(maxsize=1000)
        client = naz.Client(
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                broker=broker,
            )
        msg = naz.protocol.SubmitSM(
            short_message="hello world",
            source_addr="255700111222",
            destination_addr="255799000888",
            log_id="some-id",
        )
        await client.send_message(msg)
    """

    def __init__(
        self,
        short_message: str,
        source_addr: str,
        destination_addr: str,
        log_id: str,
        service_type: str = "CMT",  # section 5.2.11
        source_addr_ton: int = 0x00000001,  # section 5.2.5
        source_addr_npi: int = 0x00000001,
        dest_addr_ton: int = 0x00000001,
        dest_addr_npi: int = 0x00000001,
        # xxxxxx00 store-and-forward
        # xx0010xx Short Message contains ESME Delivery Acknowledgement
        # 00xxxxxx No specific features selected
        esm_class: int = 0b00000011,  # section 5.2.12
        protocol_id: int = 0x00000000,
        priority_flag: int = 0x00000000,
        schedule_delivery_time: str = "",
        validity_period: str = "",
        # xxxxxx01 SMSC Delivery Receipt requested where final delivery outcome is delivery success or failure
        # xxxx01xx SME Delivery Acknowledgement requested
        # xxx0xxxx No Intermediate notification requested
        # all other values reserved
        registered_delivery: int = 0b00000001,  # see section 5.2.17
        replace_if_present_flag: int = 0x00000000,
        sm_default_msg_id: int = 0x00000000,
        ### NON-SMPP ATTRIBUTES ###
        smpp_command: str = state.SmppCommand.SUBMIT_SM,
        version: int = 1,
        hook_metadata: str = "",
        encoding: str = "gsm0338",
        errors: str = "strict",
        ### NON-SMPP ATTRIBUTES ###
        #### OPTIONAL SMPP PARAMETERS ###
        # section 4.4.1 of smpp documentation
        # TODO:
        dest_addr_subunit: typing.Union[None, int] = None,
        dest_network_type: typing.Union[None, int] = None,
        dest_bearer_type: typing.Union[None, int] = None,
        dest_telematics_id: typing.Union[None, int] = None,
        source_addr_subunit: typing.Union[None, int] = None,
        source_network_type: typing.Union[None, int] = None,
        source_bearer_type: typing.Union[None, int] = None,
        source_telematics_id: typing.Union[None, int] = None,
        qos_time_to_live: typing.Union[None, int] = None,
        payload_type: typing.Union[None, int] = None,
        ms_msg_wait_facilities: typing.Union[None, int] = None,
        privacy_indicator: typing.Union[None, int] = None,
        user_message_reference: typing.Union[None, int] = None,
        user_response_code: typing.Union[None, int] = None,
        source_port: typing.Union[None, int] = None,
        destination_port: typing.Union[None, int] = None,
        sar_msg_ref_num: typing.Union[None, int] = None,
        language_indicator: typing.Union[None, int] = None,
        sar_total_segments: typing.Union[None, int] = None,
        sar_segment_seqnum: typing.Union[None, int] = None,
        sc_interface_version: typing.Union[None, int] = None,
        callback_num_pres_ind: typing.Union[None, int] = None,
        number_of_messages: typing.Union[None, int] = None,
        dpf_result: typing.Union[None, int] = None,
        set_dpf: typing.Union[None, int] = None,
        ms_availability_status: typing.Union[None, int] = None,
        delivery_failure_reason: typing.Union[None, int] = None,
        more_messages_to_send: typing.Union[None, int] = None,
        message_state: typing.Union[None, int] = None,
        display_time: typing.Union[None, int] = None,
        sms_signal: typing.Union[None, int] = None,
        ms_validity: typing.Union[None, int] = None,
        its_reply_type: typing.Union[None, int] = None,
        additional_status_info_text: typing.Union[None, str] = None,
        receipted_message_id: typing.Union[None, str] = None,
        source_subaddress: typing.Union[None, str] = None,
        dest_subaddress: typing.Union[None, str] = None,
        callback_num_atag: typing.Union[None, str] = None,
        callback_num: typing.Union[None, str] = None,
        network_error_code: typing.Union[None, str] = None,
        message_payload: typing.Union[None, str] = None,
        ussd_service_op: typing.Union[None, str] = None,
        its_session_info: typing.Union[None, str] = None,
        alert_on_message_delivery: bool = False,
        #### OPTIONAL SMPP PARAMETERS ###
    ) -> None:
        """
        Parameters:
            short_message: message to send to SMSC
            source_addr: the identifier(eg msisdn) of the message sender
            destination_addr: the identifier(eg msisdn) of the message recipient
            log_id: a unique identify of this request
            version: This indicates the current version of the naz message protocol.
                     This version will enable naz to be able to evolve in future; a future version of `naz` may ship with a different message protocol.
            hook_metadata: a string that to will later on be passed to `naz.Client.hook`. Your application can use it for correlation.
            service_type:	Indicates the SMS Application service associated with the message
            source_addr_ton:	Type of Number of message originator.
            source_addr_npi:	Numbering Plan Identity of message originator.
            dest_addr_ton:	Type of Number for destination.
            dest_addr_npi:	Numbering Plan Identity of destination
            esm_class:	Indicates Message Mode & Message Type.
            protocol_id:	Protocol Identifier. Network specific field.
            priority_flag:	Designates the priority level of the message.
            schedule_delivery_time:	The short message is to be scheduled by the SMSC for delivery.
            validity_period:	The validity period of this message.
            registered_delivery:	Indicator to signify if an SMSC delivery receipt or an SME acknowledgement is required.
            replace_if_present_flag:	Flag indicating if submitted message should replace an existing message.
            sm_default_msg_id:	Indicates the short message to send from a list of predefined (‘canned’) short messages stored on the SMSC
            smpp_command: any one of the SMSC commands eg submit_sm
            encoding: `encoding <https://docs.python.org/3/library/codecs.html#standard-encodings>`_ used to encode messages been sent to SMSC.
                      The encoding should be one of the encodings recognised by the SMPP specification. See section 5.2.19 of SMPP spec.
                      If you want to use your own custom codec implementation for an encoding, make sure to pass it to :py:attr:`naz.Client.custom_codecs <naz.Client.custom_codecs>`
            errors:	same meaning as the errors argument to pythons' `encode <https://docs.python.org/3/library/codecs.html#codecs.encode>`_ method
            user_message_reference: ESME assigned message reference number.
        """

        self._validate_msg_type_args(
            short_message=short_message,
            source_addr=source_addr,
            destination_addr=destination_addr,
            log_id=log_id,
            version=version,
            hook_metadata=hook_metadata,
            service_type=service_type,
            source_addr_ton=source_addr_ton,
            source_addr_npi=source_addr_npi,
            dest_addr_ton=dest_addr_ton,
            dest_addr_npi=dest_addr_npi,
            esm_class=esm_class,
            protocol_id=protocol_id,
            priority_flag=priority_flag,
            schedule_delivery_time=schedule_delivery_time,
            validity_period=validity_period,
            registered_delivery=registered_delivery,
            replace_if_present_flag=replace_if_present_flag,
            sm_default_msg_id=sm_default_msg_id,
            encoding=encoding,
            errors=errors,
        )

        self.smpp_command: str = state.SmppCommand.SUBMIT_SM
        self.version = version

        self.short_message = short_message
        self.source_addr = source_addr
        self.destination_addr = destination_addr
        self.log_id = log_id
        self.hook_metadata = hook_metadata
        self.service_type = service_type
        self.source_addr_ton = source_addr_ton
        self.source_addr_npi = source_addr_npi
        self.dest_addr_ton = dest_addr_ton
        self.dest_addr_npi = dest_addr_npi
        self.esm_class = esm_class
        self.protocol_id = protocol_id
        self.priority_flag = priority_flag
        self.schedule_delivery_time = schedule_delivery_time
        self.validity_period = validity_period
        self.registered_delivery = registered_delivery
        self.replace_if_present_flag = replace_if_present_flag
        self.sm_default_msg_id = sm_default_msg_id
        self.encoding = encoding
        self.errors = errors
        self.data_coding = state.SmppDataCoding._find_data_coding(self.encoding)

        self.optional_tags_dict = {}
        if user_message_reference:
            self.optional_tags_dict.update({"user_message_reference": user_message_reference})

        if self.optional_tags_dict:
            # validate optional tags
            for opt_name in self.optional_tags_dict.keys():
                state.OptionalTag(name=opt_name, value=self.optional_tags_dict[opt_name])

        print("lla")
        print("hello")

    @staticmethod
    def _validate_msg_type_args(
        short_message: str,
        source_addr: str,
        destination_addr: str,
        log_id: str,
        version: int,
        hook_metadata: str,
        service_type: str,
        source_addr_ton: int,
        source_addr_npi: int,
        dest_addr_ton: int,
        dest_addr_npi: int,
        esm_class: int,
        protocol_id: int,
        priority_flag: int,
        schedule_delivery_time: str,
        validity_period: str,
        registered_delivery: int,
        replace_if_present_flag: int,
        sm_default_msg_id: int,
        encoding: str,
        errors: str,
    ) -> None:
        if not isinstance(version, int):
            raise ValueError(
                "`version` should be of type:: `int` You entered: {0}".format(type(version))
            )
        if version != NAZ_MESSAGE_PROTOCOL_VERSION:
            raise ValueError(
                "`naz` currently only supports naz protocol version {0}".format(
                    NAZ_MESSAGE_PROTOCOL_VERSION
                )
            )
        if not isinstance(short_message, str):
            raise ValueError(
                "`short_message` should be of type:: `str` You entered: {0}".format(
                    type(short_message)
                )
            )
        if not isinstance(source_addr, str):
            raise ValueError(
                "`source_addr` should be of type:: `str` You entered: {0}".format(type(source_addr))
            )
        if not isinstance(destination_addr, str):
            raise ValueError(
                "`destination_addr` should be of type:: `str` You entered: {0}".format(
                    type(destination_addr)
                )
            )
        if not isinstance(log_id, str):
            raise ValueError(
                "`log_id` should be of type:: `str` You entered: {0}".format(type(log_id))
            )
        if not isinstance(hook_metadata, str):
            raise ValueError(
                "`hook_metadata` should be of type:: `str` You entered: {0}".format(
                    type(hook_metadata)
                )
            )
        if not isinstance(service_type, str):
            raise ValueError(
                "`service_type` should be of type:: `str` You entered: {0}".format(
                    type(service_type)
                )
            )
        if not isinstance(source_addr_ton, int):
            raise ValueError(
                "`source_addr_ton` should be of type:: `int` You entered: {0}".format(
                    type(source_addr_ton)
                )
            )
        if not isinstance(source_addr_npi, int):
            raise ValueError(
                "`source_addr_npi` should be of type:: `int` You entered: {0}".format(
                    type(source_addr_npi)
                )
            )
        if not isinstance(dest_addr_ton, int):
            raise ValueError(
                "`dest_addr_ton` should be of type:: `int` You entered: {0}".format(
                    type(dest_addr_ton)
                )
            )
        if not isinstance(dest_addr_npi, int):
            raise ValueError(
                "`dest_addr_npi` should be of type:: `int` You entered: {0}".format(
                    type(dest_addr_npi)
                )
            )
        if not isinstance(esm_class, int):
            raise ValueError(
                "`esm_class` should be of type:: `int` You entered: {0}".format(type(esm_class))
            )
        if not isinstance(protocol_id, int):
            raise ValueError(
                "`protocol_id` should be of type:: `int` You entered: {0}".format(type(protocol_id))
            )
        if not isinstance(priority_flag, int):
            raise ValueError(
                "`priority_flag` should be of type:: `int` You entered: {0}".format(
                    type(priority_flag)
                )
            )
        if not isinstance(schedule_delivery_time, str):
            raise ValueError(
                "`schedule_delivery_time` should be of type:: `str` You entered: {0}".format(
                    type(schedule_delivery_time)
                )
            )
        if not isinstance(validity_period, str):
            raise ValueError(
                "`validity_period` should be of type:: `str` You entered: {0}".format(
                    type(validity_period)
                )
            )
        if not isinstance(registered_delivery, int):
            raise ValueError(
                "`registered_delivery` should be of type:: `int` You entered: {0}".format(
                    type(registered_delivery)
                )
            )
        if not isinstance(replace_if_present_flag, int):
            raise ValueError(
                "`replace_if_present_flag` should be of type:: `int` You entered: {0}".format(
                    type(replace_if_present_flag)
                )
            )
        if not isinstance(sm_default_msg_id, int):
            raise ValueError(
                "`sm_default_msg_id` should be of type:: `int` You entered: {0}".format(
                    type(sm_default_msg_id)
                )
            )
        if not isinstance(encoding, str):
            raise ValueError(
                "`encoding` should be of type:: `str` You entered: {0}".format(type(encoding))
            )
        if not isinstance(errors, str):
            raise ValueError(
                "`errors` should be of type:: `str` You entered: {0}".format(type(errors))
            )

        # optional smpp parameters get validated on their own

    def to_json(self) -> str:
        _item = dict(
            smpp_command=self.smpp_command,
            version=self.version,
            short_message=self.short_message,
            source_addr=self.source_addr,
            destination_addr=self.destination_addr,
            log_id=self.log_id,
            hook_metadata=self.hook_metadata,
            service_type=self.service_type,
            source_addr_ton=self.source_addr_ton,
            source_addr_npi=self.source_addr_npi,
            dest_addr_ton=self.dest_addr_ton,
            dest_addr_npi=self.dest_addr_npi,
            esm_class=self.esm_class,
            protocol_id=self.protocol_id,
            priority_flag=self.priority_flag,
            schedule_delivery_time=self.schedule_delivery_time,
            validity_period=self.validity_period,
            registered_delivery=self.registered_delivery,
            replace_if_present_flag=self.replace_if_present_flag,
            sm_default_msg_id=self.sm_default_msg_id,
            encoding=self.encoding,
            errors=self.errors,
        )
        _item.update(**self.optional_tags_dict)
        return json.dumps(_item)

    @staticmethod
    def from_json(json_message: str) -> "SubmitSM":
        _in_dict = json.loads(json_message)
        return SubmitSM(**_in_dict)


class EnquireLinkResp(Message):
    def __init__(
        self,
        log_id: str,
        sequence_number: int,
        smpp_command: str = state.SmppCommand.ENQUIRE_LINK_RESP,
        version: int = 1,
        hook_metadata: str = "",
    ) -> None:
        """
        Parameters:
            log_id: a unique identify of this request
            smpp_command: any one of the SMSC commands eg enquire_link_resp
            version: This indicates the current version of the naz message protocol.
                     This version will enable naz to be able to evolve in future; a future version of `naz` may ship with a different message protocol.
            hook_metadata: a string that to will later on be passed to `naz.Client.hook`. Your application can use it for correlation.
            sequence_number: SMPP sequence_number
        """
        if not isinstance(log_id, str):
            raise ValueError(
                "`log_id` should be of type:: `str` You entered: {0}".format(type(log_id))
            )
        if not isinstance(sequence_number, int):
            raise ValueError(
                "`sequence_number` should be of type:: `int` You entered: {0}".format(
                    type(sequence_number)
                )
            )
        if not isinstance(version, int):
            raise ValueError(
                "`version` should be of type:: `int` You entered: {0}".format(type(version))
            )
        if version != NAZ_MESSAGE_PROTOCOL_VERSION:
            raise ValueError(
                "`naz` currently only supports naz protocol version {0}".format(
                    NAZ_MESSAGE_PROTOCOL_VERSION
                )
            )
        if not isinstance(hook_metadata, str):
            raise ValueError(
                "`hook_metadata` should be of type:: `str` You entered: {0}".format(
                    type(hook_metadata)
                )
            )
        self.log_id = log_id
        self.sequence_number = sequence_number
        self.version = version
        self.smpp_command = state.SmppCommand.ENQUIRE_LINK_RESP
        self.hook_metadata = hook_metadata

    def to_json(self) -> str:
        _item = dict(
            smpp_command=self.smpp_command,
            version=self.version,
            log_id=self.log_id,
            sequence_number=self.sequence_number,
            hook_metadata=self.hook_metadata,
        )
        return json.dumps(_item)

    @staticmethod
    def from_json(json_message: str) -> "EnquireLinkResp":
        _in_dict = json.loads(json_message)
        return EnquireLinkResp(**_in_dict)


class DeliverSmResp(Message):
    def __init__(
        self,
        log_id: str,
        message_id: str,
        sequence_number: int,
        smpp_command: str = state.SmppCommand.DELIVER_SM_RESP,
        version: int = 1,
        hook_metadata: str = "",
    ) -> None:
        """
        Parameters:
            log_id: a unique identify of this request
            smpp_command: any one of the SMSC commands eg deliver_sm_resp
            version: This indicates the current version of the naz message protocol.
                     This version will enable naz to be able to evolve in future; a future version of `naz` may ship with a different message protocol.
            hook_metadata: a string that to will later on be passed to `naz.Client.hook`. Your application can use it for correlation.
            message_id: id of this message
            sequence_number: SMPP sequence_number
        """
        if not isinstance(log_id, str):
            raise ValueError(
                "`log_id` should be of type:: `str` You entered: {0}".format(type(log_id))
            )
        if not isinstance(message_id, str):
            raise ValueError(
                "`message_id` should be of type:: `str` You entered: {0}".format(type(message_id))
            )
        if not isinstance(sequence_number, int):
            raise ValueError(
                "`sequence_number` should be of type:: `int` You entered: {0}".format(
                    type(sequence_number)
                )
            )
        if not isinstance(version, int):
            raise ValueError(
                "`version` should be of type:: `int` You entered: {0}".format(type(version))
            )
        if version != NAZ_MESSAGE_PROTOCOL_VERSION:
            raise ValueError(
                "`naz` currently only supports naz protocol version {0}".format(
                    NAZ_MESSAGE_PROTOCOL_VERSION
                )
            )
        if not isinstance(hook_metadata, str):
            raise ValueError(
                "`hook_metadata` should be of type:: `str` You entered: {0}".format(
                    type(hook_metadata)
                )
            )
        self.log_id = log_id
        self.version = version
        self.smpp_command = state.SmppCommand.DELIVER_SM_RESP
        self.message_id = message_id
        self.sequence_number = sequence_number
        self.hook_metadata = hook_metadata

    def to_json(self) -> str:
        _item = dict(
            smpp_command=self.smpp_command,
            version=self.version,
            log_id=self.log_id,
            message_id=self.message_id,
            sequence_number=self.sequence_number,
            hook_metadata=self.hook_metadata,
        )
        return json.dumps(_item)

    @staticmethod
    def from_json(json_message: str) -> "DeliverSmResp":
        _in_dict = json.loads(json_message)
        return DeliverSmResp(**_in_dict)


def json_to_Message(json_message: str) -> Message:
    """
    Utility function to deserialize the message protocol from json.
    You can use this method if you would like to return the `Message` from a broker like redis/rabbitmq/postgres etc.

    Parameters:
        json_message: `naz.protocol.Message` in json format.
    """
    _item = json.loads(json_message)
    smpp_command = _item["smpp_command"]
    if smpp_command == state.SmppCommand.SUBMIT_SM:
        return SubmitSM.from_json(json_message=json_message)
    elif smpp_command == state.SmppCommand.ENQUIRE_LINK_RESP:
        return EnquireLinkResp.from_json(json_message=json_message)
    elif smpp_command == state.SmppCommand.DELIVER_SM_RESP:
        return DeliverSmResp.from_json(json_message=json_message)
    else:
        raise NotImplementedError(
            "The `from_json` method for smpp_command: `{0}` has not been implemented.".format(
                smpp_command
            )
        )
