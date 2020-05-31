import typing
import struct

# TODO: try and turn these classes to enum


class SmppSessionState:
    """
    Represensts the states in which an SMPP session can be in.
    """

    # see section 2.2 of SMPP spec document v3.4
    # we are ignoring the other states since we are only concerning ourselves with an ESME in Transceiver mode.

    # An ESME has established a network connection to the SMSC but has not yet issued a Bind request.
    OPEN: str = "OPEN"
    # A connected ESME has requested to bind as an ESME Transceiver (by issuing a bind_transceiver PDU)
    # and has received a response from the SMSC authorising its Bind request.
    BOUND_TRX: str = "BOUND_TRX"
    # An ESME has unbound from the SMSC and has closed the network connection. The SMSC may also unbind from the ESME.
    CLOSED: str = "CLOSED"


class SmppCommand:
    """
    Represensts the various SMPP commands.
    """

    # see section 4 of SMPP spec document v3.4
    BIND_TRANSCEIVER: str = "bind_transceiver"
    BIND_TRANSCEIVER_RESP: str = "bind_transceiver_resp"
    BIND_TRANSMITTER: str = "bind_transmitter"
    BIND_RECEIVER: str = "bind_receiver"
    UNBIND: str = "unbind"
    UNBIND_RESP: str = "unbind_resp"
    SUBMIT_SM: str = "submit_sm"
    SUBMIT_SM_RESP: str = "submit_sm_resp"
    DELIVER_SM: str = "deliver_sm"
    DELIVER_SM_RESP: str = "deliver_sm_resp"
    ENQUIRE_LINK: str = "enquire_link"
    ENQUIRE_LINK_RESP: str = "enquire_link_resp"
    GENERIC_NACK: str = "generic_nack"

    # naz currently does not handle the following smpp commands.
    # open a github issue if you use naz and require support of a command in this list
    BIND_RECEIVER_RESP: str = "bind_receiver_resp"
    BIND_TRANSMITTER_RESP: str = "bind_transmitter_resp"
    QUERY_SM: str = "query_sm"
    QUERY_SM_RESP: str = "query_sm_resp"
    REPLACE_SM: str = "replace_sm"
    REPLACE_SM_RESP: str = "replace_sm_resp"
    CANCEL_SM: str = "cancel_sm"
    CANCEL_SM_RESP: str = "cancel_sm_resp"
    SUBMIT_MULTI: str = "submit_multi"
    SUBMIT_MULTI_RESP: str = "submit_multi_resp"
    OUTBIND: str = "outbind"
    ALERT_NOTIFICATION: str = "alert_notification"
    DATA_SM: str = "data_sm"
    DATA_SM_RESP: str = "data_sm_resp"
    RESERVED_A: str = "reserved_a"
    RESERVED_B: str = "reserved_b"
    RESERVED_C: str = "reserved_c"
    RESERVED_D: str = "reserved_d"
    RESERVED_E: str = "reserved_e"
    RESERVED_F: str = "reserved_f"
    RESERVED_G: str = "reserved_g"
    RESERVED_LIST_A: str = "reserved_list_a"
    RESERVED_LIST_B: str = "reserved_list_b"
    RESERVED_LIST_C: str = "reserved_list_c"
    RESERVED_LIST_D: str = "reserved_list_d"
    RESERVED_LIST_E: str = "reserved_list_e"
    RESERVED_LIST_F: str = "reserved_list_f"
    RESERVED_LIST_G: str = "reserved_list_g"
    RESERVED_LIST_H: str = "reserved_list_h"
    RESERVED_LIST_I: str = "reserved_list_i"
    RESERVED_FOR_SMPP_EXTENSION_A: str = "reserved_for_smpp_extension_a"
    RESERVED_FOR_SMPP_EXTENSION_B: str = "reserved_for_smpp_extension_b"
    RESERVED_FOR_SMSC_VENDOR_A: str = "reserved_for_smsc_vendor_a"
    RESERVED_FOR_SMSC_VENDOR_B: str = "reserved_for_smsc_vendor_b"


class CommandStatus(typing.NamedTuple):
    """
    An SMPP command status
    """

    code: str
    value: typing.Union[int, typing.List[int]]
    description: str


class SmppCommandStatus:
    """
    Represensts the various SMPP commands statuses.
    """

    # see section 5.1.3 of smpp ver 3.4 spec document

    ESME_ROK: CommandStatus = CommandStatus(
        code="ESME_ROK", value=0x00000000, description="Success"
    )
    ESME_RINVMSGLEN: CommandStatus = CommandStatus(
        code="ESME_RINVMSGLEN", value=0x00000001, description="Message Length is invalid"
    )
    ESME_RINVCMDLEN: CommandStatus = CommandStatus(
        code="ESME_RINVCMDLEN", value=0x00000002, description="Command Length is invalid"
    )
    ESME_RINVCMDID: CommandStatus = CommandStatus(
        code="ESME_RINVCMDID", value=0x00000003, description="Invalid Command ID"
    )
    ESME_RINVBNDSTS: CommandStatus = CommandStatus(
        code="ESME_RINVBNDSTS",
        value=0x00000004,
        description="Incorrect BIND Status for given command",
    )
    ESME_RALYBND: CommandStatus = CommandStatus(
        code="ESME_RALYBND", value=0x00000005, description="ESME Already in Bound State"
    )
    ESME_RINVPRTFLG: CommandStatus = CommandStatus(
        code="ESME_RINVPRTFLG", value=0x00000006, description="Invalid Priority Flag"
    )
    ESME_RINVREGDLVFLG: CommandStatus = CommandStatus(
        code="ESME_RINVREGDLVFLG", value=0x00000007, description="Invalid Registered Delivery Flag"
    )
    ESME_RSYSERR: CommandStatus = CommandStatus(
        code="ESME_RSYSERR", value=0x00000008, description="System Error"
    )
    ESME_RINVSRCADR: CommandStatus = CommandStatus(
        code="ESME_RINVSRCADR", value=0x0000000A, description="Invalid Source Address"
    )
    ESME_RINVDSTADR: CommandStatus = CommandStatus(
        code="ESME_RINVDSTADR", value=0x0000000B, description="Invalid Dest Addr"
    )
    ESME_RINVMSGID: CommandStatus = CommandStatus(
        code="ESME_RINVMSGID", value=0x0000000C, description="Message ID is invalid"
    )
    ESME_RBINDFAIL: CommandStatus = CommandStatus(
        code="ESME_RBINDFAIL", value=0x0000000D, description="Bind Failed"
    )
    ESME_RINVPASWD: CommandStatus = CommandStatus(
        code="ESME_RINVPASWD", value=0x0000000E, description="Invalid Password"
    )
    ESME_RINVSYSID: CommandStatus = CommandStatus(
        code="ESME_RINVSYSID", value=0x0000000F, description="Invalid System ID"
    )
    ESME_RCANCELFAIL: CommandStatus = CommandStatus(
        code="ESME_RCANCELFAIL", value=0x00000011, description="Cancel SM Failed"
    )
    ESME_RREPLACEFAIL: CommandStatus = CommandStatus(
        code="ESME_RREPLACEFAIL", value=0x00000013, description="Replace SM Failed"
    )
    ESME_RMSGQFUL: CommandStatus = CommandStatus(
        code="ESME_RMSGQFUL", value=0x00000014, description="Message Broker Full"
    )
    ESME_RINVSERTYP: CommandStatus = CommandStatus(
        code="ESME_RINVSERTYP", value=0x00000015, description="Invalid Service Type"
    )
    ESME_RINVNUMDESTS: CommandStatus = CommandStatus(
        code="ESME_RINVNUMDESTS", value=0x00000033, description="Invalid number of destinations"
    )
    ESME_RINVDLNAME: CommandStatus = CommandStatus(
        code="ESME_RINVNUMDESTS", value=0x00000034, description="Invalid Distribution List name"
    )
    ESME_RINVDESTFLAG: CommandStatus = CommandStatus(
        code="ESME_RINVDESTFLAG",
        value=0x00000040,
        description="Destination flag is invalid (submit_multi)",
    )
    ESME_RINVSUBREP: CommandStatus = CommandStatus(
        code="ESME_RINVSUBREP",
        value=0x00000042,
        description="Invalid (submit with replace) request(i.e. submit_sm with replace_if_present_flag set)",
    )
    ESME_RINVESMCLASS: CommandStatus = CommandStatus(
        code="ESME_RINVESMCLASS", value=0x00000043, description="Invalid esm_class field data"
    )
    ESME_RCNTSUBDL: CommandStatus = CommandStatus(
        code="ESME_RCNTSUBDL", value=0x00000044, description="Cannot Submit to Distribution List"
    )
    ESME_RSUBMITFAIL: CommandStatus = CommandStatus(
        code="ESME_RSUBMITFAIL", value=0x00000045, description="Submit_sm or submit_multi failed"
    )
    ESME_RINVSRCTON: CommandStatus = CommandStatus(
        code="ESME_RINVSRCTON", value=0x00000048, description="Invalid Source address TON"
    )
    ESME_RINVSRCNPI: CommandStatus = CommandStatus(
        code="ESME_RINVSRCNPI", value=0x00000049, description="Invalid Source address NPI"
    )
    ESME_RINVDSTTON: CommandStatus = CommandStatus(
        code="ESME_RINVDSTTON", value=0x00000050, description="Invalid Destination address TON"
    )
    ESME_RINVDSTNPI: CommandStatus = CommandStatus(
        code="ESME_RINVDSTNPI", value=0x00000051, description="Invalid Destination address NPI"
    )
    ESME_RINVSYSTYP: CommandStatus = CommandStatus(
        code="ESME_RINVSYSTYP", value=0x00000053, description="Invalid system_type field"
    )
    ESME_RINVREPFLAG: CommandStatus = CommandStatus(
        code="ESME_RINVREPFLAG", value=0x00000054, description="Invalid replace_if_present flag"
    )
    ESME_RINVNUMMSGS: CommandStatus = CommandStatus(
        code="ESME_RINVNUMMSGS", value=0x00000055, description="Invalid number of messages"
    )
    ESME_RTHROTTLED: CommandStatus = CommandStatus(
        code="ESME_RTHROTTLED",
        value=0x00000058,
        description="Throttling error (ESME has exceeded allowed message limits)",
    )
    ESME_RINVSCHED: CommandStatus = CommandStatus(
        code="ESME_RINVSCHED", value=0x00000061, description="Invalid Scheduled Delivery Time"
    )
    ESME_RINVEXPIRY: CommandStatus = CommandStatus(
        code="ESME_RINVEXPIRY",
        value=0x00000062,
        description="Invalid message validity period (Expiry time)",
    )
    ESME_RINVDFTMSGID: CommandStatus = CommandStatus(
        code="ESME_RINVDFTMSGID",
        value=0x00000063,
        description="Predefined Message Invalid or Not Found",
    )
    ESME_RX_T_APPN: CommandStatus = CommandStatus(
        code="ESME_RX_T_APPN",
        value=0x00000064,
        description="ESME Receiver Temporary App Error Code",
    )
    ESME_RX_P_APPN: CommandStatus = CommandStatus(
        code="ESME_RX_P_APPN",
        value=0x00000065,
        description="ESME Receiver Permanent App Error Code",
    )
    ESME_RX_R_APPN: CommandStatus = CommandStatus(
        code="ESME_RX_R_APPN",
        value=0x00000066,
        description="ESME Receiver Reject Message Error Code",
    )
    ESME_RQUERYFAIL: CommandStatus = CommandStatus(
        code="ESME_RQUERYFAIL", value=0x00000067, description="query_sm request failed"
    )
    ESME_RINVOPTPARSTREAM: CommandStatus = CommandStatus(
        code="ESME_RINVOPTPARSTREAM",
        value=0x000000C0,
        description="Error in the optional part of the PDU Body.",
    )
    ESME_ROPTPARNOTALLWD: CommandStatus = CommandStatus(
        code="ESME_ROPTPARNOTALLWD", value=0x000000C1, description="Optional Parameter not allowed"
    )
    ESME_RINVPARLEN: CommandStatus = CommandStatus(
        code="ESME_RINVPARLEN", value=0x000000C2, description="Invalid Parameter Length."
    )
    ESME_RMISSINGOPTPARAM: CommandStatus = CommandStatus(
        code="ESME_RMISSINGOPTPARAM",
        value=0x000000C3,
        description="Expected Optional Parameter missing",
    )
    ESME_RINVOPTPARAMVAL: CommandStatus = CommandStatus(
        code="ESME_RINVOPTPARAMVAL",
        value=0x000000C4,
        description="Invalid Optional Parameter Value",
    )

    ESME_RDELIVERYFAILURE: CommandStatus = CommandStatus(
        code="ESME_RDELIVERYFAILURE",
        value=0x000000FE,
        description="Delivery Failure (used for data_sm_resp)",
    )
    ESME_RUNKNOWNERR: CommandStatus = CommandStatus(
        code="ESME_RUNKNOWNERR", value=0x000000FF, description="Unknown Error"
    )
    RESERVED_A: CommandStatus = CommandStatus(
        code="Reserved", value=0x00000009, description="Reserved"
    )
    RESERVED_B: CommandStatus = CommandStatus(
        code="Reserved", value=0x00000010, description="Reserved"
    )
    RESERVED_C: CommandStatus = CommandStatus(
        code="Reserved", value=0x00000012, description="Reserved"
    )
    RESERVED_D: CommandStatus = CommandStatus(
        code="Reserved", value=0x00000041, description="Reserved"
    )
    RESERVED_E: CommandStatus = CommandStatus(
        code="Reserved", value=0x00000052, description="Reserved"
    )
    RESERVED_LIST_A: CommandStatus = CommandStatus(
        code="Reserved", value=[0x00000016, 0x00000032], description="Reserved"
    )
    RESERVED_LIST_B: CommandStatus = CommandStatus(
        code="Reserved", value=[0x00000035, 0x0000003F], description="Reserved"
    )
    RESERVED_LIST_C: CommandStatus = CommandStatus(
        code="Reserved", value=[0x00000046, 0x00000047], description="Reserved"
    )
    RESERVED_LIST_D: CommandStatus = CommandStatus(
        code="Reserved", value=[0x00000056, 0x00000057], description="Reserved"
    )
    RESERVED_LIST_E: CommandStatus = CommandStatus(
        code="Reserved", value=[0x00000059, 0x00000060], description="Reserved"
    )
    RESERVED_LIST_F: CommandStatus = CommandStatus(
        code="Reserved", value=[0x00000068, 0x000000BF], description="Reserved"
    )
    RESERVED_LIST_G: CommandStatus = CommandStatus(
        code="Reserved", value=[0x000000C5, 0x000000FD], description="Reserved"
    )
    RESERVED_LIST_H: CommandStatus = CommandStatus(
        code="Reserved", value=[0x00000100, 0x000003FF], description="Reserved for SMPP extension"
    )
    RESERVED_LIST_I: CommandStatus = CommandStatus(
        code="Reserved",
        value=[0x00000400, 0x000004FF],
        description="Reserved for SMSC vendor specific errors",
    )
    RESERVED_LIST_J: CommandStatus = CommandStatus(
        code="Reserved", value=[0x00000500, 0xFFFFFFFF], description="Reserved"
    )


class DataCoding(typing.NamedTuple):
    """
    An SMPP data encoding.
    """

    code: str
    value: int
    description: str


class SmppDataCoding:
    """
    Represensts the various SMPP data encodings.
    """

    # see section 5.2.19 of smpp ver 3.4 spec document.
    # also see:
    #   1. https://github.com/praekelt/vumi/blob/767eac623c81cc4b2e6ea9fbd6a3645f121ef0aa/vumi/transports/smpp/processors/default.py#L260
    #   2. https://docs.python.org/3/library/codecs.html
    #   3. https://docs.python.org/3/library/codecs.html#standard-encodings

    # The attributes of this class are equivalent to some of the names found in the python standard-encodings documentation
    # We cant use all python standard encodings[1]
    # We can only use the ones defined in SMPP spec[2];
    #
    # 1. https://docs.python.org/3/library/codecs.html#standard-encodings
    # 2. section 5.2.19 of smpp ver 3.4 spec document.

    gsm0338: DataCoding = DataCoding(
        code="gsm0338", value=0b00000000, description="SMSC Default Alphabet"
    )
    ascii: DataCoding = DataCoding(
        code="ascii", value=0b00000001, description="IA5(CCITT T.50) / ASCII(ANSI X3.4)"
    )
    octet_unspecified_I: DataCoding = DataCoding(
        code="octet_unspecified_I",
        value=0b00000010,
        description="Octet unspecified(8 - bit binary)",
    )
    latin_1: DataCoding = DataCoding(
        code="latin_1", value=0b00000011, description="Latin 1 (ISO - 8859 - 1)"
    )
    octet_unspecified_II: DataCoding = DataCoding(
        code="octet_unspecified_II",
        value=0b00000100,
        description="Octet unspecified(8 - bit binary)",
    )
    # iso2022_jp, iso2022jp and iso-2022-jp are aliases
    # see: https://stackoverflow.com/a/43240579/2768067
    iso2022_jp: DataCoding = DataCoding(
        code="iso2022_jp", value=0b00000101, description="JIS(X 0208 - 1990)"
    )
    iso8859_5: DataCoding = DataCoding(
        code="iso8859_5", value=0b00000110, description="Cyrllic(ISO - 8859 - 5)"
    )
    iso8859_8: DataCoding = DataCoding(
        code="iso8859_8", value=0b00000111, description="Latin / Hebrew(ISO - 8859 - 8)"
    )
    # see: https://stackoverflow.com/a/14488478/2768067
    utf_16_be: DataCoding = DataCoding(
        code="utf_16_be", value=0b00001000, description="UCS2(ISO / IEC - 10646)"
    )
    ucs2: DataCoding = DataCoding(
        code="ucs2", value=0b00001000, description="UCS2(ISO / IEC - 10646)"
    )
    shift_jis: DataCoding = DataCoding(
        code="shift_jis", value=0b00001001, description="Pictogram Encoding"
    )
    iso2022jp: DataCoding = DataCoding(
        code="iso2022jp", value=0b00001010, description="ISO - 2022 - JP(Music Codes)"
    )
    # reservedI= DataCoding(code="reservedI", value=0b00001011, description= "reserved")
    # reservedII= DataCoding(code="reservedII", value=0b00001100, description= "reserved")
    euc_kr: DataCoding = DataCoding(code="euc_kr", value=0b00001110, description="KS C 5601")

    # not the same as iso2022_jp but ... ¯\_(ツ)_/¯
    # iso-2022-jp=DataCoding(code="iso-2022-jp", value=0b00001101, description="Extended Kanji JIS(X 0212 - 1990)")

    # 00001111 - 10111111 reserved
    # 0b1100xxxx GSM MWI control - see [GSM 03.38]
    # 0b1101xxxx GSM MWI control - see [GSM 03.38]
    # 0b1110xxxx reserved
    # 0b1111xxxx GSM message class control - see [GSM 03.38]

    @staticmethod
    def _find_data_coding(encoding):
        # NB:
        # We cant use all python standard encodings[1]
        # We can only use the ones defined in SMPP spec[2];
        #
        # 1. https://docs.python.org/3/library/codecs.html#standard-encodings
        # 2. section 5.2.19 of smpp ver 3.4 spec document.
        try:
            return SmppDataCoding.__dict__[encoding]
        except Exception as e:
            raise ValueError(
                "That encoding: `{0}` is not a recognised SMPP encoding.".format(encoding)
            ) from e


class OptionalTag:
    """
    An SMPP OptionalTag.

    Optional Parameters MUST always appear at the end of a message, in the `Optional Parameters` section of the SMPP PDU.
    However, they may be included in ANY ORDER within the `Optional Parameters` section of the SMPP PDU
    and NEED NOT be encoded in the order presented in the smpp document.

    see section 5.3.2 of smpp ver 3.4 spec document.
    """

    # see section 5.3.2 of smpp ver 3.4 spec document.
    # All optional parameters have the following general TLV (Tag, Length, Value) format.
    # Tag, Integer, 2octets
    # Length, Integer, 2octets
    # Value, type varies, size varies. eg `receipted_message_id` is of type c-octet string of size 1-65

    # As an example, to represent a `receipted_message_id`, we need;

    # import naz, struct
    # my_receipted_message_id = Tag + Length + Value
    # Tag = naz.OptionalTag.NAME_to_TAG['receipted_message_id']
    # Length = ?
    # Value = "ThisIsSomeMessageId"
    # Value = Value.encode("ascii") + chr(0).encode("ascii") # since it is a c-octet string so it is a series of null-terminated ASCII chars
    # Length = len(Value); assert Length <= 65 # Value is c-octet string of size 1-65
    # my_receipted_message_id = struct.pack(">HH", Tag, Length) + Value # Tag & Length are each Int, 2octet. Ints in smpp are unsigned. Hence use ">H" in struct pack
    # >>> print(my_receipted_message_id)
    # b'\x00\x1e\x00\x14ThisIsSomeMessageId\x00'

    # stores a mapping of optional parameter name to tag
    NAME_to_TAG: typing.Dict[str, int] = dict(
        # dest_addr_subunit: It is used to route messages when received by a mobile station, for example to a smart card in the mobile station
        #                    or to an external device connected to the mobile station.
        dest_addr_subunit=0x0005,
        # dest_network_type: It is used to indicate a network type associated with the destination address of a message.
        dest_network_type=0x0006,
        # dest_bearer_type: It is is used to request the desired bearer for delivery of the message to the destination address.
        dest_bearer_type=0x0007,
        # dest_telematics_id: It defines the telematic interworking to be used by the delivering system for the destination address.
        dest_telematics_id=0x0008,
        # source_addr_subunit: It is used to indicate where a message originated in the mobile station,
        #                      for example a smart card in the mobile station or an external device connected to the mobile station.
        source_addr_subunit=0x000D,
        # source_network_type: It is used to indicate the network type associated with the device that originated the message.
        source_network_type=0x000E,
        # source_bearer_type: It indicates the wireless bearer over which the message originated.
        source_bearer_type=0x000F,
        # source_telematics_id: It indicates the type of telematics interface over which the message originated.
        source_telematics_id=0x0010,
        # qos_time_to_live: It defines the number of seconds which the sender requests the SMSC to keep the message if undelivered
        #                   before it is deemed expired and not worth delivering.
        qos_time_to_live=0x0017,
        # payload_type: It defines the higher layer PDU type contained in the message payload.
        payload_type=0x0019,
        # additional_status_info_text: It gives an ASCII textual description of the meaning of a response PDU.
        additional_status_info_text=0x001D,
        # receipted_message_id: It indicates the ID of the message being receipted in an SMSC Delivery Receipt.
        receipted_message_id=0x001E,
        # ms_msg_wait_facilities: It allows an indication to be provided to an MS that there are messages waiting for the subscriber on systems on the PLMN.
        ms_msg_wait_facilities=0x0030,
        # privacy_indicator: It indicates the privacy level of the message.
        privacy_indicator=0x0201,
        # source_subaddress: It specifies a subaddress associated with the originator of the message.
        source_subaddress=0x0202,
        # dest_subaddress: It specifies a subaddress associated with the destination of the message.
        dest_subaddress=0x0203,
        # user_message_reference: ESME assigned message reference number.
        user_message_reference=0x0204,
        # user_response_code: It is a response code set by the user in a User Acknowledgement/Reply message.
        user_response_code=0x0205,
        # source_port: It is used to indicate the application port number associated with the source address of the message
        source_port=0x020A,
        # destination_port: It is used to indicate the application port number associated with the destination address of the message.
        destination_port=0x020B,
        # sar_msg_ref_num: It is used to indicate the reference number for a particular concatenated short message.
        sar_msg_ref_num=0x020C,
        # language_indicator: It is used to indicate the language of the short message.
        language_indicator=0x020D,
        # sar_total_segments: It is used to indicate the total number of short messages within the concatenated short message.
        sar_total_segments=0x020E,
        # sar_segment_seqnum: It is used to indicate the sequence number of a particular short message within the concatenated short message.
        sar_segment_seqnum=0x020F,
        # sc_interface_version: It is used to indicate the SMPP version supported by the SMSC. It is returned in the bind response PDUs.
        sc_interface_version=0x0210,
        # callback_num_pres_ind: It controls the presentation indication and screening of the callback number at the mobile station.
        #                        If present, the :py:attr:`~callback_num` parameter must also be present.
        callback_num_pres_ind=0x0302,
        # callback_num_atag: It associates an alphanumeric display with the call back number
        callback_num_atag=0x0303,
        # number_of_messages: It is used to indicate the number of messages stored in a mailbox.
        number_of_messages=0x0304,
        # callback_num: It associates a call back number with the message.
        callback_num=0x0381,
        # dpf_result: It is used in the data_sm_resp PDU to indicate if delivery pending flag (DPF) was set for a delivery failure of the short message.
        dpf_result=0x0420,
        # set_dpf: An ESME may use the set_dpf parameter to request the setting of a delivery pending flag (DPF) for certain delivery failure scenarios
        set_dpf=0x0421,
        # ms_availability_status: It is used in the alert_notification operation to indicate the availability state of the MS to the ESME.
        ms_availability_status=0x0422,
        # network_error_code: It is used to indicate the actual network error code for a delivery failure.
        network_error_code=0x0423,
        # message_payload: It contains the user data.
        message_payload=0x0424,
        # delivery_failure_reason: It is used in the data_sm_resp operation to indicate the outcome of the message delivery attempt
        #                          (only applicable for transaction message mode).
        delivery_failure_reason=0x0425,
        # more_messages_to_send: It is used by the ESME in the `submit_sm` and `data_sm` operations to indicate to the SMSC
        #                        that there are further messages for the same destination SME.
        more_messages_to_send=0x0426,
        # message_state: It is used by the SMSC in the deliver_sm and data_sm PDUs to indicate to the ESME the final message state for an SMSC Delivery Receipt.
        message_state=0x0427,
        # ussd_service_op: It is required to define the USSD service operation when SMPP is being used as an interface to a (GSM) USSD system.
        ussd_service_op=0x0501,
        # display_time: It is used to associate a display time of the short message on the MS.
        display_time=0x1201,
        # sms_signal: It is used to provide a TDMA MS with alert tone information associated with the received short message.
        sms_signal=0x1203,
        # ms_validity: It is used to provide an MS with validity information associated with the received short message.
        ms_validity=0x1204,
        # alert_on_message_delivery: It is set to instruct a MS to alert the user (in a MS implementation specific manner) when the short message arrives at the MS.
        alert_on_message_delivery=0x130C,
        # its_reply_type: It indicates and controls the MS user's reply method to an SMS delivery message received from the ESME.
        #                 It is a required parameter for the CDMA Interactive Teleservice as defined by the Korean PCS carriers [KORITS].
        its_reply_type=0x1380,
        # its_session_info: It contains control information for the interactive session between an MS and an ESME.
        #                   It is a required parameter for the CDMA Interactive Teleservice as defined by the Korean PCS carriers [KORITS].
        its_session_info=0x1383,
    )

    def __init__(self, name: str, value: typing.Union[int, str, bool]) -> None:
        """
        Parameters:
            name: the name of the SMPP optional parameter.
            value: the value of the parameter
        """
        self._validate_args(name=name, value=value)

        self.name = name
        self._value = value

    @staticmethod
    def _validate_args(name: str, value: typing.Union[int, str, bool],) -> None:
        if name not in OptionalTag.NAME_to_TAG.keys():
            raise ValueError(
                "The OptionalTag with name `{0}` is not a recognised SMPP OptionalTag.".format(name)
            )

        if name in (
            "dest_addr_subunit",
            "dest_network_type",
            "dest_bearer_type",
            "dest_telematics_id",
            "source_addr_subunit",
            "source_network_type",
            "source_bearer_type",
            "source_telematics_id",
            "qos_time_to_live",
            "payload_type",
            # the type of `ms_msg_wait_facilities` is a bitMask. but it is treated as an int
            "ms_msg_wait_facilities",
            "privacy_indicator",
            "user_message_reference",
            "user_response_code",
            "source_port",
            "destination_port",
            "sar_msg_ref_num",
            "language_indicator",
            "sar_total_segments",
            "sar_segment_seqnum",
            "sc_interface_version",
            "callback_num_pres_ind",
            "number_of_messages",
            "dpf_result",
            "set_dpf",
            "ms_availability_status",
            "delivery_failure_reason",
            "more_messages_to_send",
            "message_state",
            "display_time",
            "sms_signal",
            "ms_validity",
            "its_reply_type",
        ) and not isinstance(value, int):
            raise ValueError(
                "`{0}` should be of type:: `int` You entered: {1}".format(name, type(value))
            )
        elif name in (
            "additional_status_info_text",
            "receipted_message_id",
            "source_subaddress",
            "dest_subaddress",
            "callback_num_atag",
            "callback_num",
            "network_error_code",
            "message_payload",
            "ussd_service_op",
            "its_session_info",
        ) and not isinstance(value, str):
            raise ValueError(
                "`{0}` should be of type:: `str` You entered: {1}".format(name, type(value))
            )
        elif name in ("alert_on_message_delivery",) and not isinstance(value, bool):
            # note that in smpp, `alert_on_message_delivery` has no value part in TLV
            # but in naz we just use boolean to indicate whether someone wants to set it.
            raise ValueError(
                "`{0}` should be of type:: `bool` You entered: {1}".format(name, type(value))
            )

    @property
    def tag(self) -> int:
        """
        Returns the Tag field of an optional smpp parameter.
        The Tag field is used to uniquely identify the particular optional parameter in question.
        """
        return self.NAME_to_TAG[self.name]

    @property
    def value(self) -> typing.Union[int, str, bool]:
        """
        Returns the Value field of an optional smpp parameter.
        The Value field contains the actual data for the optional parameter in question.
        """
        return self._value

    @property
    def length(self) -> int:
        """
        Returns the Value field of an optional smpp parameter.
        The Length field indicates the length of the Value field in octets(integer).
        """
        if self.name in (
            "dest_addr_subunit",
            "dest_network_type",
            "dest_bearer_type",
            "source_addr_subunit",
            "source_network_type",
            "source_bearer_type",
            "source_telematics_id",
            "payload_type",
            "ms_msg_wait_facilities",
            "privacy_indicator",
            "user_response_code",
            "language_indicator",
            "sar_total_segments",
            "sar_segment_seqnum",
            "sc_interface_version",
            "callback_num_pres_ind",
            "number_of_messages",
            "dpf_result",
            "set_dpf",
            "ms_availability_status",
            "delivery_failure_reason",
            "more_messages_to_send",
            "message_state",
            "display_time",
            "ms_validity",
            "its_reply_type",
        ):
            # This is for unsigned ints size 1
            # smpp doc says: "Length of value part in octets".
            return 1
        elif self.name in (
            "dest_telematics_id",
            "user_message_reference",
            "source_port",
            "destination_port",
            "sar_msg_ref_num",
            "sms_signal",
        ):
            return 2
        elif self.name in ("qos_time_to_live",):
            # This is for unsigned ints size 4
            return 4
        elif self.name in (
            "additional_status_info_text",
            "receipted_message_id",
            "source_subaddress",
            "dest_subaddress",
            "callback_num_atag",
            "callback_num",
            "network_error_code",
            "message_payload",
            "ussd_service_op",
            "its_session_info",
        ):
            # make mypy happy; https://github.com/python/mypy/issues/4805
            assert isinstance(self.value, str)
            return len(self.value)
        elif self.name in ("alert_on_message_delivery",):
            # see section 5.3.2.41 of smpp document
            return 0
        else:
            raise ValueError(
                "The OptionalTag with name `{0}` is not a recognised SMPP OptionalTag.".format(
                    self.name
                )
            )

    @property
    def tlv(self) -> bytes:
        """
        Returns the bytes representation of an optional smpp parameter.
        """
        if self.name in (
            "dest_addr_subunit",
            "dest_network_type",
            "dest_bearer_type",
            "source_addr_subunit",
            "source_network_type",
            "source_bearer_type",
            "source_telematics_id",
            "payload_type",
            "ms_msg_wait_facilities",
            "privacy_indicator",
            "user_response_code",
            "language_indicator",
            "sar_total_segments",
            "sar_segment_seqnum",
            "sc_interface_version",
            "callback_num_pres_ind",
            "number_of_messages",
            "dpf_result",
            "set_dpf",
            "ms_availability_status",
            "delivery_failure_reason",
            "more_messages_to_send",
            "message_state",
            "display_time",
            "ms_validity",
            "its_reply_type",
        ):
            # This is for unsigned ints size 1
            # B is for `unsigned char size 1`, H is for `unsigned short size 2` and I is  `unsigned int size 4`
            # see: https://docs.python.org/3.8/library/struct.html#format-characters
            return struct.pack(">HHB", self.tag, self.length, self.value)
        elif self.name in (
            "dest_telematics_id",
            "user_message_reference",
            "source_port",
            "destination_port",
            "sar_msg_ref_num",
            "sms_signal",
        ):
            # This is for unsigned ints size 2
            return struct.pack(">HHH", self.tag, self.length, self.value)
        elif self.name in ("qos_time_to_live",):
            # This is for unsigned ints size 4
            return struct.pack(">HHI", self.tag, self.length, self.value)
        elif self.name in (
            "additional_status_info_text",
            "receipted_message_id",
            "source_subaddress",
            "dest_subaddress",
            "callback_num_atag",
            "callback_num",
            "network_error_code",
            "message_payload",
            "ussd_service_op",
            "its_session_info",
        ):
            # make mypy happy; https://github.com/python/mypy/issues/4805
            assert isinstance(self.value, str)
            _val = self.value.encode("ascii") + chr(0).encode("ascii")
            return struct.pack(">HH", self.tag, self.length) + _val
        elif self.name in ("alert_on_message_delivery",):
            if self.value:
                # the TLV has no value field
                return struct.pack(">HH", self.tag, self.length)
            else:
                return b""
        else:
            raise ValueError(
                "The OptionalTag with name `{0}` is not a recognised SMPP OptionalTag.".format(
                    self.name
                )
            )
