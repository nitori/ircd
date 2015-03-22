
import asyncio
from pyircd import Ircd, server


loop = asyncio.get_event_loop()
ircd = Ircd(loop=loop)
ircd.add_server(server.Server(port=6667, loop=loop))
ircd.add_server(server.Server(port=6668, loop=loop))
asyncio.async(ircd.run_forever())
loop.run_forever()
