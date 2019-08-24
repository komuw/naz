## 1. naz Config file (naz client) parameters
`naz-cli` accepts a config file. The config file is a python file that has a `naz.Client` instance.   
The parameters that can be put in that file, what they mean and their default values(if any) are documented here.                     
Note that these are also the parameters that [`naz.Client`](https://github.com/komuw/naz/blob/master/naz/client.py) takes.               
        
The parameters are divided into two categories,                    
(i) parameters that emanate from the SMPP specification and             
(ii) parameters that are specific to `naz`.          

#### (i) smpp spec parameters        
*parameter* | *meaning*     | *default value*
---       | ---         | ---
smsc_host | the IP address(or domain name) of the SMSC gateway/server | N/A
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
A copy of the SMPP spec is available at; https://github.com/komuw/naz/tree/master/documentation         
You are also encouraged to consult any documentation of the SMSC partner that you want to connect with. Experience has shown that not everyone implements the SMPP spec exactly the same ¯\_(ツ)_/¯



#### (ii) naz specific parameters
*parameter* | *meaning*     | *default value*
---       | ---         | ---     
encoding | encoding<sup>1</sup> used to encode messages been sent to SMSC | gsm0338
sequence_generator | python class instance used to generate sequence_numbers| naz.sequence.SimpleSequenceGenerator
outboundqueue | python class instance implementing some queueing mechanism. messages to be sent to SMSC are queued using the said mechanism before been sent | N/A
client_id | a unique string identifying a naz client class instance | "".join(random.choices(string.ascii_uppercase + string.digits, k=17))   
logger | python class instance to be used for logging | naz.log.SimpleLogger        
loglevel | the level at which to log | INFO
log_metadata | metadata that will be included in all log statements | {"smsc_host": smsc_host, "system_id": system_id}
codec_class | python class instance to be used to encode/decode messages | naz.nazcodec.SimpleNazCodec
codec_errors_level | same meaning as the `errors` argument to pythons' `encode` method as [defined here](https://docs.python.org/3/library/codecs.html#codecs.encode) | strict
enquire_link_interval | time in seconds to wait before sending an `enquire_link` request to SMSC to check on its status | 55.0
rateLimiter | python class instance implementing rate limitation | naz.ratelimiter.SimpleRateLimiter
hook | python class instance implemeting functionality/hooks to be called by `naz` just before sending request to SMSC and just after getting response from SMSC | naz.hooks.SimpleHook
throttle_handler | python class instance implementing functionality of what todo when naz starts getting throttled responses from SMSC | naz.throttle.SimpleThrottleHandler
correlation_handler | A python class instance that naz uses to store relations between SMPP sequence numbers and user applications' log_id's and/or hook_metadata. | naz.correlater.SimpleCorrelater
drain_duration | duration in seconds that `naz` will wait for after receiving a termination signal. | 8.00   
socket_timeout | duration that `naz` will wait, for socket/connection related activities with SMSC, before timing out | 30.00     

`SMSC`: Short Message Service Centre, ie the server               
`ESME`: External Short Message Entity, ie the client                   

**NB**: the only *mandatory* parameters are the ones marked N/A ie `smsc_host`, `smsc_port`, `system_id`, `password` and `outboundqueue`             

#### Example
1. An example config file is shown below.         

`/tmp/my_config.py` 
```python        
import naz
from examples.example_klasses import ExampleRedisQueue, MySeqGen, MyRateLimiter

# run as:
#  naz-cli --client examples.example_config.client
client = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=ExampleRedisQueue(),
    encoding="gsm0338",
    sequence_generator=MySeqGen(),
    loglevel="INFO",
    log_metadata={"environment": "staging", "release": "canary"},
    codec_errors_level="ignore",
    enquire_link_interval=70.00,
    rateLimiter=MyRateLimiter(),
)
```

2. An example `naz.Client` declaration              
```python
import asyncio
import naz

class ExampleQueue(naz.q.BaseOutboundQueue):
    def __init__(self):
        self.queue = asyncio.Queue(maxsize=1000)
    async def enqueue(self, item):
        self.queue.put_nowait(item)
    async def dequeue(self):
        return await self.queue.get()


outboundqueue = ExampleQueue()
cli = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
    log_metadata={"environment": "production",  "release": "canary"},
    loglevel="WARNING",
)
```


## 2. naz enqueued message protocol. 
Your application enqueues an item in the form of a json object to a queue of it's choice and then `naz` dequeues that message, converts it into a python object and uses the parameters in there to send the message to the right place.        
`naz` supports the following items:       

*parameter* | *meaning*     | type | *expectation*
---         | ---           | ---  | ---     
version     | the current version of the naz message protocol | string | mandatory
smpp_command | the SMPP command | naz.SmppCommand(string) | mandatory
log_id | a unique identify of this request | string | mandatory
short_message | message to send to SMSC | string | optional (it is however mandatory for `naz.SmppCommand.SUBMIT_SM`)
source_addr | the identifier(eg msisdn) of the message sender | string | optional (it is however mandatory for `naz.SmppCommand.SUBMIT_SM`)
destination_addr | the identifier(eg msisdn) of the message recipient | string | optional (it is however mandatory for `naz.SmppCommand.SUBMIT_SM`)
hook_metadata | additional metadata that you would like to be passed on to hooks | string | optional     


**Note:** The enqueued item has a `version` field. This indicates the current version of the naz message protocol.    
A future version of `naz` may ship with a different message protocol that may require different mandatory fields to be in the 
enqueued json object.    

example(in json):              
```json
'{"version": "1",
"smpp_command": "submit_sm", 
"short_message": "Hello. Thanks for subscribing to our service.", 
"log_id": "iEKas812k", 
"source_addr": "254722000000", 
"destination_addr": "254722111111", 
"hook_metadata": "{\\"telco\\": \\"verizon\\", \\"customer_id\\": 123456}"
}'
```       



**References:**       
1. consult the python standard encodings: https://docs.python.org/3/library/codecs.html#standard-encodings       
