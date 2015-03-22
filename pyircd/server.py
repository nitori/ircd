
import asyncio
from asyncio.streams import StreamReader, StreamWriter
from . import client, utils, replies

EVENT_NEW_CLIENT = 1
EVENT_LOST_CLIENT = 2
EVENT_MESSAGE = 3


class Server:
    name = 'irc.example.org'
    version = 'pyircd-0.1'

    def __init__(self, port=6667, host='0.0.0.0', *,
                 queue=None, loop=None, encoding='utf-8'):
        self.queue = queue
        self.bind_port = port
        self.bind_host = host
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.encoding = encoding

    def send_line(self, writer, line):
        writer.write((line + '\r\n').encode(self.encoding))

    def send(self, writer, command, prefix=None, params=None):
        buflist = []
        if params is None:
            params = []
        if prefix is not None:
            buflist.append(':{}'.format(prefix))
        if isinstance(command, int):
            command = '{:03d}'.format(command)
        buflist.append(command.upper())
        buflist.extend(params)
        if ' ' in buflist[-1]:
            buflist[-1] = ':' + buflist[-1]
        self.send_line(writer, ' '.join(buflist))

    def send_error(self, writer, number, params):
        self.send(writer, number, prefix=self.name, params=params)

    @asyncio.coroutine
    def protocol_handler(self, reader, clnt):
        buf = b''
        while True:
            try:
                data = yield from reader.read(4 << 10)
            except ConnectionResetError:
                break
            if not data:
                break
            data = data.replace(b'\r', b'\n')
            buf += data
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                line = line.rstrip()
                if line:
                    try:
                        line = line.decode(self.encoding)
                    except UnicodeDecodeError as exc:
                        clnt.send_error(
                            replies.ERR_INCORRECTENCODING,
                            ['Incorrect encoding. You must use {}.'
                             .format(self.encoding)]
                        )
                    else:
                        parsed_line = utils.parse_line(line)
                        yield from self.queue.put(
                            (EVENT_MESSAGE, clnt, parsed_line)
                        )
        yield from self.queue.put(
            (EVENT_LOST_CLIENT, clnt)
        )

    @asyncio.coroutine
    def new_client(self, reader: StreamReader, writer: StreamWriter):
        addr = writer.get_extra_info('peername')
        clnt = client.Client(self, writer)
        asyncio.async(self.protocol_handler(reader, clnt))
        yield from self.queue.put((EVENT_NEW_CLIENT, clnt))

    @asyncio.coroutine
    def start_listening(self):
        yield from asyncio.start_server(
            self.new_client, self.bind_host, self.bind_port,
            loop=self.loop)
