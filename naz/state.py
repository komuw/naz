import typing


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
    UNBIND: str = "unbind"
    UNBIND_RESP: str = "unbind_resp"
    SUBMIT_SM: str = "submit_sm"
    SUBMIT_SM_RESP: str = "submit_sm_resp"
    DELIVER_SM: str = "deliver_sm"
    DELIVER_SM_RESP: str = "deliver_sm_resp"
    ENQUIRE_LINK: str = "enquire_link"
    ENQUIRE_LINK_RESP: str = "enquire_link_resp"
    GENERIC_NACK: str = "generic_nack"


class CommandStatus(typing.NamedTuple):
    """
    An SMPP command status
    """

    code: str
    value: int
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
    # Reserved =  CommandStatus(code="Reserved", value=0x00000009,description= "Reserved")
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
    # Reserved =  CommandStatus(code="Reserved", value=0x00000010,description= "Reserved")
    ESME_RCANCELFAIL: CommandStatus = CommandStatus(
        code="ESME_RCANCELFAIL", value=0x00000011, description="Cancel SM Failed"
    )
    # Reserved =  CommandStatus(code="Reserved", value=0x00000012,description= "Reserved")
    ESME_RREPLACEFAIL: CommandStatus = CommandStatus(
        code="ESME_RREPLACEFAIL", value=0x00000013, description="Replace SM Failed"
    )
    ESME_RMSGQFUL: CommandStatus = CommandStatus(
        code="ESME_RMSGQFUL", value=0x00000014, description="Message Queue Full"
    )
    ESME_RINVSERTYP: CommandStatus = CommandStatus(
        code="ESME_RINVSERTYP", value=0x00000015, description="Invalid Service Type"
    )
    # Reserved 0x00000016 - 0x00000032 Reserved
    ESME_RINVNUMDESTS: CommandStatus = CommandStatus(
        code="ESME_RINVNUMDESTS", value=0x00000033, description="Invalid number of destinations"
    )
    ESME_RINVDLNAME: CommandStatus = CommandStatus(
        code="ESME_RINVNUMDESTS", value=0x00000034, description="Invalid Distribution List name"
    )
    # Reserved 0x00000035 - 0x0000003F Reserved
    ESME_RINVDESTFLAG: CommandStatus = CommandStatus(
        code="ESME_RINVDESTFLAG",
        value=0x00000040,
        description="Destination flag is invalid (submit_multi)",
    )
    # Reserved =  CommandStatus(code="Reserved", value=0x00000041,description= "Reserved")
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
    # Reserved 0x00000046 - 0x00000047 Reserved
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
    # Reserved =  CommandStatus(code="Reserved", value=0x00000052,description= "Reserved")
    ESME_RINVSYSTYP: CommandStatus = CommandStatus(
        code="ESME_RINVSYSTYP", value=0x00000053, description="Invalid system_type field"
    )
    ESME_RINVREPFLAG: CommandStatus = CommandStatus(
        code="ESME_RINVREPFLAG", value=0x00000054, description="Invalid replace_if_present flag"
    )
    ESME_RINVNUMMSGS: CommandStatus = CommandStatus(
        code="ESME_RINVNUMMSGS", value=0x00000055, description="Invalid number of messages"
    )
    # Reserved 0x00000056 - 0x00000057 Reserved
    ESME_RTHROTTLED: CommandStatus = CommandStatus(
        code="ESME_RTHROTTLED",
        value=0x00000058,
        description="Throttling error (ESME has exceeded allowed message limits)",
    )
    # Reserved 0x00000059 - 0x00000060 Reserved
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
    # Reserved 0x00000068 - 0x000000BF Reserved
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
    # Reserved 0x000000C5 - 0x000000FD Reserved
    ESME_RDELIVERYFAILURE: CommandStatus = CommandStatus(
        code="ESME_RDELIVERYFAILURE",
        value=0x000000FE,
        description="Delivery Failure (used for data_sm_resp)",
    )
    ESME_RUNKNOWNERR: CommandStatus = CommandStatus(
        code="ESME_RUNKNOWNERR", value=0x000000FF, description="Unknown Error"
    )
    # Reserved for SMPP extension 0x00000100 - 0x000003FF Reserved for SMPP extension
    # Reserved for SMSC vendor specific errors 0x00000400 - 0x000004FF Reserved for SMSC vendor specific errors
    # Reserved 0x00000500 - 0xFFFFFFFF Reserved


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
    # ie; https://docs.python.org/3/library/codecs.html#standard-encodings

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
