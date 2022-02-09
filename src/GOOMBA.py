import discord
import json
from .Commands import *

class GOOMBA_AutoShardedClient(discord.AutoShardedClient):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        await bot.process_commands(message)