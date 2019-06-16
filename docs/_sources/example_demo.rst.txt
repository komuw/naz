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

