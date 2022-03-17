import discord
from discord.ext import commands
import subprocess as sp

class Admin(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        
    @commands.command(pass_context=True)
    async def restart(self, ctx: commands.Context):
        await ctx.send("RESTARTING THIS BITCH, BRB.")
        sp.run(
            "git pull",
            shell = True
        )
        sp.run(
            "sudo systemctl restart GOOMBA",
            shell = True
        )
