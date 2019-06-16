=============================
  Example demo of using naz
=============================

| In this demo, we will see how to use ``naz``.


| We are going to start off on an empty directory

.. code-block:: bash

    mkdir /tmp/demo_naz/ && \
    cd /tmp/demo_naz

| Next we install ``naz`` and confirm that it is installed

.. code-block:: bash

    pip install naz && \
    naz-cli --version
      naz v0.6.1

| In order to use ``naz``, we need to have a place where messages are going to be stored before been submitted to the SMSC.
| Messages are stored in a queue in ``naz``. But whereas other smpp clients force you to use a particular queue/broker implementation(redis, rabbitMQ, kafka,, AWS SQS etc), ``naz`` is queue agnostic.
| ``naz`` will happily use any queue/broker so long as its implementation in software satisfies ``naz``'s `queueing interface <https://komuw.github.io/naz/queue.html#naz.q.BaseOutboundQueue>`_
| For this demo we will use redis as our queue of choice. So lets start a redis server, we will use docker for that;

.. code-block:: bash

    docker run -p 6379:6379 redis:5.0-alpine
      Redis is starting
      Ready to accept connections

| redis server is running a docker container and it is available for connection on the host at ``localhost:6379``
| Now we need a way for ``naz`` to be able to communicate with the redis server, ie we need to implemnet ``naz``'s `queueing interface <https://komuw.github.io/naz/queue.html#naz.q.BaseOutboundQueue>`_ for our redis server.
| Let's do that, we'll create a file called ``/tmp/demo_naz/my_queue.py``

.. code-block:: python

    import os
    import json
    import asyncio

    import naz
    import aioredis  # pip install aioredis


    class MyRedisQueue(naz.q.BaseOutboundQueue):
        """
        use redis as our queue.
        This is an implementation of the `naz.q.BaseOutboundQueue` interface
        """

        def __init__(self):
            self.host = "localhost"
            self.port = 6379
            self.password = None  # use a password in prod
            self.timeout = 8
            self.queue_name = "naz_benchmarks_queue"
            self._redis = None

        async def _get_redis(self):
            if self._redis:
                return self._redis
            self._redis = await aioredis.create_redis_pool(
                address=(self.host, self.port),
                db=0,
                password=self.password,
                minsize=1,
                maxsize=10,
                timeout=self.timeout,
            )
            return self._redis

        async def enqueue(self, item):
            _redis = await self._get_redis()
            await _redis.lpush(self.queue_name, json.dumps(item))

        async def dequeue(self):
            _redis = await self._get_redis()
            while True:
                item = await _redis.brpop(self.queue_name, timeout=self.timeout)
                if item:
                    dequed_item = json.loads(item[1].decode())
                    return dequed_item
                else:
                    await asyncio.sleep(5)


| With that we are now ready to have ``naz`` communicating with redis.
| Now what we need is an smpp client to talk to SMSC. ``naz`` is that client, but we need to instantiate a class instance of `naz Client <https://komuw.github.io/naz/client.html#naz.client.Client>`_ 
| Lets do that in a file called ``/tmp/demo_naz/my_client.py``

.. code-block:: python

    import naz
    from my_queue import MyRedisQueue

    my_naz_client = naz.Client(
        smsc_host="localhost",
        smsc_port=2775,
        system_id="smppclient1",
        password="password",
        outboundqueue=MyRedisQueue(),
    )

| We have instantiated a ``naz`` client and passed in the redis queue implementation.
| The ``naz`` client expects to be communicating with an ``SMSC`` server listening on ``localhost:2775``. 
| We are going to run an SMSC simulator in this demo, however, if you have a real SMSC server to connect to; you can replace the ``smsc_host``, ``smsc_port``, ``system_id``, ``password`` and any other SMSC related settings.
| Consult the `naz Client documentation <https://komuw.github.io/naz/client.html#naz.client.Client.__init__>`_ to see all the options that you can use to instantaite a naz Client.
| So lets run the SMSC simulator, we'll use a docker container for that.

.. code-block:: bash

    docker run -p 2775:2775 komuw/smpp_server:v0.3
      StandardConnectionHandler waiting for connection

| Okay, lets start the ``naz-cli`` which is a command line application that ships with ``naz``. When you do ``pip install naz``, the CLI was also installed.
| ``naz-cli`` typically takes one command line option ``--client`` which is the dotted path to a ``naz.Client`` instance. You can run help to see the options

.. code-block:: bash

  naz-cli --help
  usage: naz [-h] [--version] --client CLIENT [--dry-run]

  naz is an async SMPP client. example usage: naz-cli --client
  dotted.path.to.naz.Client.instance

  optional arguments:
    -h, --help       show this help message and exit
    --version        The currently installed naz version.
    --client CLIENT  The dotted path to a `naz.Client` instance. eg: --client
                    dotted.path.to.a.naz.Client.class.instance
    --dry-run        Whether we want to do a dry-run of the naz cli. This is
                    typically only used by developers who are developing naz.
                    eg: --dry-run

| Okay lets run the thing.

.. code-block:: bash

    naz-cli --client my_client.my_naz_client
      Naz: the SMPP client.
      {'timestamp': '2019-06-16 07:52:59,412', 'event': 'naz.cli.main', 'stage': 'start', 'client_id': '7WJF935MQGSJPLQ7E'}
      {'timestamp': '2019-06-16 07:52:59,435', 'event': 'naz.Client.connect', 'stage': 'start', 'log_id': 'b526gdnxfbf8sqlzz', 'smsc_host': 'localhost', 'system_id': 'smppclient1', 'client_id': '0R5ND6BSD3G4ATWUX', 'pid': 28125}

| So we have started ``naz`` with the dotted path to the naz Client that we had instantiated in the file ``/tmp/demo_naz/my_client.py``
| NB: the file where you have instantiated the naz Client needs to be in your PYTHON_PATH


| So the `naz-cli` is running and communicating to both redis server and SMSC server. However, we have not sent any messages. Let's do that now.
| We will create another file ``/tmp/demo_naz/app.py`` that contains our business logic for sending out messages

.. code-block:: python

  import asyncio
  from my_client import my_naz_client

  async def send_messages():
      """
      send out messages to customers once they make purchases.
      """
      tracking_code = "kLqk248JSK8"
      msg = "Thanks for purchasing the Awesome shoes. Tracking code: {0}".format(tracking_code)
      log_id = tracking_code
      source_addr = "AwesomeStore"
      destination_addr = "254722000111"
      await my_naz_client.submit_sm(
          short_message=msg, log_id=log_id, source_addr=source_addr, destination_addr=destination_addr
      )

  loop = asyncio.get_event_loop()
  loop.run_until_complete(send_messages())


| We can execute that file, to send out messages;

.. code-block:: python

    python app.py

| And if you look at the ``naz-cli`` logs, you should see log events of the message been sent out and the SMSC making responses.

.. code-block:: bash

  {
      "timestamp": "2019-06-16 08:08:35,975",
      "event": "naz.Client.dequeue_messages",
      "stage": "end",
      "log_id": "kLqk248JSK8",
      "smpp_command": "submit_sm",
      "send_request": True,
      "smsc_host": "localhost",
      "system_id": "smppclient1",
      "client_id": "0R5ND6BSD3G4ATWUX",
      "pid": 28125,
  }
  {
      "timestamp": "2019-06-16 08:08:35,974",
      "event": "naz.Client.send_data",
      "stage": "start",
      "smpp_command": "submit_sm",
      "log_id": "kLqk248JSK8",
      "msg": "@@@à@@@è@@@@@@@ΣCMT@££AwesomeStore@££254722000111@¥@@@@£@@@CThanks for purchasing the Awesome shoes. Tracking code: kLqk248JSK8",
      "connection_lost": False,
      "smsc_host": "localhost",
      "system_id": "smppclient1",
      "client_id": "0R5ND6BSD3G4ATWUX",
      "pid": 28125,
  }
  {
      "timestamp": "2019-06-16 08:08:35,980",
      "event": "naz.Client.receive_data",
      "stage": "end",
      "smsc_host": "localhost",
      "system_id": "smppclient1",
      "client_id": "0R5ND6BSD3G4ATWUX",
      "pid": 28125,
  }
  {
      "timestamp": "2019-06-16 08:08:35,980",
      "event": "naz.Client.command_handlers",
      "stage": "start",
      "smpp_command": "submit_sm_resp",
      "log_id": "kLqk248JSK8",
      "command_status": 0,
      "state": "Success",
      "smsc_host": "localhost",
      "system_id": "smppclient1",
      "client_id": "0R5ND6BSD3G4ATWUX",
      "pid": 28125,
  }

| ``naz`` gives you a lot more possibilities; you can change queues at will, you can change the way logging is done(including passing in your own logging implementation), you can have custom rate limiting, custom throttle handling, hooks that get called at various stages of messages passing in through naz, and so much more.

| Go through `the documentation <https://komuw.github.io/naz/>`_ to learn much more.
