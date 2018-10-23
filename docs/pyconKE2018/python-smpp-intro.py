# 1. connect to network
import socket, struct

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect(("127.0.0.1", 2775))

# 2. create PDU
body = b""
command_length = 16 + len(body)  # 16 is for headers
command_id = 21  # enquire_link PDU
command_status = 0
sequence_number = 1
header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)
full_pdu = header + body

# 3. send PDU over network
sock.send(full_pdu)
