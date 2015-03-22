
from asyncio.streams import StreamWriter


class Client:
    def __init__(self, server, writer: StreamWriter):
        self.remote_addr = writer.get_extra_info('peername')
        self.remote_host, self.remote_port = self.remote_addr

        self.local_addr = writer.get_extra_info('sockname')
        self.local_host, self.local_port = self.local_addr

        self.server = server
        self.writer = writer

        self.nickname = None

    def send(self, command, prefix=None, params=None):
        self.server.send(self.writer, command, prefix, params)

    def send_error(self, number, message):
        self.server.send_error(self.writer, number, message)

    def __repr__(self):
        if self.nickname is None:
            return '<Client {} on {}>'.format(
                self.remote_host, self.local_port
            )
        else:
            return '<Client {!r} {} on {}>'.format(
                self.nickname, self.remote_host, self.local_port)