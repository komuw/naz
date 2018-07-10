import json
import asyncio

import naz
import pika


class RabbitmqExampleQueue(naz.q.BaseOutboundQueue):
    """
    use rabbitMQ as our queue.
    Note that in practice, you would probaly want to use a non-blocking rabbitMQ client.
    """

    def __init__(self):
        self.queue_name = "myqueue"
        parameters = pika.URLParameters("amqp://guest:guest@localhost:5672/%2F")
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    async def enqueue(self, item):
        self.channel.queue_declare(queue=self.queue_name)
        self.channel.publish(
            exchange="",
            routing_key=self.queue_name,
            body=json.dumps(item),
            properties=pika.BasicProperties(content_type="text/plain", delivery_mode=1),
        )

    async def dequeue(self):
        self.channel.queue_declare(queue=self.queue_name)
        _, _, body = self.channel.basic_get(self.queue_name)
        item = json.loads(body.decode())
        return item


loop = asyncio.get_event_loop()
outboundqueue = RabbitmqExampleQueue()
cli = naz.Client(
    async_loop=loop,
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
)

item_to_enqueue = {
    "smpp_event": "submit_sm",
    "short_message": "Hello World",
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
    print("\n\t error occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.close()
