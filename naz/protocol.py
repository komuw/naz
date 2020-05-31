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
            ms_validity=1,
        )
        await client.send_message(msg)
    """

    def __init__(
        self,
        #### MANDATORY SMPP PARAMETERS ###
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
        #### MANDATORY SMPP PARAMETERS ###
        ###
        ### NON-SMPP ATTRIBUTES ###
        smpp_command: str = state.SmppCommand.SUBMIT_SM,
        version: int = 1,
        hook_metadata: str = "",
        encoding: str = "gsm0338",
        errors: str = "strict",
        ### NON-SMPP ATTRIBUTES ###
        ###
        #### OPTIONAL SMPP PARAMETERS ###
        # section 4.4.1 of smpp documentation
        user_message_reference: typing.Union[None, int] = None,
        source_port: typing.Union[None, int] = None,
        source_addr_subunit: typing.Union[None, int] = None,
        destination_port: typing.Union[None, int] = None,
        dest_addr_subunit: typing.Union[None, int] = None,
        sar_msg_ref_num: typing.Union[None, int] = None,
        sar_total_segments: typing.Union[None, int] = None,
        sar_segment_seqnum: typing.Union[None, int] = None,
        more_messages_to_send: typing.Union[None, int] = None,
        payload_type: typing.Union[None, int] = None,
        message_payload: typing.Union[None, str] = None,
        privacy_indicator: typing.Union[None, int] = None,
        callback_num: typing.Union[None, str] = None,
        callback_num_pres_ind: typing.Union[None, int] = None,
        callback_num_atag: typing.Union[None, str] = None,
        source_subaddress: typing.Union[None, str] = None,
        dest_subaddress: typing.Union[None, str] = None,
        user_response_code: typing.Union[None, int] = None,
        display_time: typing.Union[None, int] = None,
        sms_signal: typing.Union[None, int] = None,
        ms_validity: typing.Union[None, int] = None,
        ms_msg_wait_facilities: typing.Union[None, int] = None,
        number_of_messages: typing.Union[None, int] = None,
        alert_on_message_delivery: bool = False,
        language_indicator: typing.Union[None, int] = None,
        its_reply_type: typing.Union[None, int] = None,
        its_session_info: typing.Union[None, str] = None,
        ussd_service_op: typing.Union[None, str] = None,
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
            sm_default_msg_id:	Indicates the short message to send from a list of predefined ('canned') short messages stored on the SMSC
            smpp_command: any one of the SMSC commands eg submit_sm
            encoding: `encoding <https://docs.python.org/3/library/codecs.html#standard-encodings>`_ used to encode messages been sent to SMSC.
                      The encoding should be one of the encodings recognised by the SMPP specification. See section 5.2.19 of SMPP spec.
                      If you want to use your own custom codec implementation for an encoding, make sure to pass it to :py:attr:`naz.Client.custom_codecs <naz.Client.custom_codecs>`
            errors:	same meaning as the errors argument to pythons' `encode <https://docs.python.org/3/library/codecs.html#codecs.encode>`_ method
            # Optional SMPP parameters.
            user_message_reference: ESME assigned message reference number.
            source_port: It is used to indicate the application port number associated with the source address of the message
            source_addr_subunit: It is used to indicate where a message originated in the mobile station,
                                 for example a smart card in the mobile station or an external device connected to the mobile station.
            destination_port: It is used to indicate the application port number associated with the destination address of the message.
            dest_addr_subunit: It is used to route messages when received by a mobile station, for example to a smart card in the mobile station
                               or to an external device connected to the mobile station.
            sar_msg_ref_num: It is used to indicate the reference number for a particular concatenated short message.
            sar_total_segments: It is used to indicate the total number of short messages within the concatenated short message.
            sar_segment_seqnum: It is used to indicate the sequence number of a particular short message within the concatenated short message.
            more_messages_to_send: It is used by the ESME in the `submit_sm` and `data_sm` operations to indicate to the SMSC
                                   that there are further messages for the same destination SME.
            payload_type: It defines the higher layer PDU type contained in the message payload.
            message_payload: It contains the user data.
            privacy_indicator: It indicates the privacy level of the message.
            callback_num: It associates a call back number with the message.
            callback_num_pres_ind: It controls the presentation indication and screening of the callback number at the mobile station.
                                   If present, the :py:attr:`~callback_num` parameter must also be present.
            callback_num_atag: It associates an alphanumeric display with the call back number
            source_subaddress: It specifies a subaddress associated with the originator of the message.
            dest_subaddress: It specifies a subaddress associated with the destination of the message.
            user_response_code: It is a response code set by the user in a User Acknowledgement/Reply message.
            display_time: It is used to associate a display time of the short message on the MS.
            sms_signal: It is used to provide a TDMA MS with alert tone information associated with the received short message.
            ms_validity: It is used to provide an MS with validity information associated with the received short message.
            ms_msg_wait_facilities: It allows an indication to be provided to an MS that there are messages waiting for the subscriber on systems on the PLMN.
            number_of_messages: It is used to indicate the number of messages stored in a mailbox.
            alert_on_message_delivery: It is set to instruct a MS to alert the user (in a MS implementation specific manner) when the short message arrives at the MS.
            language_indicator: It is used to indicate the language of the short message.
            its_reply_type: It indicates and controls the MS user's reply method to an SMS delivery message received from the ESME.
                            It is a required parameter for the CDMA Interactive Teleservice as defined by the Korean PCS carriers [KORITS].
            its_session_info: It contains control information for the interactive session between an MS and an ESME.
                              It is a required parameter for the CDMA Interactive Teleservice as defined by the Korean PCS carriers [KORITS].
            ussd_service_op: It is required to define the USSD service operation when SMPP is being used as an interface to a (GSM) USSD system.
        """

        self._validate_msg_type_args(
            short_message=short_message,
            source_addr=source_addr,
            destination_addr=destination_addr,
            log_id=log_id,
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
            smpp_command=smpp_command,
            version=version,
            hook_metadata=hook_metadata,
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

        self.optional_tags_dict = self._create_opt_tags(
            user_message_reference=user_message_reference,
            source_port=source_port,
            source_addr_subunit=source_addr_subunit,
            destination_port=destination_port,
            dest_addr_subunit=dest_addr_subunit,
            sar_msg_ref_num=sar_msg_ref_num,
            sar_total_segments=sar_total_segments,
            sar_segment_seqnum=sar_segment_seqnum,
            more_messages_to_send=more_messages_to_send,
            payload_type=payload_type,
            message_payload=message_payload,
            privacy_indicator=privacy_indicator,
            callback_num=callback_num,
            callback_num_pres_ind=callback_num_pres_ind,
            callback_num_atag=callback_num_atag,
            source_subaddress=source_subaddress,
            dest_subaddress=dest_subaddress,
            user_response_code=user_response_code,
            display_time=display_time,
            sms_signal=sms_signal,
            ms_validity=ms_validity,
            ms_msg_wait_facilities=ms_msg_wait_facilities,
            number_of_messages=number_of_messages,
            alert_on_message_delivery=alert_on_message_delivery,
            language_indicator=language_indicator,
            its_reply_type=its_reply_type,
            its_session_info=its_session_info,
            ussd_service_op=ussd_service_op,
        )

    @staticmethod
    def _validate_msg_type_args(
        short_message: str,
        source_addr: str,
        destination_addr: str,
        log_id: str,
        smpp_command: str,
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
        if not isinstance(smpp_command, str):
            raise ValueError(
                "`smpp_command` should be of type:: `str` You entered: {0}".format(
                    type(smpp_command)
                )
            )
        if smpp_command != state.SmppCommand.SUBMIT_SM:
            raise ValueError(
                "`smpp_command` should be:: `naz.state.SmppCommand.SUBMIT_SM` You entered: {0}".format(
                    smpp_command
                )
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

        # note: optional smpp parameters get validated on their own in `_create_opt_tags`

    @staticmethod
    def _create_opt_tags(**kwargs):
        optional_tags_dict = {}
        for opt_name in kwargs.keys():
            if kwargs[opt_name] is not None:
                optional_tags_dict.update({opt_name: kwargs[opt_name]})

        # validate optional tags
        for opt_name in optional_tags_dict.keys():
            state.OptionalTag(name=opt_name, value=optional_tags_dict[opt_name])

        return optional_tags_dict

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
