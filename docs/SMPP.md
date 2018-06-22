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



