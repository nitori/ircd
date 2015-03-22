
from asyncio.streams import StreamWriter


class Client:
    def __init__(self, server, writer: StreamWriter):
        self.remote_addr = writer.get_extra_info('peername')
        self.remote_host, self.remote_port = self.remote_addr

        self.local_addr = writer.get_extra_info('sockname')
        self.local_host, self.local_port = self.local_addr

        self.server = server
        self.writer = writer

        # state
        self.registered = False
        self.nickname = None
        self.user = None
        self.realname = None
        self.vhost = None

    @property
    def mask(self):
        if self.vhost is None:
            host = self.remote_host
        else:
            host = self.vhost
        return '{}!{}@{}'.format(
            self.nickname, self.user, host)

    def send(self, command, prefix=None, params=None):
        self.server.send(self.writer, command, prefix, params)

    def send_error(self, number, params):
        if self.nickname is None:
            outparams = ['*'] + params
        else:
            outparams = [self.nickname] + params
        self.server.send_error(self.writer, number, outparams)

    def server_send(self, command, params=None):
        """Send as the server.
        Of the form:
        :server.name COMMAND nickname params*
        """
        if params is None:
            params = []
        if self.nickname is None:
            params = ['*'] + params
        else:
            params = [self.nickname] + params
        self.send(command, self.server.name, params)

    def __hash__(self):
        return hash(id(self))

    def __repr__(self):
        if self.nickname is None:
            return '<Client {} on {}>'.format(
                self.remote_host, self.local_port
            )
        else:
            return '<Client {!r} {} on {}>'.format(
                self.nickname, self.remote_host, self.local_port)