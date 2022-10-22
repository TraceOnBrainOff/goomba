import discord
from discord.ext import commands
import traceback

from .cogs.Music import WaveMusic
from .cogs.Psycho import Psycho
from .cogs.OctoPrint import OctoPrint
from .cogs.Admin import Admin

class Bot(commands.AutoShardedBot):
    def __init__(self):
        all_intents = discord.Intents.all()
        super().__init__(intents=all_intents, command_prefix=commands.when_mentioned_or("&"))
        self.synced = False

    async def setup_hook(self) -> None:
        await self.add_cog(WaveMusic(self))
        await self.add_cog(Psycho(self))
        await self.add_cog(OctoPrint(self))
        await self.add_cog(Admin(self))
        return await super().setup_hook()

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        if not self.synced:
            await self.tree.sync()
            self.synced = True
        
    async def on_error(self, event_method, *args, **kwargs):
        exc = traceback.format_exc()
        print(exc)

client = Bot()