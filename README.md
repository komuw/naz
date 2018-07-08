## naz          

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/616e5c6664dd4c1abb26f34f0bf566ae)](https://www.codacy.com/app/komuw/naz)
[![Build Status](https://travis-ci.com/komuw/naz.svg?branch=master)](https://travis-ci.com/komuw/naz)
[![codecov](https://codecov.io/gh/komuw/naz/branch/master/graph/badge.svg)](https://codecov.io/gh/komuw/naz)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/komuw/naz)

naz is an SMPP client.           
It's name is derived from Kenyan hip hop artiste, Nazizi.                             

> SMPP is a protocol designed for the transfer of short message data between External Short Messaging Entities(ESMEs), Routing Entities(REs) and Short Message Service Center(SMSC). - [Wikipedia](https://en.wikipedia.org/wiki/Short_Message_Peer-to-Peer)

naz currently only supports SMPP version 3.4.       
naz has no third-party dependencies and it requires python version 3.6+


naz is in active development and it's API may change in backward incompatible ways.               
[https://pypi.python.org/pypi/naz](https://pypi.python.org/pypi/naz)                 

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
  + [Rate limiting](#3-rate-limiting)            
  + [Throttle handling](#4-throttle-handling)            
  + [Queuing](#5-queuing)            


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
outboundqueue = naz.q.SimpleOutboundQueue(maxsize=1000, loop=loop)
cli = naz.Client(
    async_loop=loop,
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
)

# queue messages to send
for i in range(0, 4):
    print("submit_sm round:", i)
    item_to_enqueue = {
        "event": "submit_sm",
        "short_message": "Hello World-{0}".format(str(i)),
        "correlation_id": "myid12345",
        "source_addr": "254722111111",
        "destination_addr": "254722999999",
    }
    loop.run_until_complete(outboundqueue.enqueue(item_to_enqueue))

# connect to the SMSC host
reader, writer = loop.run_until_complete(cli.connect())
# bind to SMSC as a tranceiver
loop.run_until_complete(cli.tranceiver_bind())

try:
    # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
    tasks = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
    loop.run_forever()
except Exception as e:
    print("exception occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.close()
```
For more information about all the parameters that `naz.Client` can take, consult the [documentation here](https://github.com/komuw/naz/blob/master/docs/config.md)    


#### 2. As a cli app
naz also ships with a commandline interface app called `naz-cli`.            
create a json config file, eg;            
`/tmp/my_config.json`
```
{
  "smsc_host": "127.0.0.1",
  "smsc_port": 2775,
  "system_id": "smppclient1",
  "password": "password",
  "outboundqueue": "myfile.ExampleQueue"
}
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
`naz-cli --config /tmp/my_config.json`
```shell
	 Naz: the SMPP client.

{'event': 'connect', 'stage': 'start'} {'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
{'event': 'connect', 'stage': 'end'} {'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
{'event': 'tranceiver_bind', 'stage': 'start'} {'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
{'event': 'send_data', 'stage': 'start', 'smpp_command': 'bind_transceiver', 'correlation_id': None} {'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
{'event': 'SimpleHook.request', 'stage': 'start', 'correlation_id': None} {'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
{'event': 'send_data', 'stage': 'end', 'smpp_command': 'bind_transceiver', 'correlation_id': None} {'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
{'event': 'tranceiver_bind', 'stage': 'end'} {'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
{'event': 'send_forever', 'stage': 'start'} {'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
```              
For more information about the `naz` config file, consult the [documentation here](https://github.com/komuw/naz/blob/master/docs/config.md)                
To see help:

`naz-cli --help`   
```shell         
naz is an SMPP client.     
example usage: naz-cli --config /path/to/my_config.json

optional arguments:
  -h, --help            show this help message and exit
  --version             The currently installed naz version.
  --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The log level to output log messages at. eg: --loglevel DEBUG
  --config CONFIG       The config file to use. eg: --config /path/to/my_config.json
```



## Features
#### 1. async everywhere
SMPP is an async protocol; the client can send a request and only get a response from SMSC/server 20mins later out of band.               
It thus makes sense to write your SMPP client in an async manner. We leverage python3's async/await to do so. And if you do not like python's inbuilt 
event loop, you can bring your own. eg; to use [uvloop](https://github.com/MagicStack/uvloop);
```python
import naz
import asyncio
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
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
by default, `naz` annotates all log events with `smsc_host` and `system_id`

##### 2.2 hooks
a hook is a class with two methods `request` and `response`, ie it implements `naz`'s BaseHook interface as [defined here](https://github.com/komuw/naz/blob/master/naz/hooks.py).           
`naz` will call the `request` method just before sending request to SMSC and also call the `response` method just after getting response from SMSC.       
the default hook that `naz` uses is `naz.hooks.SimpleHook` which does nothing but logs.             
If you wanted, for example to keep metrics of all requests and responses to SMSC in your [prometheus](https://prometheus.io/) setup;
```python
import naz
from prometheus_client import Counter

class MyPrometheusHook(naz.hooks.BaseHook):
    async def request(self, event, correlation_id=None) :
        c = Counter('my_requests', 'Description of counter')
        c.inc() # Increment by 1
    async def response(self, event, correlation_id=None):
        c = Counter('my_responses', 'Description of counter')
        c.inc() # Increment by 1

myHook = MyPrometheusHook()
cli = naz.Client(
    ...
    hook=myHook,
)
```

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
Your application should enqueue a dictionary object with any parameters but the following are mandatory:              
```bash
{
    "event": "submit_sm",
    "short_message": string,
    "correlation_id": string,
    "source_addr": string,
    "destination_addr": string
}
```
`naz` ships with a simple queue implementation called [`naz.q.SimpleOutboundQueue`](https://github.com/komuw/naz/blob/master/naz/q.py).                     
An example of using that;
```python
import asyncio
import naz

loop = asyncio.get_event_loop()
my_queue = naz.q.SimpleOutboundQueue(maxsize=1000, loop=loop) # can hold upto 1000 items
cli = naz.Client(
    ...
    async_loop=loop,
    outboundqueue=my_queue,
)
# connect to the SMSC host
loop.run_until_complete(cli.connect())
# bind to SMSC as a tranceiver
loop.run_until_complete(cli.tranceiver_bind())

try:
    # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
    tasks = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
    loop.run_forever()
except Exception as e:
    print("exception occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.close()
```
then in your application, queue items to the queue;
```python
# queue messages to send
for i in range(0, 4):
    item_to_enqueue = {
        "event": "submit_sm",
        "short_message": "Hello World-{0}".format(str(i)),
        "correlation_id": "myid12345",
        "source_addr": "254722111111",
        "destination_addr": "254722999999",
    }
    loop.run_until_complete(outboundqueue.enqueue(item_to_enqueue))
```                   
                         
                         
Here is another example, but where we now use redis for our queue;
```python
import json
import asyncio
import naz
import redis

class RedisExampleQueue(naz.q.BaseOutboundQueue):
    """
    use redis as our queue.
    This implements a basic FIFO queue using redis.
    Basically we use the redis command LPUSH to push messages onto the queue and BRPOP to pull them off.
    https://redis.io/commands/lpush
    https://redis.io/commands/brpop
    Note that in practice, you would probaly want to use a non-blocking redis
    client eg https://github.com/aio-libs/aioredis
    """
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
# connect to the SMSC host
reader, writer = loop.run_until_complete(cli.connect())
# bind to SMSC as a tranceiver
loop.run_until_complete(cli.tranceiver_bind())
try:
    # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
    tasks = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
    loop.run_forever()
except Exception as e:
    print("error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.close()
```
then queue on your application side;
```python
# queue messages to send
for i in range(0, 5):
    print("submit_sm round:", i)
    item_to_enqueue = {
        "event": "submit_sm",
        "short_message": "Hello World-{0}".format(str(i)),
        "correlation_id": "myid12345",
        "source_addr": "254722111111",
        "destination_addr": "254722999999",
    }
    loop.run_until_complete(outboundqueue.enqueue(item_to_enqueue))
```


#### 6. Well written(if I have to say so myself):
  - [Good test coverage](https://codecov.io/gh/komuw/naz)
  - [Passing continous integration](https://travis-ci.com/komuw/naz/builds)
  - [statically analyzed code](https://www.codacy.com/app/komuw/naz/dashboard)


## Development setup
- see [documentation on contributing](https://github.com/komuw/naz/blob/master/.github/CONTRIBUTING.md)
- **NB:** I make no commitment of accepting your pull requests.                 


## TODO
- 

