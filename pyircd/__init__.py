
import asyncio
from asyncio.streams import StreamReader, StreamWriter
from . import server, utils


class Ircd:
    """An instance of this contains all the state of all connected
    clientes and opened channels.
    """

    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.server_queue = asyncio.Queue()

        self.clients = []
        self.channels = []

        self.servers = []

    def add_server(self, srv):
        self.servers.append(srv)
        srv.queue = self.server_queue
        asyncio.async(srv.start_listening())

    @asyncio.coroutine
    def run_forever(self):
        while True:
            event, *params = yield from self.server_queue.get()
            if event == server.EVENT_NEW_CLIENT:
                clnt, = params
                print('New Client: {}'.format(clnt))
            elif event == server.EVENT_LOST_CLIENT:
                clnt, = params
                print('Lost Client: {}'.format(clnt))
            elif event == server.EVENT_MESSAGE:
                clnt, message = params
                print('Message: {}'.format(clnt))
                print('         {}'.format(message))
