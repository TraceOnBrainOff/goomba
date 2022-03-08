import asyncio
import discord
from discord.ext import commands
import wavelink
import typing

class VoiceState:
    def __init__(self, bot):
        self.player: wavelink.Player = None
        self.bot = bot
        self.invoked_text_channel: discord.TextChannel = None

    def is_playing(self):
        if self.player is None:
            return False
        return self.player.is_playing()

    def skip(self):
        if self.is_playing():
            self.player.stop()


class WaveMusic(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.voice_states = {}
        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(bot=self.bot,
            host='0.0.0.0',
            port=2333,
            password='apeshitmonkey'
        )

    def get_voice_state(self, server):
        state = self.voice_states.get(str(server.id))
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[str(server.id)] = state
        return state

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        print(f'Node: <{node.identifier}> is ready!')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        """Event fired when a song has ended."""
        #get state
        #check if the queue is empty
        #if yes, purge the queue and post a message
        #if not, queue the next song, post a message
        state = self.get_voice_state(player.guild)
        if player.queue.is_empty:
            await state.invoked_text_channel.send(f"Oooga booga no more shit in the queue, disconnecting")
            await self.delete_state(player.guild)
        else:
            track = await player.queue.get_wait()
            await state.invoked_text_channel.send(f"Next track: {track}")
            await player.play(track)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if self.bot.user.id == member.id: #check if the member is the bot
            if (before.channel != None) and (after.channel == None):  #check if it left the channel
                await self.delete_state(before.guild) #evoke stop or the equivalent function for clearing stuff

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx: commands.Context):
        #check if the author is in vc
        #check if it's already connected to the channel
        #if its in the wrong channel, move it
        """Summons the bot to join your voice channel."""
        if ctx.author.voice is None:
            await ctx.send('You are not in a voice channel.')
            return False
        summoned_channel = ctx.author.voice.channel
        state = self.get_voice_state(ctx.message.guild)
        if state.voice is None:
            state.voice = await summoned_channel.connect(cls=wavelink.Player)
        else:
            await state.voice.move_to(summoned_channel)
        state.invoked_text_channel = ctx.message.channel
        return True
    
    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        state = self.get_voice_state(ctx.message.guild)
        if not state.is_playing():
            await ctx.send('Not playing any music right now...')
            return
        state.player.stop()
        await ctx.send('Skipping...')

    @commands.command()
    async def play(self, ctx: commands.Context, *, search):
        """Play a song with the given search query.

        If not connected, connect to our voice channel.
        """
        state = self.get_voice_state(ctx.message.guild)
        #if not connected, join
        if state.voice is None:
            success = await ctx.invoke(self.join)
            if not success:
                await ctx.send("Couldn't join the voice channel!")
                return

        track = await wavelink.YouTubeTrack.search(query=search, return_first=True)
        if not track:
            await ctx.send(f"No results found.")
            return
        #check if already playing, if yes, add to queue, if not, play
        if not state.is_playing():
            await state.player.play(track)
            await ctx.send(f"Playing track: {track}")
        else:
            await state.player.queue.put_wait(track)
            await ctx.send(f"Added to queue: {track}")
    
    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        state = self.get_voice_state(ctx.message.guild)
        if not state.is_playing():
            await ctx.send('Not playing anything.')
        else:
            await ctx.send('Now playing {}'.format(state.player.track))

    
    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value : int = 100):
        """Sets the volume of the currently playing song."""
        state = self.get_voice_state(ctx.message.guild)
        if state.is_playing():
            await state.player.set_volume(value)

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.guild)
        if state.is_playing():
            await state.player.pause(True)

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.guild)
        if not state.is_playing():
            await state.player.resume()

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        guild = ctx.message.guild
        await self.delete_state(guild)

    async def delete_state(self, guild):
        state = self.get_voice_state(guild)
        if state.is_playing():
            await state.player.queue.reset()
            await state.player.stop()

        try:
            del self.voice_states[str(guild.id)]
            await state.player.disconnect()
        except:
            pass

    def __unload(self):
        for state in self.voice_states.values():
            try:
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass