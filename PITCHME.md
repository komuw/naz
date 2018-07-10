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
`pip install naz`        
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
    log_metadata={ "env": "prod", "release": "canary", "work": "jira-2345"},
)
```

--- 
#### 5.1.1 observability: logs
```bash
{'event': 'connect', 'stage': 'start'} {'env': 'prod', 'release': 'canary', 'work': 'jira-2345', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
{'event': 'connect', 'stage': 'end'} {'env': 'prod', 'release': 'canary', 'work': 'jira-2345', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
{'event': 'tranceiver_bind', 'stage': 'start'} {'env': 'prod', 'release': 'canary', 'work': 'jira-2345', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
```

---
#### 5.1.2 observability: hooks          
An instance of a class that implements `naz.hooks.BaseHook`.  It has two methods `request` and `response`.         
create an instance implementation of `BaseHook`, plug it in, and u can do whatever u want inside `request`/`response` methods.  

---
#### 5.1.2 observability: example 
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
            c.execute("UPDATE SmsTable SET State='delivered' WHERE CorrelatinID=?", t)
            conn.commit()
            conn.close()

stateHook = SetMessageStateHook()
cli = naz.Client(
    ...
    hook=stateHook,
)
```

#### 5.2 Rate limiting             
#### 5.4 Throttle handling              
#### 5.5 Queuing             
#### 5.6 cli app

---
#### 6. then what?         


vumi smpp config:     
https://github.com/praekelt/vumi/blob/master/vumi/transports/smpp/config.py
