#### 2.1 Protocol Definition
SMPP is based on the exchange of request and response protocol data units (PDUs) between the ESME and the SMSC over an underlying TCP/IP or X.25 network connection. 
The SMPP protocol defines:
- a set of operations and associated Protocol Data Units (PDUs) for the exchange of short messages between an ESME and an SMSC
- the data that an ESME application can exchange with an SMSC during SMPP operations. 

Every SMPP operation must consist of a request PDU and associated response PDU.
The receiving entity must return the associated SMPP response to an SMPP PDU request.
- the only exception to this rule is the `alert_notification` PDU for which there is no response                   

**NB:** We will only concern ourselves with an ESME in `Transceiver` mode.

#### 2.2 SMPP session states:
1. OPEN (Connected and Bind Pending)
An ESME has established a network connection to the SMSC but has not yet issued a Bind request.
2. BOUND_TRX
A connected ESME has requested to bind as an ESME Transceiver (by issuing a `bind_transceiver` **PDU**) and has received a response from the SMSC authorising its
Bind request. An ESME bound as a Transceiver supports the complete set of operations supported by a Transmitter ESME and a Receiver ESME.
3. CLOSED (Unbound and Disconnected)
An ESME has unbound from the SMSC and has closed the network connection. The SMSC may also unbind from the ESME.                
**NB:** we are ignoring the other states since we are only concerning ourselves with an ESME in `Transceiver` mode.

The purpose of the `outbind` operation is to allow the SMSC signal an ESME to originate a `bind_receiver` request to the SMSC. An example of where such a facility might be applicable would be where the SMSC had outstanding messages for delivery to the ESME.
SMSC should bind to the ESME by issuing an `outbind` request. The ESME responds with a `bind_receiver` request to which the SMSC will reply with a `bind_receiver_resp`. If the ESME does not accept the outbind session (e.g. because of an illegal system_id orpassword etc.) the ESME should disconnect the network connection. Once the SMPP session is established the characteristics of the session are that of a normal SMPP receiver session.                 
**question:** does ESME have to respond with a `bind_receiver` or can it send a `bind_transceiver` ??

#### 2.3 PDUS
Section 2.3 of smpp ver3.4 spec has a table of all PDU names(`submit_sm`, `bind_transceiver` etc ) the smpp session state that applies to them and who(ESME or SMSC) can issue them.                 
**NB:** For first draft we will only support the following PDUs:         
`bind_transceiver` -> `bind_transceiver_resp`            
`unbind` -> `unbind_resp`           
`submit_sm` -> `submit_sm_resp`           
`deliver_sm` -> `deliver_sm_resp`            
`enquire_link` -> `enquire_link_resp`           
`generic_nack` -> has no response. it is for error handling.

#### 2.4 Network Layer Connections
The underlying transport interface between the SMSC and ESME may be based on a TCP/IP or X.25 network connection.
For us, will assume TCP/IP.
At the SMPP level, the ESME and SMSC should treat the network connection as a reliable transport which manages delivery and receipt of SMPP PDUs.


#### 2.5 SMPP messages sent from ESME to SMSC, and their responses
`submit_sm` -> `submit_sm_resp`          
`data_sm` -> `data_sm_resp`          
In addition to submission of messages to the SMSC, an ESME may perform the following SMPP operations **using** the **message identifier returned** by the **SMSC in the message acknowledgement**:          
`query_sm ` -> `query_sm_resp`: Query the SMSC for the status of a previously submitted message        
`cancel_sm` -> `cancel_sm_resp`: Cancel delivery of a previously submitted message            
`replace_sm` -> `replace_sm_resp`: Replace a previously submitted message                         
**NB:** For first draft we will only support `submit_sm` PDU

#### 2.6 SMPP messages sent from SMSC to ESME , and their responses          
`deliver_sm` -> `deliver_sm_resp`       
`data_sm` -> `data_sm_resp`          
`alert_notification` -> has no response                          
**NB:** For first draft we will only support `deliver_sm` PDU

SMPP responses should be returned in the same order in which the original requests were received. 
However **this is not mandatory** within SMPP and the **ESME/SMSC should be capable of handling responses received out of sequence.**

The maximum number of outstanding (i.e. unacknowledged) SMPP operations between an ESME and SMSC and vice versa is not specified explicitly in the SMPP spec and will be **governed** by the **SMPP implementation on the SMSC**.
However, as a guideline it is recommended that no more than **10 SMPP messages are outstanding** at any time.


#### 2.8 SMPP Error Handling
In the event that the original SMPP request PDU is found to contain an error, the receiving entity must return a response with an appropriate error code inserted in the `command_status` field of the response PDU header. (See section 3.2 of spec document.)       
If the receiving entity finds an error in the PDU header, it should return a `generic_nak` PDU to the originator. (See section 4.3 of spec document.)

#### 2.9 SMPP Timers
It is recommended that each SMPP session be managed using configurable timers on both the ESME and SMSC communicating.
(See section 7.2 of spec document.)                       
**NB:** For first draft we will only support `enquire_link_timer` on it's expiration we will send an `enquire_link` request to SMSC. This timer specifies the time lapse allowed between operations after which an SMPP entity should interrogate whether it’s peer still has an active session.


#### 2.10 Message Modes
The typical delivery mechanisms that may be offered by an SMSC are: `Store and Forward`, `Datagram`, `Transaction mode`            
Store and Forward - SMSC stores sms in db before forwading to customer. SMPP supports this mode via `submit_sm` operation.          
The ESME must request an SMSC Delivery Receipt in the `submit_sm` operation using the `esm_class` parameter of `submit_sm` op.                       
**NB:** For first draft we will only support `Store and Forward` msg mode. we will use `esm_class` param of submit_sm op.

Look at section 2.11 of spec document to learn more about Message Types.

#### 3.1 SMPP PDU - Type Definitions
The following SMPP PDU data type definitions are used to define the SMPP parameters:
- Integer - An **unsigned** value with the defined number of octets. The octets will always be transmitted MSB first (Big Endian). NULL is zero.      
**NB:** todo this in python use:
```python
## https://stackoverflow.com/a/846045/2768067
## https://docs.python.org/3.6/library/struct.html#format-characters
import struct
print struct.pack('>I', 134) # '>I' is a format string. > means big endian and I means unsigned int
```              
**NB:** the format string depends on the size allowed. as an example `interface_version` is an Integer whose size should be `1 octet` (section 4.1.5)
```python
import struct
interface_version = 34
struct.pack('>B', interface_version) # here we use `B` because has size 1 see; https://docs.python.org/3.6/library/struct.html#format-characters
```

- C-Octet String - A series of **ASCII characters** terminated with the **NULL** character. eg `system_id` is a C-Octet String.            
**NB:** in python;
```python
import six
system_id = 'smppclient1' 
six.b( system_id + chr(0)) # b'smppclient1\x00'
# alternative: bytes(system_id + chr(0), 'utf8') but we would have to check on encoding
```
- C-Octet Strin(Decimal) - A series of ASCII characters, each character **representing** a decimal digit (0 - 9) and terminated with the NULL character.
- C-Octet String(Hex) - A series of ASCII characters, each character representing a hexadecimal digit (0 - F) and terminated with the NULL character.
- Octet String - A series of octets, not necessarily NULL terminated.                    
**NB:** look at the caveats at the end of section 3.1


#### 3.2 SMPP PDU Format - Overview
SMPP PDU consists of a PDU header followed by a PDU body.      

Header:        
- command_length, 4octets, Integer - The command_length field defines the total octet length of the SMPP PDU packet including the length field.
- command_id, 4octets, Integer - The command_id field identifies the particular SMPP PDU, e.g., submit_sm, query_sm, etc.
  each SMPP request PDU has a unique command_id in the range 0x00000000 to 0x000001FF
  each SMPP response PDU has a unique command_id in the range 0x80000000 to 0x800001FF.
  eg: `submit_sm` is command_id `0x00000004` while `submit_sm_resp` is `0x80000004`
  Look at chapter 5 of spec document.
- command_status, 4octets, Integer - The command_status field indicates the success or failure of an SMPP request.
  it should be set to NULL for smpp requests, it only applies to responses.
- sequence_number, 4octets, Integer - number which allows SMPP requests and responses to be correlated. should increase monotonically.
  **ought to be in 0x00000001 to 0x7FFFFFFF range.**                    

Body:
- Mandatory Parameters, variable octet, mixed Type - A list of mandatory parameters corresponding to that SMPP PDU defined in the command_id
  Look at section 4 of spec document to learn more about Message Types.
- Optional Parameters, variable octet, mixed Type - list of Optional Parameters corresponding to that SMPP PDU defined in the command_id          
They are laid out as follows;               

command-length | command-id | command-status |sequence-number | PDU-Body            


**NB:** Some SMPP PDUs may only have a Header part only, for example, the `enquire_link`     
**NB:** 1octet == 8bits == 1byte. so 4 octets == 4bytes. so for `submit_sm_resp` is `0x80000004`
```python
import struct
body = b'smppclient1\x00password\x00\x00\x00\x00\x004\x00\x00\x00'
command_length = 16 + len(body)  #16 is for headers
command_code = 0x00000009 #the command code for `bind_transceiver` see section 5.1.2.1
status =  0x00000000 #the status for success see section 5.1.3
sequence = 0x00000001
header = struct.pack(">IIII", command_length, command_code, status, sequence) # will be the same if we used `">LLLL"` as format string
item_to_send_down_the_wire = header + body
```


#### Example
Here's a full example of sending a `bind_transceiver` request.             
look at section 4.1.5 for `bind_transceiver` Syntax.

```python
# see section 4.1.5 for BIND_TRANSCEIVER Syntax
# set asyncio debug. ie export PYTHONASYNCIODEBUG=1 && python aha.py
import socket
import struct

### setup socket ####
_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_socket.settimeout(5)
_socket.connect(('127.0.0.1', 2775))
####################

### create body ####
body = b''
system_id = 'smppclient1'
password = 'password'
system_type = ''
interface_version = 34
addr_ton = 0
addr_npi = 0
address_range = ''

body = body + \
       bytes(system_id + chr(0), 'utf8') + \
       bytes(password + chr(0), 'utf8') + \
       bytes(system_type + chr(0), 'utf8') + \
       struct.pack('>I', interface_version) + \
       struct.pack('>I', addr_ton) + \
       struct.pack('>I', addr_npi) + \
      bytes(address_range + chr(0), 'utf8')
####################

### create header ####
command_length = 16 + len(body) #16 is for headers
command_code = 0x00000009 #the command code for `bind_transceiver` see section 5.1.2.1
status =  0x00000000 #the status for success see section 5.1.3
sequence = 0x00000001
header = struct.pack(">IIII", command_length, command_code, status, sequence)
######################

#### send
item_to_send_down_the_wire = header + body
sent_last = _socket.send(item_to_send_down_the_wire[0:])
```
and SMSC logs look like:
```bash
BIND_TRANSCEIVER:
3 cmd_len=51,cmd_id=9,cmd_status=0,seq_no=1,system_id=smppclient1
password=password,system_type=,interface_version=0,addr_ton=0,addr_npi=0, address_range=''
StandardProtocolHandler: setting address range to
New transceiver session bound to SMPPSim

BIND_TRANSCEIVER_RESP:
cmd_len=0,cmd_id=-2147483639,cmd_status=0,seq_no=1,system_id=SMPPSim
```
