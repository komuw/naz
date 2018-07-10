pip install -U jupyter jupyterlab      
jupyter lab -y 
jupyter nbconvert pres.ipynb --to slides --post serve --SlidesExporter.reveal_theme=serif --SlidesExporter.reveal_scroll=True --SlidesExporter.reveal_transition=none    

---

#### topics                   
1. SMPP spec intro               
2. SMPP & python intro        
3. current lay of the land                  
4. naz intro                                       
5. naz features                    
6. then what?         

---
#### 1. SMPP spec intro                 
The SMPP protocol is designed for transfer of short messages between a Message Center(SMSC/USSD server etc) & an SMS app system.                
It's based on exchange of request/response protocol data units(PDUs) between the client and the server over a TCP/IP network.                

---
#### 1.1 sequence of requests
![Image of sequence](docs/sequence.png)
                             
---
#### 1.2 PDU format
![Image of pdu format](docs/pdu_format.png)

---
#### 2. SMPP & python intro         
```python
import socket, struct
# 1. network connect
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect(('127.0.0.1', 2775))
# 2. create PDU
body = b""
command_length = 16 + len(body)  # 16 is for headers
command_id = 21 # enquire_link PDU
command_status = 0
sequence_number = 1
header = struct.pack(">IIII",
                     command_length,
                     command_id,
                     command_status,
                     sequence_number)
# send PDU
full_pdu = header + body
sock.send(full_pdu)
```          
@[1-5]
@[6-16]
@[17-19]


---
#### 3. current lay of the land               
- github.com/podshumok/python-smpplib               
- github.com/praekelt/vumi                    
- ... couple more          

---
#### 3.1 problems with current solutions           
    - complexity of code base    
    - coupling with other things(rabbitMQ, redis, Twisted)      
    - non-granular configurability         
      - (PR #352 you can only set `throttle_delay: X seconds` )
    - maintenance debt:
      - (PR #342 disable vumi sentry integration; vumi outdated raven dependancies)
      - cant migrate transport to py3(because vumi is py2)
    - lack of visibility      
      - (PR #335 and PR #327 enrich queue to vumi logging). 
      - PR #336, PR #339


---
#### 4. naz intro                     
naz is an async SMPP client.       
It's easily configurable, BYO(throttlers, rateLimiters etc)        

---
#### 4.1 architecture                
| Your App |  ---> | Queue | ---> | Naz |                   
what is the Queue?? inMem, rabbitmq, redis ...??       
Naz makes no imposition of what the Queue is.      
BYO queue...             

---
#### 4.2 usage                          
```python
import naz, asyncio
loop = asyncio.get_event_loop()
outboundqueue = naz.q.SimpleOutboundQueue(maxsize=1000, loop=loop)
cli = naz.Client(
    async_loop=loop,
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
)
# 1. network connect and bind
reader, writer = loop.run_until_complete(cli.connect())
loop.run_until_complete(cli.tranceiver_bind())
try:
    # 2. consume from queue, read responses from SMSC, send status checks
    tasks = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
except Exception as e:
    print("exception occured. error={0}".format(str(e)))
finally:
    # 3. unbind
    loop.run_until_complete(cli.unbind())
    loop.close()
```
@[1-11]
@[12-14]
@[15-19]
@[20-25]

---
#### 4.2.1 sequence of requests
![Image of sequence](docs/sequence.png)

---
#### 5. naz features  
running theme: configurability, BYO ... nini nini

---                
#### 5.1.1 observability: logging                 
```python
import naz
cli = naz.Client(
    ...
    log_metadata={
        "env": "prod", "release": "canary", "work": "jira-2345"
        }
)
```

--- 
#### 5.1.1 observability: logs
```bash
{'event': 'connect', 'stage': 'start'}         
{'env': 'prod', 'release': 'canary', 'work': 'jira-2345', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}                
{'event': 'connect', 'stage': 'end'}              
{'env': 'prod', 'release': 'canary', 'work': 'jira-2345', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}               
{'event': 'tranceiver_bind', 'stage': 'start'}                   
{'env': 'prod', 'release': 'canary', 'work': 'jira-2345', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}                      
```

---
#### 5.1.2 observability: hooks          
An instance of a class that implements `naz.hooks.BaseHook`.  It has two methods `request` and `response`.         
create an instance implementation of `BaseHook`, plug it in, and u can do whatever u want inside `request`/`response` methods.  

---
#### 5.1.2 observability: hooks example 
```python
import sqlite3
import naz
class SetMessageStateHook(naz.hooks.BaseHook):
    async def request(self, smpp_event, correlation_id):
        pass
    async def response(self, smpp_event, correlation_id):
        if smpp_event == "deliver_sm":
            conn = sqlite3.connect('mySmsDB.db')
            c = conn.cursor()
            t = (correlation_id,)
            # watch out for SQL injections!!
            c.execute("UPDATE \
                       SmsTable \
                       SET State='delivered' \
                       WHERE CorrelatinID=?", t)
            conn.commit()
            conn.close()

stateHook = SetMessageStateHook()
cli = naz.Client(
    ...
    hook=stateHook,
)
```
@[6-17]

---
#### 5.2 Rate limiting  
An instance of a class that implements `naz.ratelimiter.BaseRateLimiter`.  It has one method `limit`.         
create an instance implementation of `BaseRateLimiter`, plug it in, and u can implement any rate limiting algo inside `limit` method.         
`naz` ships with a simple token-bucket Ratelimiter, `SimpleRateLimiter`   


---
#### 5.2 Rate limiting: example                
```python
import naz
limiter = naz.ratelimiter.SimpleRateLimiter(
    send_rate=1, max_tokens=1, delay_for_tokens=6
)
cli = naz.Client(
    ...
    rateLimiter=limiter,
)
```

---
#### 5.2 Rate limiting - logs
```bash
{'event': 'receive_data', 'stage': 'start'}                 
{'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
{'event': 'SimpleRateLimiter.limit', 'stage': 'end',            
'state': 'limiting rate',             
'send_rate': 1, 'delay': 6, 'effective_send_rate': 0.166}
```

---
#### 5.2 Rate limiting: example2                
```python
import naz

class AwesomeLimiter(naz.ratelimiter.BaseRateLimiter):
    async def limit(self):
        sleeper = 13.13
        print("\n\t hey we are rate limiting. sleep={}".format(sleeper))
        await asyncio.sleep(sleeper)

lim = AwesomeLimiter()
cli = naz.Client(
    ...
    rateLimiter=lim,
)
```

---
#### 5.2 Rate limiting 2 - logs
```
{'deny_request_at': 1, 'state': 'allow_request'}      
{'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}          

	 hey we are rate limiting. sleep=13.13
{'event': 'receive_data', 'stage': 'start'} {'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
```

---
#### 5.4 Throttle handling     
An instance of a class that implements `naz.throttle.BaseThrottleHandler`.  It has methods `throttled`, `not_throttled`, `allow_request` & `throttle_delay`.         
create an instance implementation of `BaseThrottleHandler` and plug it in.         
`naz` ships with a default, `SimpleThrottleHandler`              

---
#### 5.4 Throttle handling; example
```python
import naz

th = naz.throttle.SimpleThrottleHandler(sampling_period=180,
                                        sample_size=45,
                                        deny_request_at=1.2)
cli = naz.Client(
    ...
    throttle_handler=th,
)
```

---
#### 5.5 Queuing               
An instance of a class that implements `naz.q.BaseOutboundQueue`. It has two methods `enqueue` & `dequeue`.         
what you put inside those two methods is upto you.         
Your app queues messages, naz consumes from that queue and then sends those messages to SMSC/server.           
`naz` ships with a `SimpleOutboundQueue` that queues inMem.

---
#### 5.5 Queuing; example
```python
import asyncio, naz, redis

class RedisExampleQueue(naz.q.BaseOutboundQueue):
    def __init__(self):
        self.redis_instance = redis.StrictRedis(host="localhost", port=6379, db=0)
        self.queue_name = "myqueue"
    async def enqueue(self, item):
        self.redis_instance.lpush(self.queue_name, json.dumps(item))
    async def dequeue(self):
        x = self.redis_instance.brpop(self.queue_name)
        dequed_item = json.loads(x[1].decode())
        return dequed_item

loop = asyncio.get_event_loop()
outboundqueue = RedisExampleQueue()
cli = naz.Client(
    async_loop=loop,
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
)
# 1. network connect and bind
reader, writer = loop.run_until_complete(cli.connect())
loop.run_until_complete(cli.tranceiver_bind())
try:
    # 2. consume from queue, read responses from SMSC, send status checks
    tasks = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
except Exception as e:
    print("exception occured. error={0}".format(str(e)))
finally:
    # 3. unbind
    loop.run_until_complete(cli.unbind())
    loop.close()
```
@[3-10]
@[12-21]

---
#### 5.5 Queuing; example (your app)
```python
import asyncio, naz, redis

outboundqueue = RedisExampleQueue()
for i in range(0, 5):
    item = {
        "smpp_event": "submit_sm",
        "short_message": "Hello World-{0}".format(str(i)),
        "correlation_id": "myid12345",
        "source_addr": "254722111111",
        "destination_addr": "254722999999",
    }
    loop.run_until_complete(outboundqueue.enqueue(item))
```
@[3-12]

---
#### 5.6 cli app

---
#### 6. then what?         


vumi smpp config:     
https://github.com/praekelt/vumi/blob/master/vumi/transports/smpp/config.py
