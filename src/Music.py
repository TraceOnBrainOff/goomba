import asyncio
import discord
from discord.ext import commands
import wavelink
import typing

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice: wavelink.Player = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = wavelink.Queue()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False
        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()

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
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state
        return state

    def is_playing(self):
        pass

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        print(f'Node: <{node.identifier}> is ready!')

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx):
        #check if the author is in vc
        #check if it's already connected to the channel
        #if its in the wrong channel, move it
        """Summons the bot to join your voice channel."""
        if ctx.author.voice is None:
            await self.bot.say('You are not in a voice channel.')
            return False
        summoned_channel = ctx.author.voice.channel
        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await summoned_channel.connect(cls=wavelink.Player)
        else:
            await state.voice.move_to(summoned_channel)
        return True
    
    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return
        state.skip()
        await self.bot.say('Skipping...')

    @commands.command()
    async def play(self, ctx: commands.Context, *, search: typing.Union[wavelink.SoundCloudTrack, wavelink.YouTubeTrack]):
        """Play a song with the given search query.

        If not connected, connect to our voice channel.
        """
        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            success = await ctx.invoke(self.join)
            if not success:
                return
        #if not connected, join
        #check if it's in the same channel as the author, if not, move
        #check if already playing, if yes, add to queue, if not, play
        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect()
        else:
            vc: wavelink.Player = ctx.voice_client

        await vc.play(search)
    
    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            await self.bot.say('Now playing {}'.format(state.current))

    
    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value : int):
        """Sets the volume of the currently playing song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.voice
            player.volume = value / 100
            await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.voice
            player.pause()

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.voice
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.voice
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
        except:
            pass