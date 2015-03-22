
import functools
import asyncio
from asyncio.streams import StreamReader, StreamWriter
from . import server, utils, exceptions, replies


def registration_required(func):
    @functools.wraps(func)
    def _wrapper(obj, client, message):
        if client.registered:
            return func(obj, client, message)
        else:
            raise exceptions.IrcError(
                replies.ERR_NOTREGISTERED, ['You are not registered.']
            )
    return _wrapper


def check_param_count(message, count):
    if len(message.params) < count:
        raise exceptions.IrcError(
            replies.ERR_NEEDMOREPARAMS,
            [message.command, 'Not enough parameters.'])


class Ircd:
    """An instance of this contains all the state of all connected
    clientes and opened channels.
    """

    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.server_queue = asyncio.Queue()

        self.nicknames = {}  # nickname.lower() -> client
        self.clients = []
        self.channels = {}  # channame.lower() -> channame
        self.memberships = []  # (channame, client, mode)

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
                client, = params
                self.clients.append(client)
                print('New Client: {}'.format(client))
            elif event == server.EVENT_LOST_CLIENT:
                client, = params
                self.clients.remove(client)
                print('Lost Client: {}'.format(client))
            elif event == server.EVENT_MESSAGE:
                client, message = params
                if message.command:
                    try:
                        self.process_message(client, message)
                    except exceptions.IrcError as exc:
                        client.send_error(exc.number, exc.params)
                    except Exception as exc:
                        client.send_error()

    def process_message(self, client, message):
        func = getattr(self, 'on_{}'.format(message.command.lower()), None)
        if func is None:
            client.send_error(
                replies.ERR_UNKNOWNCOMMAND,
                [message.command, 'Unknown command'])
            return
        func(client, message)

    def get_channel_clients(self, channel):
        for channame, client, mode in self.memberships:
            if channame.lower() == channel.lower():
                yield client, mode

    def get_client_channels(self, client):
        for channame, clnt, mode in self.memberships:
            if client is clnt:
                yield channame, mode

    def on_client_registered(self, client, message):
        client.registered = True
        client.server_send(
            replies.RPL_WELCOME,
            ['Welcome to the Internet Relay Network {}'
             .format(client.mask)]
        )
        client.server_send(
            replies.RPL_YOURHOST,
            ['Your host is {}, running version {}'
             .format(client.remote_host, client.server.version)]
        )
        client.server_send(
            replies.RPL_CREATED,
            ['This server was created today.']
        )
        client.server_send(
            replies.RPL_MYINFO,
            [client.server.name, client.server.version, 'abc', 'def']
        )
        client.server_send(
            5,
            ['NETWORK=BubiNet',
             'PREFIX=(ov)@+']
        )

        # MOTD
        client.server_send(
            replies.RPL_MOTDSTART,
            ['{} Message Of The Day'.format(client.server.name)]
        )
        with open('motd.txt', 'r', encoding='utf-8') as fp:
            for line in fp:
                client.server_send(
                    replies.RPL_MOTD,
                    ['- {}'.format(line.rstrip())]
                )
        client.server_send(
            replies.RPL_ENDOFMOTD,
            ['End of Message Of The Day']
        )

    def on_nick(self, client, message):
        check_param_count(message, 1)
        new_nickname = utils.normalize_name(message.params[0])
        utils.check_nickname(new_nickname)

        if new_nickname.lower() in self.nicknames:
            raise exceptions.IrcError(
                replies.ERR_NICKNAMEINUSE,
                [new_nickname, 'Nickname already in use']
            )

        if client.nickname is None:
            # registration process
            self.nicknames[new_nickname.lower()] = client
            client.nickname = new_nickname
            if client.user:
                self.on_client_registered(client, message)
            return

        # nick changing process
        old_nickname = client.nickname
        old_mask = client.mask
        del self.nicknames[old_nickname.lower()]
        self.nicknames[new_nickname.lower()] = client
        client.nickname = new_nickname

        # find clients to send this notification to
        recipients = set()
        for channel, mode in self.get_client_channels(client):
            recipients = recipients.union(
                {clnt for clnt, mode in self.get_channel_clients(channel)}
            )
        for other_client in recipients:
            other_client.send(
                message.command,
                old_mask,
                [new_nickname]
            )

    def on_user(self, client, message):
        check_param_count(message, 4)
        client.user = message.params[0]
        client.realname = message.params[-1]
        if client.nickname:
            self.on_client_registered(client, message)

    def on_cap(self, client, message):
        pass

    @registration_required
    def on_privmsg(self, client, message):
        check_param_count(message, 2)
        channel = utils.normalize_name(message.params[0])
        text = message.params[1]
        for other_client, mode in self.get_channel_clients(message.params[0]):
            if other_client is not client:
                other_client.send(
                    message.command,
                    client.mask,
                    [channel, text]
                )

    @registration_required
    def on_notice(self, client, message):
        pass

    @registration_required
    def on_join(self, client, message):
        channel = utils.normalize_name(message.params[0])
        utils.check_channelname(channel)
        if channel.lower() in self.channels:
            join_channel = self.channels[channel.lower()]
            mode = ''
        else:
            self.channels[channel.lower()] = channel
            join_channel = channel
            mode = '@'
        self.memberships.append((join_channel, client, mode))
        names = []
        for other_client, mode in self.get_channel_clients(join_channel):
            names.append('{}{}'.format(mode, other_client.nickname))
            other_client.send(
                message.command,
                client.mask,
                [join_channel]
            )
        client.server_send(
            replies.RPL_NAMREPLY,
            ['=', join_channel, ' '.join(names)]
        )
        client.server_send(
            replies.RPL_ENDOFNAMES,
            [join_channel, 'End of /NAMES']
        )

    @registration_required
    def on_part(self, client, message):
        pass

    @registration_required
    def on_quit(self, client, message):
        pass

    def on_ping(self, client, message):
        pass