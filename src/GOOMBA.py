import discord
from discord.ext import commands
import traceback

from .cogs.Music import WaveMusic
from .cogs.Psycho import Psycho

class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or("&"))

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    #async def on_error(self, *args, **kwargs):
    #    pass

client = Bot()
client.add_cog(WaveMusic(client))
client.add_cog(Psycho(client))

