
import socket
import struct
import asyncio



# todo:
# 1. add configurable retries
# 2. add configurable rate limits. our rate limits should be tight
# 3. metrics, what is happening

class DefaultSequenceGenerator(object):
    """
    sequence_number are 4 octets Integers which allows SMPP requests and responses to be correlated.
    The sequence_number should increase monotonically.
    And they ought to be in the range 0x00000001 to 0x7FFFFFFF
    see section 3.2 of smpp ver 3.4 spec document.

    You can supply your own sequence generator, so long as it respects the range defined in the SMPP spec.
    """
    MIN_SEQUENCE_NUMBER = 0x00000001
    MAX_SEQUENCE_NUMBER = 0x7FFFFFFF
    def __init__(self):
        self.sequence_number = self.MIN_SEQUENCE_NUMBER
    def next_sequence(self):
        if self.sequence_number == self.MAX_SEQUENCE_NUMBER:
            # wrap around
            self.sequence_number = self.MIN_SEQUENCE_NUMBER
        else:
            self.sequence_number += 1
        return self.sequence_number


class Client:
    """
    """
    def __init__(self,
                 async_loop,
                 SMSC_HOST,
                 SMSC_PORT,
                 system_id,
                 password,
                 system_type='',
                 addr_ton=0,
                 addr_npi=0,
                 address_range='',
                 encoding='utf8',
                 interface_version=34,
                 sequence_generator=None):
        self.async_loop = async_loop
        self.SMSC_HOST = SMSC_HOST
        self.SMSC_PORT = SMSC_PORT
        self.system_id = system_id
        self.password = password 
        self.system_type = system_type
        self.interface_version = interface_version
        self.addr_ton = addr_ton
        self.addr_npi = addr_npi
        self.address_range = address_range
        self.encoding = encoding
        if not sequence_generator:
            self.sequence_generator = DefaultSequenceGenerator()
        self.MAX_SEQUENCE_NUMBER = 0x7FFFFFFF

        # see section 5.1.2.1 of smpp ver 3.4 spec document
        self.command_ids = {
            'bind_transceiver': 0x00000009,
        }

        # see section 5.1.3 of smpp ver 3.4 spec document
        self.command_statuses = {
            'ESME_ROK': 0x00000000,
        }

        self.reader = None
        self.writer = None

    async def connect(self):
        reader, writer = await asyncio.open_connection(self.SMSC_HOST, self.SMSC_PORT, loop=self.async_loop)
        self.reader = reader
        self.writer = writer
        return reader, writer

    async def tranceiver_bind(self):
        # body
        body = b''
        body = body + \
        bytes(self.system_id + chr(0), self.encoding) + \
        bytes(self.password + chr(0), self.encoding) + \
        bytes(self.system_type + chr(0), self.encoding) + \
        struct.pack('>I', self.interface_version) + \
        struct.pack('>I', self.addr_ton) + \
        struct.pack('>I', self.addr_npi) + \
        bytes(self.address_range + chr(0), self.encoding)

        # header
        command_length = 16 + len(body) # 16 is for headers
        command_id = self.command_ids['bind_transceiver']
        command_status =  self.command_statuses['ESME_ROK'] #the status for success see section 5.1.3
        sequence_number = self.sequence_generator.next_sequence()
        if sequence_number > self.MAX_SEQUENCE_NUMBER:
            # prevent third party sequence_generators from ruining our party
            raise ValueError('the sequence_number: {0} is greater than the max: {1} allowed by SMPP spec.'.format(sequence_number, self.MAX_SEQUENCE_NUMBER))
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        await self.send_data(full_pdu, self.writer)
        return full_pdu

    async def send_data(self, msg, writer):
        """
        This method does not block; it buffers the data and arranges for it to be sent out asynchronously.
        see: https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamWriter.write
        """
        # todo: look at `set_write_buffer_limits` and `get_write_buffer_limits` methods
        if isinstance(msg, str):
            msg = bytes(msg, 'utf8')
        writer.write(msg)
        await writer.drain()

    async def receive_data(self, reader):
        """
        """
        # todo: look at `pause_reading` and `resume_reading` methods
        command_length_header_data = await reader.read(4)
        total_pdu_length = struct.unpack('>I', command_length_header_data)[0]

        MSGLEN = total_pdu_length - 4
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = await reader.read(min(MSGLEN - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        full_pdu_data = command_length_header_data + b''.join(chunks) 
        return full_pdu_data


loop = asyncio.get_event_loop()
cli = Client(async_loop=loop,
             SMSC_HOST='127.0.0.1',
             SMSC_PORT=2775,
             system_id='smppclient1',
             password='password')

reader, writer = loop.run_until_complete(cli.connect())

loop.run_until_complete(cli.tranceiver_bind())

received = loop.run_until_complete(cli.receive_data(reader))
# received = cli.myreceive()
print("received", received)
loop.run_forever()
loop.close()