=====================
  Introduction to naz
=====================
naz is an async SMPP client.
It's name is derived from Kenyan hip hop artiste, Nazizi.

``SMPP is a protocol designed for the transfer of short message data between External Short Messaging Entities(ESMEs), Routing Entities(REs) and Short Message Service Center(SMSC).`` - `Wikipedia <https://en.wikipedia.org/wiki/Short_Message_Peer-to-Peer>`_

| naz currently only supports SMPP version 3.4.
| naz has no third-party dependencies and it requires python version 3.6+

naz is in active development and it's API may change in backward incompatible ways.

**Table of Contents**

.. contents::
    :local:
    :depth: 1

1 Installation
=================
``pip install naz``


2 Usage
===============

2.1 As a library
==================

.. code-block:: python

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
            "version": "1",
            "smpp_command": naz.SmppCommand.SUBMIT_SM,
            "short_message": "Hello World-{0}".format(str(i)),
            "log_id": "myid12345",
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
        loop.stop()


NB:

* (a) For more information about all the parameters that `naz.Client` can take, consult the `documentation here <https://github.com/komuw/naz/blob/master/documentation/config.md>`_
* (b) More examples can be found `here <https://github.com/komuw/naz/tree/master/examples>`_ 
* (c) if you need an SMSC server/gateway to test with, you can use the `docker-compose <https://github.com/komuw/naz/blob/master/docker-compose.yml>`_ file in the ``naz`` repo to bring up an SMSC simulator.
      That docker-compose file also has a redis and rabbitMQ container if you would like to use those as your `naz.q.BaseOutboundQueue`.



2.2 As a cli app
=====================
``naz`` also ships with a commandline interface app called ``naz-cli`` (it is also installed by default when you `pip install naz`).

create a json config file, eg; `/tmp/my_config.json`

.. code-block:: bash

    {
    "smsc_host": "127.0.0.1",
    "smsc_port": 2775,
    "system_id": "smppclient1",
    "password": "password",
    "outboundqueue": "myfile.ExampleQueue"
    }

and a python file, `myfile.py` (in the current working directory) with the contents:

.. code-block:: python

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


then run:
``naz-cli --config /tmp/my_config.json``

NB:

* (a) For more information about the naz config file, consult the `documentation here <https://github.com/komuw/naz/blob/master/documentation/config.md>`_
* (b) More examples can be found `here <https://github.com/komuw/naz/tree/master/examples>`_ 
      As an example, start the SMSC simulator(``docker-compose up``) then in another terminal run, 
      ``naz-cli --config examples/example_config.json``


3 Features
=====================

3.1 async everywhere
=====================
| SMPP is an async protocol; the client can send a request and only get a response from SMSC/server 20mins later out of band.
| It thus makes sense to write your SMPP client in an async manner. We leverage python3's async/await to do so.
| And if you do not like python's inbuilt event loop, you can bring your own. eg; to use uvloop;

.. code-block:: python

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

3.2 monitoring and observability
==========================================

3.2.1 logging
=====================
| In ``naz`` you have the ability to annotate all the log events that naz will generate with anything you want.
| So, for example if you wanted to annotate all log-events with a release version and your app's running environment.

.. code-block:: python

    import naz
    cli = naz.Client(
        ...
        log_metadata={ "environment": "production", "release": "canary"},
    )

| and then these will show up in all log events.
| by default, naz annotates all log events with smsc_host, system_id and client_id

``naz`` also gives you the ability to supply your own logger. 
For example if you wanted ``naz`` to use key=value style of logging, then just create a logger that does just that:

.. code-block:: python

    import naz

    class KVlogger(naz.logger.BaseLogger):
        def __init__(self):
            self.logger = logging.getLogger("myKVlogger")
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            if not self.logger.handlers:
                self.logger.addHandler(handler)
            self.logger.setLevel("DEBUG")
        def bind(self, loglevel, log_metadata):
            pass
        def log(self, level, log_data):
            # implementation of key=value log renderer
            message = ", ".join("{0}={1}".format(k, v) for k, v in log_data.items())
            self.logger.log(level, message)

    kvLog = KVlogger()
    cli = naz.Client(
        ...
        log_handler=kvLog,
    )


``naz`` also gives you the ability to supply your own logger. 
For example if you wanted ``naz`` to use key=value style of logging, then just create a logger that does just that:

.. code-block:: python

    import naz

    class KVlogger(naz.logger.BaseLogger):
        def __init__(self):
            self.logger = logging.getLogger("myKVlogger")
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            if not self.logger.handlers:
                self.logger.addHandler(handler)
            self.logger.setLevel("DEBUG")
        def bind(self, loglevel, log_metadata):
            pass
        def log(self, level, log_data):
            # implementation of key=value log renderer
            message = ", ".join("{0}={1}".format(k, v) for k, v in log_data.items())
            self.logger.log(level, message)

    kvLog = KVlogger()
    cli = naz.Client(
        ...
        log_handler=kvLog,
    )


3.2.2 hooks
=====================
| A hook is a class with two methods `request` and `response`, ie it implements naz's ``naz.hooks.BaseHook`` interface.
| ``naz`` will call the `request` method just before sending request to SMSC and also call the `response` method just after getting response from SMSC.
| The default hook that naz uses is ``naz.hooks.SimpleHook`` which just logs the request and response.
| If you wanted, for example to keep metrics of all requests and responses to SMSC in your prometheus setup;

.. code-block:: python

    import naz
    from prometheus_client import Counter

    class MyPrometheusHook(naz.hooks.BaseHook):
        async def request(self, smpp_command, log_id, hook_metadata):
            c = Counter('my_requests', 'Description of counter')
            c.inc() # Increment by 1
        async def response(self,
                        smpp_command,
                        log_id,
                        hook_metadata,
                        smsc_response):
            c = Counter('my_responses', 'Description of counter')
            c.inc() # Increment by 1

    myHook = MyPrometheusHook()
    cli = naz.Client(
        ...
        hook=myHook,
    )

another example is if you want to update a database record whenever you get a delivery notification event;

.. code-block:: python

    import sqlite3
    import naz

    class SetMessageStateHook(naz.hooks.BaseHook):
        async def request(self, smpp_command, log_id, hook_metadata):
            pass
        async def response(self,
                        smpp_command,
                        log_id,
                        hook_metadata,
                        smsc_response):
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


3.3 Rate limiting
=====================
| Sometimes you want to control the rate at which the client sends requests to an SMSC/server. ``naz`` lets you do this, by allowing you to specify a custom rate limiter.
| By default, naz uses a simple token bucket rate limiting algorithm implemented in ``naz.ratelimiter.SimpleRateLimiter``
| You can customize naz's ratelimiter or even write your own ratelimiter (if you decide to write your own, you just have to satisfy the ``naz.ratelimiter.BaseRateLimiter`` interface)
| To customize the default ratelimiter, for example to send at a rate of 35 requests per second.

.. code-block:: python

    import logging
    import naz
    logger = logging.getLogger("naz.rateLimiter")

    myLimiter = naz.ratelimiter.SimpleRateLimiter(logger=logger, send_rate=35)
    cli = naz.Client(
        ...
        rateLimiter=myLimiter,
    )

3.4 Throttle handling
=====================
| Sometimes, when a client sends requests to an SMSC/server, the SMSC may reply with an ESME_RTHROTTLED status.
| This can happen, say if the client has surpassed the rate at which it is supposed to send requests at, or the SMSC is under load or for whatever reason ¯_(ツ)_/¯

The way naz handles throtlling is via Throttle handlers.
A throttle handler is a class that implements the ``naz.BaseThrottleHandler``

By default naz uses ``naz.throttle.SimpleThrottleHandler`` to handle throttling.
As an example if you want to deny outgoing requests if the percentage of throttles is above 1.2% over a period of 180 seconds and the total number of responses from SMSC is greater than 45, then;

.. code-block:: python

    from naz.throttle import SimpleThrottleHandler
    throttler = SimpleThrottleHandler(sampling_period=180,
                                    sample_size=45,
                                    deny_request_at=1.2)
    cli = naz.Client(
        ...
        throttle_handler=throttler,
    )

3.5 Queuing
=====================
`How does your application and naz talk with each other?`

It's via a queuing interface. Your application queues messages to a queue, ``naz`` consumes from that queue and then naz sends those messages to SMSC/server.

You can implement the queuing mechanism any way you like, so long as it satisfies the ``naz.q.BaseOutboundQueue``

| Your application should call that class's enqueue method to enqueue messages.
| Your application should enqueue a dictionary/json object with any parameters but the following are mandatory:

.. code-block:: bash

    {
        "version": "1",
        "smpp_command": naz.SmppCommand.SUBMIT_SM,
        "short_message": string,
        "log_id": string,
        "source_addr": string,
        "destination_addr": string
    }

For more information about all the parameters that are needed in the enqueued json object, consult the `documentation <https://github.com/komuw/naz/blob/master/documentation/config.md#2-naz-enqueued-message-protocol>`_ 

| naz ships with a simple queue implementation called ``naz.q.SimpleOutboundQueue``
| **NB:** ``naz.q.SimpleOutboundQueue`` should only be used for demo/test purposes.

An example of using that queue;

.. code-block:: python

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
        loop.stop()
    then in your application, queue items to the queue;

    # queue messages to send
    for i in range(0, 4):
        item_to_enqueue = {
            "version": "1",
            "smpp_command": naz.SmppCommand.SUBMIT_SM,
            "short_message": "Hello World-{0}".format(str(i)),
            "log_id": "myid12345",
            "source_addr": "254722111111",
            "destination_addr": "254722999999",
        }
        loop.run_until_complete(outboundqueue.enqueue(item_to_enqueue))

then in your application, queue items to the queue;

.. code-block:: python

    # queue messages to send
    for i in range(0, 4):
        item_to_enqueue = {
            "version": "1",
            "smpp_command": naz.SmppCommand.SUBMIT_SM,
            "short_message": "Hello World-{0}".format(str(i)),
            "log_id": "myid12345",
            "source_addr": "254722111111",
            "destination_addr": "254722999999",
        }
        loop.run_until_complete(outboundqueue.enqueue(item_to_enqueue))