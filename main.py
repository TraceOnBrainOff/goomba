import discord
import json

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))

client = MyClient()

token_file = open('token.txt')
token = token_file.read()
token_file.close()
print(token)
client.run(token)