import discord
from discord.ext import commands
import traceback

from .cogs.Music import WaveMusic
from .cogs.Psycho import Psycho
from .cogs.OctoPrint import OctoPrint
from .cogs.Admin import Admin

class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or("&"))

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        self.app_info = await self.application_info()
        self.owner = self.app_info.owner

    async def on_error(self, event_method, *args, **kwargs):
        exc = traceback.format_exc()
        await self.owner.send(f"```\n{exc}```")
        print(exc)

client = Bot()
client.add_cog(WaveMusic(client))
client.add_cog(Psycho(client))
client.add_cog(OctoPrint(client))
client.add_cog(Admin(client))
