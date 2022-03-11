import discord
from discord.ext import commands
import octorest

class OctoPrint(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        bot.loop.create_task(self.connect_printer())
    
    async def connect_printer(self):
        await self.bot.wait_until_ready()
        try:
            client = octorest.OctoRest(url="127.0.0.1:5000", apikey=apikey)
            return client
        except ConnectionError as ex:
            # Handle exception as you wish
            print(ex)