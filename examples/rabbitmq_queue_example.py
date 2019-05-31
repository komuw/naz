import os
import json
import asyncio
import functools
import concurrent

import naz
import pika


class RabbitmqExampleQueue(naz.q.BaseOutboundQueue):
    """
    use rabbitMQ as our queue.
    Note that in practice, you would probaly want to use a non-blocking rabbitMQ client.

    Since naz, uses python3's asyncio; any IO calls should not be blocking.
    This means that to communicate with rabbitMQ, we need to either:
      1. uses an async rabbitMQ client(pika is not async) or
      2. use a blocking rabbitMQ client inside a concurrent.futures.Executor

    In this class we use the latter. see;
    a) https://docs.python.org/3/library/asyncio-dev.html#running-blocking-code
    b) https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor
    """

    def __init__(self, exchange=""):
        self.queue_name = "myqueue"
        self.exchange = exchange
        self.properties = pika.BasicProperties(content_type="application/json", type="direct")

        self.connection, self.channel = None, None
        self.loop = asyncio.get_event_loop()

    def connect(self):
        """
        This method enables use to reuse connections and channels to RabbitMQ.
        This is a recommended best practice, see:
          1. https://www.cloudamqp.com/blog/2018-01-19-part4-rabbitmq-13-common-errors.html

        If RabbitMQ is low on resources, it emits Connection.Blocked to the client connection.
        Subsequently, RabbitMQ suspsends processing requests from that connection.
        This may impact BlockingConnection/BlockingChannel operations in unexpected ways.
        If the blocked state persists for a long time, the blocking operation will appear to hang.
        To break this potential deadlock, applications may configure the blocked_connection_timeout
        connection parameter when instantiating BlockingConnection.
        see:
          2. see: https://pika.readthedocs.io/en/latest/modules/adapters/blocking.html

        Other variables we have set when connecting to RabbitMQ are:
          connection_attempts is the number of socket connection attempts.
          retry_delay is the interval between socket connection attempts.
          socket_timeout is the socket timeout value.
        see:
          3. https://pika.readthedocs.io/en/stable/_modules/pika/connection.html#URLParameters
        """
        if self.connection and self.channel:
            # do not try to establish a connection
            # if it already exists
            return
        else:
            rabbitmq_url = "amqp://guest:guest@localhost:5672/%2F"
            rabbitmq_url = (
                rabbitmq_url + "?blocked_connection_timeout={blocked_connection_timeout}&"
                "connection_attempts={connection_attempts}&"
                "retry_delay={retry_delay}&"
                "socket_timeout={socket_timeout}".format(
                    blocked_connection_timeout=2,
                    connection_attempts=2,
                    retry_delay=2,
                    socket_timeout=5,
                )
            )
            connection_params = pika.URLParameters(rabbitmq_url)
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()
            channel.queue_declare(queue=self.queue_name, durable=True)

            setattr(self, "connection", connection)
            setattr(self, "channel", channel)

    async def enqueue(self, item):
        with concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix="naz-rabbitmq-thread-pool"
        ) as executor:
            await self.loop.run_in_executor(
                executor, functools.partial(self.blocking_enqueue, item=item)
            )

    def blocking_enqueue(self, item):
        self.connect()
        self.channel.publish(
            exchange=self.exchange,
            routing_key=self.queue_name,
            body=json.dumps(item),
            properties=self.properties,
            mandatory=True,
        )

    async def dequeue(self):
        with concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix="naz-rabbitmq-thread-pool"
        ) as executor:
            while True:
                item = await self.loop.run_in_executor(
                    executor, functools.partial(self.blocking_dequeue)
                )
                if item:
                    return item
                else:
                    await asyncio.sleep(5)

    def blocking_dequeue(self):
        self.connect()
        method_frame, _, body = self.channel.basic_get(self.queue_name)
        if body and method_frame:
            self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            item = json.loads(body.decode())
            return item
        else:
            return None


loop = asyncio.get_event_loop()
outboundqueue = RabbitmqExampleQueue()
cli = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password=os.getenv("password", "password"),
    outboundqueue=outboundqueue,
    enquire_link_interval=17.00,
)

item_to_enqueue = {
    "version": "1",
    "smpp_command": naz.SmppCommand.SUBMIT_SM,
    "short_message": "Hello World",
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
    tasks = asyncio.gather(cli.dequeue_messages(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
    loop.run_forever()
except Exception as e:
    print("\n\t error occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.stop()
