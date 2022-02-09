import discord
import json
import Commands

class GOOMBA_AutoShardedClient(discord.AutoShardedClient):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if message.content.startswith('$') == True:
            print('Message from {0.author}: {0.content}'.format(message))