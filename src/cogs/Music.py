import asyncio
import discord
from discord.ext import commands
import wavelink
import typing

class VoiceState:
    def __init__(self, bot):
        self.voice: wavelink.Player = None
        self.bot = bot
        self.original_channel: discord.TextChannel = None

    def is_playing(self):
        if self.voice is None:
            return False
        return self.voice.is_playing()

    @property
    def player(self):
        return self.voice

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
    async def on_wavelink_track_end(self, player, track, reason):
        """Event fired when a song has ended."""
        track = await player.queue.get_wait()
        await player.play(track)
        

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
        state.original_channel = ctx.message.channel
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