optional_parameter_tag_by_hex = {
    "0005": {
        "hex": "0005",
        "name": "dest_addr_subunit",
        "type": "integer",
        "tech": "GSM",
    },  # SMPP v3.4, section 5.3.2.1, page 134
    "0006": {
        "hex": "0006",
        "name": "dest_network_type",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.3, page 135
    "0007": {
        "hex": "0007",
        "name": "dest_bearer_type",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.5, page 136
    "0008": {
        "hex": "0008",
        "name": "dest_telematics_id",
        "type": "integer",
        "tech": "GSM",
        "min": 2,
    },  # SMPP v3.4, section 5.3.2.7, page 137
    "000d": {
        "hex": "000d",
        "name": "source_addr_subunit",
        "type": "integer",
        "tech": "GSM",
    },  # SMPP v3.4, section 5.3.2.2, page 134
    "000e": {
        "hex": "000e",
        "name": "source_network_type",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.4, page 135
    "000f": {
        "hex": "000f",
        "name": "source_bearer_type",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.6, page 136
    "0010": {
        "hex": "0010",
        "name": "source_telematics_id",
        "type": "integer",
        "tech": "GSM",
    },  # SMPP v3.4, section 5.3.2.8, page 137
    "0017": {
        "hex": "0017",
        "name": "qos_time_to_live",
        "type": "integer",
        "tech": "Generic",
        "min": 4,
    },  # SMPP v3.4, section 5.3.2.9, page 138
    "0019": {
        "hex": "0019",
        "name": "payload_type",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.10, page 138
    "001d": {
        "hex": "001d",
        "name": "additional_status_info_text",
        "type": "string",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.11, page 139
    "001e": {
        "hex": "001e",
        "name": "receipted_message_id",
        "type": "string",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.12, page 139
    "0030": {
        "hex": "0030",
        "name": "ms_msg_wait_facilities",
        "type": "bitmask",
        "tech": "GSM",
    },  # SMPP v3.4, section 5.3.2.13, page 140
    "0101": {
        "hex": "0101",
        "name": "PVCY_AuthenticationStr",
        "type": None,
        "tech": "? (J-Phone)",
    },  # v4 page 58-62
    "0201": {
        "hex": "0201",
        "name": "privacy_indicator",
        "type": "integer",
        "tech": "CDMA, TDMA",
    },  # SMPP v3.4, section 5.3.2.14, page 141
    "0202": {
        "hex": "0202",
        "name": "source_subaddress",
        "type": "hex",
        "tech": "CDMA, TDMA",
        "min": 2,
    },  # SMPP v3.4, section 5.3.2.15, page 142
    "0203": {
        "hex": "0203",
        "name": "dest_subaddress",
        "type": "hex",
        "tech": "CDMA, TDMA",
        "min": 2,
    },  # SMPP v3.4, section 5.3.2.16, page 143
    "0204": {
        "hex": "0204",
        "name": "user_message_reference",
        "type": "integer",
        "tech": "Generic",
        "min": 2,
    },  # SMPP v3.4, section 5.3.2.17, page 143
    "0205": {
        "hex": "0205",
        "name": "user_response_code",
        "type": "integer",
        "tech": "CDMA, TDMA",
    },  # SMPP v3.4, section 5.3.2.18, page 144
    "020a": {
        "hex": "020a",
        "name": "source_port",
        "type": "integer",
        "tech": "Generic",
        "min": 2,
    },  # SMPP v3.4, section 5.3.2.20, page 145
    "020b": {
        "hex": "020b",
        "name": "destination_port",
        "type": "integer",
        "tech": "Generic",
        "min": 2,
    },  # SMPP v3.4, section 5.3.2.21, page 145
    "020c": {
        "hex": "020c",
        "name": "sar_msg_ref_num",
        "type": "integer",
        "tech": "Generic",
        "min": 2,
    },  # SMPP v3.4, section 5.3.2.22, page 146
    "020d": {
        "hex": "020d",
        "name": "language_indicator",
        "type": "integer",
        "tech": "CDMA, TDMA",
    },  # SMPP v3.4, section 5.3.2.19, page 144
    "020e": {
        "hex": "020e",
        "name": "sar_total_segments",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.23, page 147
    "020f": {
        "hex": "020f",
        "name": "sar_segment_seqnum",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.24, page 147
    "0210": {
        "hex": "0210",
        "name": "sc_interface_version",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.25, page 148
    "0301": {"hex": "0301", "name": "CC_CBN", "type": None, "tech": "V4"},  # v4 page 70
    "0302": {
        "hex": "0302",
        "name": "callback_num_pres_ind",
        "type": "bitmask",
        "tech": "TDMA",
    },  # SMPP v3.4, section 5.3.2.37, page 156
    "0303": {
        "hex": "0303",
        "name": "callback_num_atag",
        "type": "hex",
        "tech": "TDMA",
    },  # SMPP v3.4, section 5.3.2.38, page 157
    "0304": {
        "hex": "0304",
        "name": "number_of_messages",
        "type": "integer",
        "tech": "CDMA",
    },  # SMPP v3.4, section 5.3.2.39, page 158
    "0381": {
        "hex": "0381",
        "name": "callback_num",
        "type": "hex",
        "tech": "CDMA, TDMA, GSM, iDEN",
        "min": 4,
    },  # SMPP v3.4, section 5.3.2.36, page 155
    "0420": {
        "hex": "0420",
        "name": "dpf_result",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.28, page 149
    "0421": {
        "hex": "0421",
        "name": "set_dpf",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.29, page 150
    "0422": {
        "hex": "0422",
        "name": "ms_availability_status",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.30, page 151
    "0423": {
        "hex": "0423",
        "name": "network_error_code",
        "type": "hex",
        "tech": "Generic",
        "min": 3,
    },  # SMPP v3.4, section 5.3.2.31, page 152
    "0424": {
        "hex": "0424",
        "name": "message_payload",
        "type": "hex",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.32, page 153
    "0425": {
        "hex": "0425",
        "name": "delivery_failure_reason",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.33, page 153
    "0426": {
        "hex": "0426",
        "name": "more_messages_to_send",
        "type": "integer",
        "tech": "GSM",
    },  # SMPP v3.4, section 5.3.2.34, page 154
    "0427": {
        "hex": "0427",
        "name": "message_state",
        "type": "integer",
        "tech": "Generic",
    },  # SMPP v3.4, section 5.3.2.35, page 154
    "0428": {"hex": "0428", "name": "congestion_state", "type": None, "tech": "Generic"},
    "0501": {
        "hex": "0501",
        "name": "ussd_service_op",
        "type": "hex",
        "tech": "GSM (USSD)",
    },  # SMPP v3.4, section 5.3.2.44, page 161
    "0600": {"hex": "0600", "name": "broadcast_channel_indicator", "type": None, "tech": "GSM"},
    "0601": {
        "hex": "0601",
        "name": "broadcast_content_type",
        "type": None,
        "tech": "CDMA, TDMA, GSM",
    },
    "0602": {
        "hex": "0602",
        "name": "broadcast_content_type_info",
        "type": None,
        "tech": "CDMA, TDMA",
    },
    "0603": {"hex": "0603", "name": "broadcast_message_class", "type": None, "tech": "GSM"},
    "0604": {"hex": "0604", "name": "broadcast_rep_num", "type": None, "tech": "GSM"},
    "0605": {
        "hex": "0605",
        "name": "broadcast_frequency_interval",
        "type": None,
        "tech": "CDMA, TDMA, GSM",
    },
    "0606": {
        "hex": "0606",
        "name": "broadcast_area_identifier",
        "type": None,
        "tech": "CDMA, TDMA, GSM",
    },
    "0607": {
        "hex": "0607",
        "name": "broadcast_error_status",
        "type": None,
        "tech": "CDMA, TDMA, GSM",
    },
    "0608": {"hex": "0608", "name": "broadcast_area_success", "type": None, "tech": "GSM"},
    "0609": {"hex": "0609", "name": "broadcast_end_time", "type": None, "tech": "CDMA, TDMA, GSM"},
    "060a": {"hex": "060a", "name": "broadcast_service_group", "type": None, "tech": "CDMA, TDMA"},
    "060b": {"hex": "060b", "name": "billing_identification", "type": None, "tech": "Generic"},
    "060d": {"hex": "060d", "name": "source_network_id", "type": None, "tech": "Generic"},
    "060e": {"hex": "060e", "name": "dest_network_id", "type": None, "tech": "Generic"},
    "060f": {"hex": "060f", "name": "source_node_id", "type": None, "tech": "Generic"},
    "0610": {"hex": "0610", "name": "dest_node_id", "type": None, "tech": "Generic"},
    "0611": {
        "hex": "0611",
        "name": "dest_addr_np_resolution",
        "type": None,
        "tech": "CDMA, TDMA (US Only)",
    },
    "0612": {
        "hex": "0612",
        "name": "dest_addr_np_information",
        "type": None,
        "tech": "CDMA, TDMA (US Only)",
    },
    "0613": {
        "hex": "0613",
        "name": "dest_addr_np_country",
        "type": None,
        "tech": "CDMA, TDMA (US Only)",
    },
    "1101": {
        "hex": "1101",
        "name": "PDC_MessageClass",
        "type": None,
        "tech": "? (J-Phone)",
    },  # v4 page 75
    "1102": {
        "hex": "1102",
        "name": "PDC_PresentationOption",
        "type": None,
        "tech": "? (J-Phone)",
    },  # v4 page 76
    "1103": {
        "hex": "1103",
        "name": "PDC_AlertMechanism",
        "type": None,
        "tech": "? (J-Phone)",
    },  # v4 page 76
    "1104": {
        "hex": "1104",
        "name": "PDC_Teleservice",
        "type": None,
        "tech": "? (J-Phone)",
    },  # v4 page 77
    "1105": {
        "hex": "1105",
        "name": "PDC_MultiPartMessage",
        "type": None,
        "tech": "? (J-Phone)",
    },  # v4 page 77
    "1106": {
        "hex": "1106",
        "name": "PDC_PredefinedMsg",
        "type": None,
        "tech": "? (J-Phone)",
    },  # v4 page 78
    "1201": {
        "hex": "1201",
        "name": "display_time",
        "type": "integer",
        "tech": "CDMA, TDMA",
    },  # SMPP v3.4, section 5.3.2.26, page 148
    "1203": {
        "hex": "1203",
        "name": "sms_signal",
        "type": "integer",
        "tech": "TDMA",
        "min": 2,
    },  # SMPP v3.4, section 5.3.2.40, page 158
    "1204": {
        "hex": "1204",
        "name": "ms_validity",
        "type": "integer",
        "tech": "CDMA, TDMA",
    },  # SMPP v3.4, section 5.3.2.27, page 149
    "1304": {
        "hex": "1304",
        "name": "IS95A_AlertOnDelivery",
        "type": None,
        "tech": "CDMA",
    },  # v4 page 85
    "1306": {
        "hex": "1306",
        "name": "IS95A_LanguageIndicator",
        "type": None,
        "tech": "CDMA",
    },  # v4 page 86
    "130c": {
        "hex": "130c",
        "name": "alert_on_message_delivery",
        "type": None,
        "tech": "CDMA",
    },  # SMPP v3.4, section 5.3.2.41, page 159
    "1380": {
        "hex": "1380",
        "name": "its_reply_type",
        "type": "integer",
        "tech": "CDMA",
    },  # SMPP v3.4, section 5.3.2.42, page 159
    "1383": {
        "hex": "1383",
        "name": "its_session_info",
        "type": "hex",
        "tech": "CDMA",
        "min": 2,
    },  # SMPP v3.4, section 5.3.2.43, page 160
    "1402": {"hex": "1402", "name": "operator_id", "type": None, "tech": "vendor extension"},
    "1403": {
        "hex": "1403",
        "name": "tariff",
        "type": None,
        "tech": "Mobile Network Code vendor extension",
    },
    "1450": {
        "hex": "1450",
        "name": "mcc",
        "type": None,
        "tech": "Mobile Country Code vendor extension",
    },
    "1451": {
        "hex": "1451",
        "name": "mnc",
        "type": None,
        "tech": "Mobile Network Code vendor extension",
    },
}


def optional_parameter_tag_name_by_hex(x):
    return optional_parameter_tag_by_hex.get(x, {}).get("name")


def optional_parameter_tag_type_by_hex(x):
    return optional_parameter_tag_by_hex.get(x, {}).get("type")


def unpack_pdu(pdu_bin):
    return decode_pdu(pdu_bin.hex())


def decode_pdu(pdu_hex):
    hex_ref = [pdu_hex]
    pdu = {}
    body = decode_body(hex_ref)
    if len(body) > 0:
        pdu["body"] = body
    return pdu


def decode_body(hex_ref):
    body = {}
    optional = decode_optional_parameters(hex_ref)

    if len(optional) > 0:
        body["optional_parameters"] = optional
    return body


def decode_optional_parameters(hex_ref):

    optional_parameters = []
    hex = hex_ref[0]
    # The original PDU in bytes is: bytes.fromhex(hex_ref[0])
    while len(hex) > 0:
        if len(hex) < 8:
            # We don't have enough data here for this to be a valid param.
            # TODO: Something better than `print` here.
            print("Invalid optional param data, ignoring: %s" % (hex,))
            break
        (tag_hex, length_hex, rest) = (hex[0:4], hex[4:8], hex[8:])
        tag = optional_parameter_tag_name_by_hex(tag_hex)
        if tag is None:
            tag = tag_hex
        length = int(length_hex, 16)
        (value_hex, tail) = (rest[0 : length * 2], rest[length * 2 :])
        if len(value_hex) == 0:
            value = None
        else:
            value = decode_hex_type(value_hex, optional_parameter_tag_type_by_hex(tag_hex))
        hex = tail
        optional_parameters.append({"tag": tag, "length": length, "value": value})
    return optional_parameters


def decode_hex_type(hex, type, count=0, hex_ref=[""]):
    if hex is None:
        return hex
    elif type == "integer":
        return int(hex, 16)
    elif type == "string":
        return re.sub("00", "", hex).decode("hex")
    elif type == "xstring":
        return hex.decode("hex")
    elif type == "dest_address" or type == "unsuccess_sme":
        list = []
        fields = mandatory_parameter_list_by_command_name(type)
        for i in range(count):
            item = decode_mandatory_parameters(fields, hex_ref)
            if item.get("dest_flag", None) == 1:  # 'dest_address' only
                subfields = mandatory_parameter_list_by_command_name("sme_dest_address")
                rest = decode_mandatory_parameters(subfields, hex_ref)
                item.update(rest)
            elif item.get("dest_flag", None) == 2:  # 'dest_address' only
                subfields = mandatory_parameter_list_by_command_name("distribution_list")
                rest = decode_mandatory_parameters(subfields, hex_ref)
                item.update(rest)
            list.append(item)
        return list
    else:
        return hex


def command_id_name_by_hex(x):
    return command_id_by_hex.get(x, {}).get("name")


command_id_by_hex = {
    "80000000": {"hex": "80000000", "name": "generic_nack"},
    "00000001": {"hex": "00000001", "name": "bind_receiver"},
    "80000001": {"hex": "80000001", "name": "bind_receiver_resp"},
    "00000002": {"hex": "00000002", "name": "bind_transmitter"},
    "80000002": {"hex": "80000002", "name": "bind_transmitter_resp"},
    "00000003": {"hex": "00000003", "name": "query_sm"},
    "80000003": {"hex": "80000003", "name": "query_sm_resp"},
    "00000004": {"hex": "00000004", "name": "submit_sm"},
    "80000004": {"hex": "80000004", "name": "submit_sm_resp"},
    "00000005": {"hex": "00000005", "name": "deliver_sm"},
    "80000005": {"hex": "80000005", "name": "deliver_sm_resp"},
    "00000006": {"hex": "00000006", "name": "unbind"},
    "80000006": {"hex": "80000006", "name": "unbind_resp"},
    "00000007": {"hex": "00000007", "name": "replace_sm"},
    "80000007": {"hex": "80000007", "name": "replace_sm_resp"},
    "00000008": {"hex": "00000008", "name": "cancel_sm"},
    "80000008": {"hex": "80000008", "name": "cancel_sm_resp"},
    "00000009": {"hex": "00000009", "name": "bind_transceiver"},
    "80000009": {"hex": "80000009", "name": "bind_transceiver_resp"},
    "0000000b": {"hex": "0000000b", "name": "outbind"},
    "00000015": {"hex": "00000015", "name": "enquire_link"},
    "80000015": {"hex": "80000015", "name": "enquire_link_resp"},
    "00000021": {"hex": "00000021", "name": "submit_multi"},
    "80000021": {"hex": "80000021", "name": "submit_multi_resp"},
    "00000102": {"hex": "00000102", "name": "alert_notification"},
    "00000103": {"hex": "00000103", "name": "data_sm"},
    "80000103": {"hex": "80000103", "name": "data_sm_resp"},
}


def command_status_name_by_hex(x):
    return command_status_by_hex.get(x, {}).get("name")


command_status_by_hex = {
    "00000000": {"hex": "00000000", "name": "ESME_ROK", "description": "No error"},
    "00000001": {
        "hex": "00000001",
        "name": "ESME_RINVMSGLEN",
        "description": "Message Length is invalid",
    },
    "00000002": {
        "hex": "00000002",
        "name": "ESME_RINVCMDLEN",
        "description": "Command Length is invalid",
    },
    "00000003": {"hex": "00000003", "name": "ESME_RINVCMDID", "description": "Invalid Command ID"},
    "00000004": {
        "hex": "00000004",
        "name": "ESME_RINVBNDSTS",
        "description": "Incorrect BIND Status for given command",
    },
    "00000005": {
        "hex": "00000005",
        "name": "ESME_RALYBND",
        "description": "ESME Already in bound state",
    },
    "00000006": {
        "hex": "00000006",
        "name": "ESME_RINVPRTFLG",
        "description": "Invalid priority flag",
    },
    "00000007": {
        "hex": "00000007",
        "name": "ESME_RINVREGDLVFLG",
        "description": "Invalid registered delivery flag",
    },
    "00000008": {"hex": "00000008", "name": "ESME_RSYSERR", "description": "System Error"},
    "0000000a": {
        "hex": "0000000a",
        "name": "ESME_RINVSRCADR",
        "description": "Invalid source address",
    },
    "0000000b": {
        "hex": "0000000b",
        "name": "ESME_RINVDSTADR",
        "description": "Invalid destination address",
    },
    "0000000c": {
        "hex": "0000000c",
        "name": "ESME_RINVMSGID",
        "description": "Message ID is invalid",
    },
    "0000000d": {"hex": "0000000d", "name": "ESME_RBINDFAIL", "description": "Bind failed"},
    "0000000e": {"hex": "0000000e", "name": "ESME_RINVPASWD", "description": "Invalid password"},
    "0000000f": {"hex": "0000000f", "name": "ESME_RINVSYSID", "description": "Invalid System ID"},
    "00000011": {"hex": "00000011", "name": "ESME_RCANCELFAIL", "description": "Cancel SM Failed"},
    "00000013": {
        "hex": "00000013",
        "name": "ESME_RREPLACEFAIL",
        "description": "Replace SM Failed",
    },
    "00000014": {"hex": "00000014", "name": "ESME_RMSGQFUL", "description": "Message queue full"},
    "00000015": {
        "hex": "00000015",
        "name": "ESME_RINVSERTYP",
        "description": "Invalid service type",
    },
    "00000033": {
        "hex": "00000033",
        "name": "ESME_RINVNUMDESTS",
        "description": "Invalid number of destinations",
    },
    "00000034": {
        "hex": "00000034",
        "name": "ESME_RINVDLNAME",
        "description": "Invalid distribution list name",
    },
    "00000040": {
        "hex": "00000040",
        "name": "ESME_RINVDESTFLAG",
        "description": "Destination flag is invalid (submit_multi)",
    },
    "00000042": {
        "hex": "00000042",
        "name": "ESME_RINVSUBREP",
        "description": "Invalid `submit with replace' request (i.e. submit_sm with replace_if_present_flag set)",
    },
    "00000043": {
        "hex": "00000043",
        "name": "ESME_RINVESMCLASS",
        "description": "Invalid esm_class field data",
    },
    "00000044": {
        "hex": "00000044",
        "name": "ESME_RCNTSUBDL",
        "description": "Cannot submit to distribution list",
    },
    "00000045": {
        "hex": "00000045",
        "name": "ESME_RSUBMITFAIL",
        "description": "submit_sm or submit_multi failed",
    },
    "00000048": {
        "hex": "00000048",
        "name": "ESME_RINVSRCTON",
        "description": "Invalid source address TON",
    },
    "00000049": {
        "hex": "00000049",
        "name": "ESME_RINVSRCNPI",
        "description": "Invalid source address NPI",
    },
    "00000050": {
        "hex": "00000050",
        "name": "ESME_RINVDSTTON",
        "description": "Invalid destination address TON",
    },
    "00000051": {
        "hex": "00000051",
        "name": "ESME_RINVDSTNPI",
        "description": "Invalid destination address NPI",
    },
    "00000053": {
        "hex": "00000053",
        "name": "ESME_RINVSYSTYP",
        "description": "Invalid system_type field",
    },
    "00000054": {
        "hex": "00000054",
        "name": "ESME_RINVREPFLAG",
        "description": "Invalid replace_if_present flag",
    },
    "00000055": {
        "hex": "00000055",
        "name": "ESME_RINVNUMMSGS",
        "description": "Invalid number of messages",
    },
    "00000058": {
        "hex": "00000058",
        "name": "ESME_RTHROTTLED",
        "description": "Throttling error (ESME has exceeded allowed message limits)",
    },
    "00000061": {
        "hex": "00000061",
        "name": "ESME_RINVSCHED",
        "description": "Invalid scheduled delivery time",
    },
    "00000062": {
        "hex": "00000062",
        "name": "ESME_RINVEXPIRY",
        "description": "Invalid message validity period (expiry time)",
    },
    "00000063": {
        "hex": "00000063",
        "name": "ESME_RINVDFTMSGID",
        "description": "Predefined message invalid or not found",
    },
    "00000064": {
        "hex": "00000064",
        "name": "ESME_RX_T_APPN",
        "description": "ESME Receiver Temporary App Error Code",
    },
    "00000065": {
        "hex": "00000065",
        "name": "ESME_RX_P_APPN",
        "description": "ESME Receiver Permanent App Error Code",
    },
    "00000066": {
        "hex": "00000066",
        "name": "ESME_RX_R_APPN",
        "description": "ESME Receiver Reject Message Error Code",
    },
    "00000067": {
        "hex": "00000067",
        "name": "ESME_RQUERYFAIL",
        "description": "query_sm request failed",
    },
    "000000c0": {
        "hex": "000000c0",
        "name": "ESME_RINVOPTPARSTREAM",
        "description": "Error in the optional part of the PDU Body",
    },
    "000000c1": {
        "hex": "000000c1",
        "name": "ESME_ROPTPARNOTALLWD",
        "description": "Optional paramenter not allowed",
    },
    "000000c2": {
        "hex": "000000c2",
        "name": "ESME_RINVPARLEN",
        "description": "Invalid parameter length",
    },
    "000000c3": {
        "hex": "000000c3",
        "name": "ESME_RMISSINGOPTPARAM",
        "description": "Expected optional parameter missing",
    },
    "000000c4": {
        "hex": "000000c4",
        "name": "ESME_RINVOPTPARAMVAL",
        "description": "Invalid optional parameter value",
    },
    "000000fe": {
        "hex": "000000fe",
        "name": "ESME_RDELIVERYFAILURE",
        "description": "Delivery Failure (used for data_sm_resp)",
    },
    "000000ff": {"hex": "000000ff", "name": "ESME_RUNKNOWNERR", "description": "Unknown error"},
}


import struct

tag = 0x001E
length = 0x0018  # 24 in length
tag_n_len = struct.pack(">HH", tag, length)
value = "1618Z-0102G-2333M-25FJF"  # 23 in length
value = value.encode() + chr(0).encode()  # 24 in length

deliver_sm_pdu = b"\x00\x00\x00M\x00\x00\x00\x05\x00\x00\x00\x00\x9f\x88\xf1$AWSBD\x00\x01\x0116505551234\x00\x01\x0117735554070\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x11id:1618Z-0102G-2333M-25FJF sub:SSS dlvrd:DDD blah blah"
deliver_sm_pdu = deliver_sm_pdu + tag_n_len + value


unpack_pdu(deliver_sm_pdu)
print()
print()


import struct

target_tag = 0x001E
target_tag = struct.pack(">H", target_tag)
import itertools


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


x = pairwise([1, 2, 3, 4, 5, 6, 7, 8, 9])
# list(x)
# [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)]

# target_tag in deliver_sm_pdu
print()
print()
if target_tag in deliver_sm_pdu:
    # the PDU contains a `receipted_message_id` TLV optional tag
    position_of_target_tag = deliver_sm_pdu.find(target_tag)
    # since a tag is 2 integer in size lets skip one more.
    end_of_target_tag = position_of_target_tag + 1
    # since after a tag, comes a tag_length which is 2 integer in size
    # lets also skip that
    end_of_target_tag_length = end_of_target_tag + 2
    # tag_value is of size 1 - 65
    tag_value = deliver_sm_pdu[end_of_target_tag_length + 1 :]
    tag_value = tag_value.replace(chr(0).encode(), b"")
    tag_value.decode()
else:
    # lets abort
    pass

print("tag_value:")
print(tag_value)


# body
body = b""
submit_sm_resp_smsc_message_id = "1618Z-0102G-2333M-25FJF"
body = body + submit_sm_resp_smsc_message_id.encode() + chr(0).encode()

# header
command_length = 16 + len(body)  # 16 is for headers
command_id = 0x80000004  # submit_sm_resp
command_status = 0x00000000  # success
header = struct.pack(">IIII", command_length, command_id, command_status, 1)
full_pdu = header + body

print("full_pdu")
print(full_pdu)
