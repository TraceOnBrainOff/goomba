import discord
import json
from .Commands import *

class GOOMBA_AutoShardedClient(discord.AutoShardedClient):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    @bot.event
    async def on_message(self, message):
        pass