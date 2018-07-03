`naz-cli` accepts a json config file. The parameters that can be put in that file, what they mean and their default values(if any) are documented here.                   
The parameters are divided into two categories, (i) parameters that emanate from the SMPP specification and (ii) parameters that are specific to `naz`.          

#### (i) smpp spec parameters        
*parameter* | *meaning*     | *default value*
---       | ---         | ---
smsc_host | the IP address(or doamin name) of the SMSC gateway | N/A
smsc_port        | the port at which SMSC is listening on       |  N/A
system_id | Identifies the ESME system requesting to bind as a transceiver with the SMSC. | N/A
password | The password to  be used by the SMSC to authenticate the ESME requesting to bind. | N/A
system_type | Identifies the type of ESME system requesting to bind with the SMSC. | ""
addr_ton | Type of Number of the ESME address. | 0
addr_npi | Numbering Plan Indicator (NPI) for ESME address(es) served via this SMPP transceiver session| 0
address_range | A single ESME address or a range of ESME addresses served via this SMPP transceiver session. | ""
interface_version | Indicates the version of the SMPP protocol supported by the ESME. | 34
service_type | Indicates the SMS Application service associated with the message | CMT
source_addr_ton |  Type of Number of message originator. | 1
source_addr_npi | Numbering Plan Identity of message originator. | 1
dest_addr_ton | Type of Number for destination. | 1
dest_addr_npi | Numbering Plan Identity of destination | 1
esm_class |  Indicates Message Mode & Message Type. | 8
protocol_id |  Protocol Identifier. Network specific field. | 0
priority_flag | Designates the priority level of the message. | 0
schedule_delivery_time | The short message is to be scheduled by the SMSC for delivery. | ""
validity_period | The validity period of this message. | ""
registered_delivery |  Indicator to signify if an SMSC delivery receipt or an SME acknowledgement is required. | 5
replace_if_present_flag |  Flag indicating if submitted message should replace an existing message. | 0
sm_default_msg_id |  Indicates the short message to send from a list of predefined (‘canned’) short messages stored on the SMSC | 0


**NB**: The canonical reference for these values is the SMPP version 3.4 spec document. It's is encouraged that you consult. 
Where anything differs with the SMPP spec document, you should consider the spec as the truth.        
Any errors are my own doing, apologies in advance.          
A copy of the SMPP spec is available at; https://github.com/komuw/naz/tree/master/docs         
You are also encouraged to consult any documentation of the SMSC partner that you want to connect with. Experience has shown that not everyone implements the SMPP spec exactly the same ¯\_(ツ)_/¯



#### (ii) naz specific parameters
*parameter* | *meaning*     | *default value*
---       | ---         | ---     
encoding | encoding used to encode messages been sent to SMSC | gsm0338
sequence_generator | python class used to generate sequence_numbers| naz.sequence.SimpleSequenceGenerator
outboundqueue | python class implementing some queueing mechanism. messages to be sent to SMSC are queued using the said mechanism before been sent | N/A
loglevel | the level at which to log | DEBUG
log_metadata | metadata that will be included in all log statements | {"smsc_host": smsc_host, "system_id": system_id}
codec_class | python class to be used to encode/decode messages | naz.nazcodec.NazCodec
codec_errors_level | same meaning as the `errors` argument to pythons' `encode` method as [defined here](https://docs.python.org/3/library/codecs.html#codecs.encode) | strict
enquire_link_interval | time in seconds to wait before sending an `enquire_link` request to SMSC to check on its status | 90
rateLimiter | python class implementing rate limitation | naz.ratelimiter.SimpleRateLimiter
hook | python class implemeting functionality/hooks to be called by `naz` just before sending request to SMSC and just after getting response from SMSC | naz.hooks.SimpleHook
throttle_handler | python class implementing functionality of what todo when naz starts getting throttled responses from SMSC | naz.throttle.SimpleThrottleHandler

`SMSC`: Short Message Service Centre, ie the server               
`ESME`: External Short Message Entity, ie the client                   

**NB**: the only *mandatory* parameters are the ones marked N/A ie `smsc_host`, `smsc_port`, `system_id`, `password` and `outboundqueue`             

#### Example
An example config file is shown below.         

`/tmp/my_config.json` 
```bash        
{
  "smsc_host": "127.0.0.1",
  "smsc_port": 2775,
  "system_id": "smppclient1",
  "password": "password",
  "outboundqueue": "dotted.path.to.Myqueue",
  "encoding": "gsm0338",
  "sequence_generator": "my.dotted.path.to.RedisSequencer",
  "loglevel": "INFO",
  "log_metadata": {
    "environment": "production",
    "release": "canary"
  },
  "codec_errors_level": "ignore",
  "enquire_link_interval": 30,
  "rateLimiter": "dotted.path.to.CustomRateLimiter"
}
```
