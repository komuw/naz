## naz          

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/616e5c6664dd4c1abb26f34f0bf566ae)](https://www.codacy.com/app/komuw/naz)
[![ci](https://github.com/komuw/naz/workflows/naz%20ci/badge.svg)](https://github.com/komuw/naz/actions)
[![codecov](https://codecov.io/gh/komuw/naz/branch/master/graph/badge.svg)](https://codecov.io/gh/komuw/naz)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/komuw/naz)


naz is an async SMPP client.           
It's name is derived from Kenyan hip hop artiste, Nazizi.                             

> SMPP is a protocol designed for the transfer of short message data between External Short Messaging Entities(ESMEs), Routing Entities(REs) and Short Message Service Center(SMSC). - [Wikipedia](https://en.wikipedia.org/wiki/Short_Message_Peer-to-Peer)

naz currently only supports SMPP version 3.4.       
naz has no third-party dependencies and it requires python version 3.6+


naz is in active development and it's API may change in backward incompatible ways.               
[https://pypi.python.org/pypi/naz](https://pypi.python.org/pypi/naz)                 


Comprehensive documetion is available -> [Documentation](https://komuw.github.io/naz)


**Contents:**          
[Installation](#installation)         
[Usage](#usage)                  
  + [As a library](#1-as-a-library)            
  + [As cli app](#2-as-a-cli-app)            

[Features](#features)               
  + [async everywhere](#1-async-everywhere)            
  + [monitoring-and-observability](#2-monitoring-and-observability)            
    + [logging](#21-logging)            
    + [hooks](#22-hooks)
    + [integration with bug trackers(eg Sentry )](#23-integration-with-bug-trackers)
  + [Rate limiting](#3-rate-limiting)            
  + [Throttle handling](#4-throttle-handling)            
  + [Queuing](#5-queuing)      
      
[Benchmarks](./benchmarks/README.md)


## Installation

```shell
pip install naz
```           


## Usage

#### 1. As a library
```python
import asyncio
import naz

loop = asyncio.get_event_loop()
outboundqueue = naz.q.SimpleOutboundQueue(maxsize=1000)
cli = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
)

# queue messages to send
for i in range(0, 4):
    print("submit_sm round:", i)
    loop.run_until_complete(
        cli.submit_sm(
            short_message="Hello World-{0}".format(str(i)),
            log_id="myid12345",
            source_addr="254722111111",
            destination_addr="254722999999",
        )
    )

# connect to the SMSC host
reader, writer = loop.run_until_complete(cli.connect())
# bind to SMSC as a tranceiver
loop.run_until_complete(cli.tranceiver_bind())

try:
    # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
    tasks = asyncio.gather(cli.dequeue_messages(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
    loop.run_forever()
except Exception as e:
    print("exception occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.stop()
```
**NB:**      
(a) For more information about all the parameters that `naz.Client` can take, consult the [documentation here](https://github.com/komuw/naz/blob/master/documentation/config.md)            
(b) More [examples can be found here](https://github.com/komuw/naz/tree/master/examples)         
(c) if you need a SMSC server/gateway to test with, you can use the [docker-compose file in this repo](https://github.com/komuw/naz/blob/master/docker-compose.yml) to bring up an SMSC simulator.        
That docker-compose file also has a redis and rabbitMQ container if you would like to use those as your outboundqueue.


#### 2. As a cli app
naz also ships with a commandline interface app called `naz-cli`.            
create a python config file, eg;            
`/tmp/my_config.py`
```python
import naz
from myfile import ExampleQueue

client = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=ExampleQueue()
)
```
and a python file, `myfile.py` (in the current working directory) with the contents:

```python
import asyncio
import naz

class ExampleQueue(naz.q.BaseOutboundQueue):
    def __init__(self):
        loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue(maxsize=1000, loop=loop)
    async def enqueue(self, item):
        self.queue.put_nowait(item)
    async def dequeue(self):
        return await self.queue.get()
```
then 
run:                
`naz-cli --client tmp.my_config.client`
```shell
	 Naz: the SMPP client.

{'event': 'naz.Client.connect', 'stage': 'start', 'environment': 'production', 'release': 'canary', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1', 'client_id': '2VU55VT86KHWXTW7X'}
{'event': 'naz.Client.connect', 'stage': 'end', 'environment': 'production', 'release': 'canary', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1', 'client_id': '2VU55VT86KHWXTW7X'}
{'event': 'naz.Client.tranceiver_bind', 'stage': 'start', 'environment': 'production', 'release': 'canary', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1', 'client_id': '2VU55VT86KHWXTW7X'}
{'event': 'naz.Client.send_data', 'stage': 'start', 'smpp_command': 'bind_transceiver', 'log_id': None, 'msg': 'hello', 'environment': 'production', 'release': 'canary', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1', 'client_id': '2VU55VT86KHWXTW7X'}
{'event': 'naz.SimpleHook.to_smsc', 'stage': 'start', 'smpp_command': 'bind_transceiver', 'log_id': None, 'environment': 'production', 'release': 'canary', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1', 'client_id': '2VU55VT86KHWXTW7X'}
{'event': 'naz.Client.send_data', 'stage': 'end', 'smpp_command': 'bind_transceiver', 'log_id': None, 'msg': 'hello', 'environment': 'production', 'release': 'canary', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1', 'client_id': '2VU55VT86KHWXTW7X'}
{'event': 'naz.Client.tranceiver_bind', 'stage': 'end', 'environment': 'production', 'release': 'canary', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1', 'client_id': '2VU55VT86KHWXTW7X'}
{'event': 'naz.Client.dequeue_messages', 'stage': 'start', 'environment': 'production', 'release': 'canary', 'smsc_host': '127.0.0.1', 'system_id': 'smppclient1', 'client_id': '2VU55VT86KHWXTW7X'}
```              
             
**NB:**      
(a) For more information about the `naz` config file, consult the [documentation here](https://github.com/komuw/naz/blob/master/documentation/config.md)             
(b) More [examples can be found here](https://github.com/komuw/naz/tree/master/examples). As an example, start the SMSC simulator(`docker-compose up`) then in another terminal run, `naz-cli --client examples.example_config.client`

To see help:

`naz-cli --help`   
```shell         
naz is an async SMPP client.     
example usage: naz-cli --client path.to.my_config.client

optional arguments:
  -h, --help            show this help message and exit
  --version             The currently installed naz version.
  --client CLIENT       The config file to use. eg: --client path.to.my_config.client
```



## Features
#### 1. async everywhere
SMPP is an async protocol; the client can send a request and only get a response from SMSC/server 20mins later out of band.               
It thus makes sense to write your SMPP client in an async manner. We leverage python3's async/await to do so. 
```python
import naz
import asyncio

loop = asyncio.get_event_loop()
outboundqueue = naz.q.SimpleOutboundQueue(maxsize=1000)
cli = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
)
```

#### 2. monitoring and observability
it's a loaded term, I know.                  

##### 2.1 logging
In `naz` you have the ability to annotate all the log events that `naz` will generate with anything you want.        
So, for example if you wanted to annotate all log-events with a release version and your app's running environment.
```python
import naz

cli = naz.Client(
    ...
    log_metadata={ "environment": "production", "release": "canary"},
)
```
and then these will show up in all log events.             
by default, `naz` annotates all log events with `smsc_host`, `system_id` and `client_id`

##### 2.2 hooks
a hook is a class with two methods `to_smsc` and `from_smsc`, ie it implements `naz`'s BaseHook interface as [defined here](https://github.com/komuw/naz/blob/master/naz/hooks.py).           
`naz` will call the `to_smsc` method just before sending data to SMSC and also call the `from_smsc` method just after getting data from SMSC.       
the default hook that `naz` uses is `naz.hooks.SimpleHook` which does nothing but logs.             
If you wanted, for example to keep metrics of all requests and responses to SMSC in your [prometheus](https://prometheus.io/) setup;
```python
import naz
from prometheus_client import Counter

class MyPrometheusHook(naz.hooks.BaseHook):
    async def to_smsc(self, smpp_command, log_id, hook_metadata, pdu):
        c = Counter('my_requests', 'Description of counter')
        c.inc() # Increment by 1
    async def from_smsc(self,
                    smpp_command,
                    log_id,
                    hook_metadata,
                    status,
                    pdu):
        c = Counter('my_responses', 'Description of counter')
        c.inc() # Increment by 1

myHook = MyPrometheusHook()
cli = naz.Client(
    ...
    hook=myHook,
)
```
another example is if you want to update a database record whenever you get a delivery notification event;
```python
import sqlite3
import naz

class SetMessageStateHook(naz.hooks.BaseHook):
    async def to_smsc(self, smpp_command, log_id, hook_metadata, pdu):
        pass
    async def from_smsc(self,
                    smpp_command,
                    log_id,
                    hook_metadata,
                    status,
                    pdu):
        if smpp_command == naz.SmppCommand.DELIVER_SM:
            conn = sqlite3.connect('mySmsDB.db')
            c = conn.cursor()
            t = (log_id,)
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


#### 2.3 integration with bug trackers
If you want to integrate `naz` with your bug/issue tracker of choice, all you have to do is use their logging integrator.   
As an example, to integrate `naz` with [sentry](https://sentry.io/), all you have to do is import and init the sentry sdk. A good place to do that would be in the naz config file, ie;  
`/tmp/my_config.py`
```python
import naz
from myfile import ExampleQueue

import sentry_sdk # import sentry SDK
sentry_sdk.init("https://<YOUR_SENTRY_PUBLIC_KEY>@sentry.io/<YOUR_SENTRY_PROJECT_ID>")

my_naz_client = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=ExampleQueue()
)
```

then run the `naz-cli` as usual:                
`naz-cli --client tmp.my_config.my_naz_client`    
And just like that you are good to go. This is what errors from `naz` will look like on sentry(sans the emojis, ofcourse):   

![naz integration with sentry](https://raw.githubusercontent.com/komuw/naz/master/documentation/sphinx-docs/naz-sentry.png "naz integration with sentry")



#### 3. Rate limiting
Sometimes you want to control the rate at which the client sends requests to an SMSC/server. `naz` lets you do this, by allowing you to specify a custom rate limiter.
By default, `naz` uses a simple token bucket rate limiting algorithm [implemented here](https://github.com/komuw/naz/blob/master/naz/ratelimiter.py).         
You can customize `naz`'s ratelimiter or even write your own ratelimiter (if you decide to write your own, you just have to satisfy the `BaseRateLimiter` interface [found here](https://github.com/komuw/naz/blob/master/naz/ratelimiter.py) )            
To customize the default ratelimiter, for example to send at a rate of 35 requests per second.
```python
import naz

myLimiter = naz.ratelimiter.SimpleRateLimiter(send_rate=35)
cli = naz.Client(
    ...
    rateLimiter=myLimiter,
)
```

#### 4. Throttle handling
Sometimes, when a client sends requests to an SMSC/server, the SMSC may reply with an `ESME_RTHROTTLED` status.           
This can happen, say if the client has surpassed the rate at which it is supposed to send requests at, or the SMSC is under load or for whatever reason ¯\_(ツ)_/¯           
The way `naz` handles throtlling is via Throttle handlers.                
A throttle handler is a class that implements the `BaseThrottleHandler` interface as [defined here](https://github.com/komuw/naz/blob/master/naz/throttle.py)            
`naz` calls that class's `throttled` method everytime it gets a throttled(`ESME_RTHROTTLED`) response from the SMSC and it also calls that class's `not_throttled` method 
everytime it gets a response from the SMSC and the response is NOT a throttled response.            
`naz` will also call that class's `allow_request` method just before sending a request to SMSC. the `allow_request` method should return `True` if requests should be allowed to SMSC 
else it should return `False` if requests should not be sent.                 
By default `naz` uses [`naz.throttle.SimpleThrottleHandler`](https://github.com/komuw/naz/blob/master/naz/throttle.py) to handle throttling.            
The way `SimpleThrottleHandler` works is, it calculates the percentage of responses that are throttle responses and then denies outgoing requests(towards SMSC) if percentage of responses that are throttles goes above a certain metric.         
As an example if you want to deny outgoing requests if the percentage of throttles is above 1.2% over a period of 180 seconds and the total number of responses from SMSC is greater than 45, then;
```python
import naz

throttler = naz.throttle.SimpleThrottleHandler(sampling_period=180,
                                               sample_size=45,
                                               deny_request_at=1.2)
cli = naz.Client(
    ...
    throttle_handler=throttler,
)
```

#### 5. Queuing
**How does your application and `naz` talk with each other?**         
It's via a queuing interface. Your application queues messages to a queue, `naz` consumes from that queue and then `naz` sends those messages to SMSC/server.       
You can implement the queuing mechanism any way you like, so long as it satisfies the `BaseOutboundQueue` interface as [defined here](https://github.com/komuw/naz/blob/master/naz/q.py)             
Your application should call that class's `enqueue` method to -you guessed it- enqueue messages to the queue while `naz` will call the class's `dequeue` method to consume from the queue.         
Your application should enqueue a dictionary/json object with any parameters but the following are mandatory:              
```bash
{
    "version": "1",
    "smpp_command": naz.SmppCommand.SUBMIT_SM,
    "short_message": string,
    "log_id": string,
    "source_addr": string,
    "destination_addr": string
}
```  
For more information about all the parameters that are needed in the enqueued json object, consult the [documentation here](https://github.com/komuw/naz/blob/master/documentation/config.md)      

`naz` ships with a simple queue implementation called [`naz.q.SimpleOutboundQueue`](https://github.com/komuw/naz/blob/master/naz/q.py).                     
An example of using that;
```python
import asyncio
import naz

loop = asyncio.get_event_loop()
my_queue = naz.q.SimpleOutboundQueue(maxsize=1000,) # can hold upto 1000 items
cli = naz.Client(
    ...
    outboundqueue=my_queue,
)
# connect to the SMSC host
loop.run_until_complete(cli.connect())
# bind to SMSC as a tranceiver
loop.run_until_complete(cli.tranceiver_bind())

try:
    # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
    tasks = asyncio.gather(cli.dequeue_messages(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
    loop.run_forever()
except Exception as e:
    print("exception occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.stop()
```
then in your application, queue items to the queue;
```python
# queue messages to send
for i in range(0, 4):
    loop.run_until_complete(
        cli.submit_sm(
            short_message="Hello World-{0}".format(str(i)),
            log_id="myid12345",
            source_addr="254722111111",
            destination_addr="254722999999",
        )
    )
```                   
                         
                         
Here is another example, but where we now use redis for our queue;
```python
import json
import asyncio
import naz
import aioredis

class RedisExampleQueue(naz.q.BaseOutboundQueue):
    """
    use redis as our queue.
    This implements a basic FIFO queue using redis.
    Basically we use the redis command LPUSH to push messages onto the queue and BRPOP to pull them off.
    https://redis.io/commands/lpush
    https://redis.io/commands/brpop
    You should use a non-blocking redis client eg https://github.com/aio-libs/aioredis
    """
    def __init__(self):
        self.queue_name = "myqueue"
    async def enqueue(self, item):
        _redis = await aioredis.create_redis_pool(address=("localhost", 6379))
        await _redis.lpush(self.queue_name, json.dumps(item))
    async def dequeue(self):
        _redis = await aioredis.create_redis_pool(address=("localhost", 6379))
        x = await _redis.brpop(self.queue_name)
        dequed_item = json.loads(x[1].decode())
        return dequed_item

loop = asyncio.get_event_loop()
outboundqueue = RedisExampleQueue()
cli = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
)
# connect to the SMSC host
reader, writer = loop.run_until_complete(cli.connect())
# bind to SMSC as a tranceiver
loop.run_until_complete(cli.tranceiver_bind())
try:
    # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
    tasks = asyncio.gather(cli.dequeue_messages(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
    loop.run_forever()
except Exception as e:
    print("error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.stop()
```
then queue on your application side;
```python
# queue messages to send
for i in range(0, 5):
    print("submit_sm round:", i)
    loop.run_until_complete(
        cli.submit_sm(
            short_message="Hello World-{0}".format(str(i)),
            log_id="myid12345",
            source_addr="254722111111",
            destination_addr="254722999999",
        )
    )
```


#### 6. Well written(if I have to say so myself):
  - [Good test coverage](https://codecov.io/gh/komuw/naz)
  - [Passing continous integration](https://github.com/komuw/naz/actions)
  - [statically analyzed code](https://www.codacy.com/app/komuw/naz/dashboard)


## Development setup
- see [documentation on contributing](https://github.com/komuw/naz/blob/master/.github/CONTRIBUTING.md)
- **NB:** I make no commitment of accepting your pull requests.                 


## TODO
- 
