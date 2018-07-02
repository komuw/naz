## naz          

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/616e5c6664dd4c1abb26f34f0bf566ae)](https://www.codacy.com/app/komuW/naz?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=komuw/naz&amp;utm_campaign=Badge_Grade)
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
outboundqueue = naz.q.DefaultOutboundQueue(maxsize=1000, loop=loop)
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
    gathering = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(gathering)
    loop.run_forever()
except Exception as e:
    print("exception occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.close()
```


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
  "outboundqueue": "myfile.ExampleQueue",
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

submit_sm_enqueue. correlation_id=myid12345. source_addr=254722111111. destination_addr=254722999999. log_metadata={'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
submit_sm_enqueued. event=submit_sm. correlation_id=myid12345. source_addr=254722111111. destination_addr=254722999999. log_metadata={'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
network_connecting. log_metadata={'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
network_connected. log_metadata={'smsc_host': '127.0.0.1', 'system_id': 'smppclient1'}
```              
For more information about the `naz` config file, consult the [documentation here](docs/config.md)
To see help:

`naz-cli --help`   
```shell         
usage: naz [-h] [--version] [--loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
           --config CONFIG

naz is an SMPP client. example usage: naz-cli --config /path/to/my_config.json

optional arguments:
  -h, --help            show this help message and exit
  --version             The currently installed naz version.
  --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The log level to output log messages at. eg:
                        --loglevel DEBUG
  --config CONFIG       The config file to use. eg: --config
                        /path/to/my_config.json
```



## Features
- 
- 
- Well written(if I have to say so myself):
  - [Good test coverage](https://codecov.io/gh/komuw/naz)
  - [Passing continous integration](https://circleci.com/gh/komuw/naz)
  - [High grade statically analyzed code](https://www.codacy.com/app/komuw/naz/dashboard)


## Development setup
- see [documentation on contributing](.github/CONTRIBUTING.md)
- **NB:** I make no commitment of accepting your pull requests.                 



## TODO
- 

