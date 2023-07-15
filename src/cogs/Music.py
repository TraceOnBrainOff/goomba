import asyncio
import discord
from discord.ext import commands
from discord import ui as ui
import wavelink
import typing
import os

class VoiceState:
    def __init__(self, parent):
        self.player: wavelink.Player = None
        self.bot = parent.bot
        self.wave_music = parent
        self.invoked_text_channel: discord.TextChannel = None
        self.message_player = None

    async def create_player(self):
        self.player_view = PlayerView(self)
        if self.message_player == None:
            self.message_player = await self.invoked_text_channel.send(
                embed=discord.Embed(title="Goomba Player", description="Use the buttons below..."),
                view = PlayerView(self)
            )

    def is_playing(self):
        if self.player is None:
            return False
        return self.player.is_playing()

    async def skip(self):
        if self.is_playing():
            await self.player.stop(force = True)
            await self.invoked_text_channel.send(embed=discord.Embed(title=f"Skipping track..."), delete_after=5)

    async def stop(self):
        if self.is_playing():
            self.player.queue.reset()
            await self.player.stop()
            await self.message_player.delete()
            await self.wave_music.delete_state(self.player.guild)

    async def pause_resume(self):
        if not self.player.is_paused():
            await self.player.pause()
        else:
            await self.player.resume()

    async def disconnect_message(self):
        await self.invoked_text_channel.send(embed=discord.Embed(title=f"Empty Queue", description="Disconnecting."), delete_after=5)

    def playing_embed(self, track):
        emb = discord.Embed(title=f"Currently playing", description=f"{track}")
        #if track.thumbnail:
        #    emb.set_thumbnail(url=track.thumbnail)
        return emb

    async def update_playing_embed(self, track):
        if self.message_player == None:
            self.message_player = await self.invoked_text_channel.send(embed=self.playing_embed(track), view=self.player_view)
        else:
            try:
                await self.message_player.edit(embed=self.playing_embed(track), view=self.player_view)
            except:
                self.message_player = await self.invoked_text_channel.send(embed=self.playing_embed(track), view=self.player_view)

    async def new_track_callback(self, track):
        await self.update_playing_embed(track)

class PlayerView(ui.View):
    def __init__(self, voice_state: VoiceState):
        super().__init__(timeout=None)
        self.voice_state = voice_state
        self.pause_button = PauseButton(self.voice_state)
        self.skip_button = SkipButton(self.voice_state)
        self.stop_button = StopButton(self.voice_state)
        self.createPlayerItems()
    def createPlayerItems(self):
        self.add_item(
            self.pause_button
        )
        self.add_item(
            self.skip_button
        )
        self.add_item(
            self.stop_button
        )

class PauseButton(ui.Button):
    def __init__(self, voice_state: VoiceState):
        super().__init__(custom_id="pause_button", style=discord.ButtonStyle.primary, emoji="⏯️", disabled=False)
        self.voice_state = voice_state
    async def callback(self, interaction: discord.Interaction):
        await self.voice_state.pause_resume()
        try: #All three of these can sometimes be responded to multiple times so lets ignore the exception
            await interaction.response.defer()
        except InteractionResponded:
            pass

class SkipButton(ui.Button):
    def __init__(self, voice_state: VoiceState):
        super().__init__(custom_id="skip_button", style=discord.ButtonStyle.primary, emoji="⏭️", disabled=False)
        self.voice_state = voice_state
    async def callback(self, interaction: discord.Interaction):
        await self.voice_state.skip()
        try:
            await interaction.response.defer()
        except InteractionResponded:
            pass

class StopButton(ui.Button):
    def __init__(self, voice_state: VoiceState):
        super().__init__(custom_id="stop_button", style=discord.ButtonStyle.primary, emoji="⏹️", disabled=False)
        self.voice_state = voice_state
    async def callback(self, interaction: discord.Interaction):
        await self.voice_state.stop()
        try:
            await interaction.response.defer()
        except InteractionResponded:
            pass

class WaveMusic(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.voice_states = {}
        self.node_pool = wavelink.NodePool()

    @commands.Cog.listener("on_ready")
    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        lavalink_password = ""
        with open("/run/secrets/lavalink_password") as f:
            lavalink_password = f.read()
        await self.bot.wait_until_ready()
        node: wavelink.Node = wavelink.Node(id='node1', uri='lavalink:2333', password=lavalink_password)
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])

    async def get_voice_state(self, server):
        state = self.voice_states.get(str(server.id))
        if state is None:
            state = VoiceState(self)
            self.voice_states[str(server.id)] = state
        return state

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f"Node {node.id} is ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        """Event fired when a song has ended."""
        #get state
        #check if the queue is empty
        #if yes, purge the queue and post a message
        #if not, queue the next song, post a message
        state = await self.get_voice_state(payload.player.guild)
        if payload.player.queue.is_empty:
            await state.disconnect_message()
            await state.stop()
            await self.delete_state(state.player.guild)
        else:
            track = payload.player.queue.get()
            await state.new_track_callback(track)
            await payload.player.play(track)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if self.bot.user.id == member.id: #check if the member is the bot
            if (before.channel != None) and (after.channel == None):  #check if it left the channel
                await self.delete_state(before.channel.guild) #evoke stop or the equivalent function for clearing stuff

    @commands.hybrid_command()
    async def join(self, ctx: commands.Context):
        #check if the author is in vc
        #check if it's already connected to the channel
        #if its in the wrong channel, move it
        """Summons the bot to join your voice channel."""
        if (ctx.author.voice is None):
            await ctx.send(embed=discord.Embed(title=f"On God...", description="You are not in a voice channel."), delete_after=5)
            return False
        summoned_channel = ctx.author.voice.channel
        state = await self.get_voice_state(ctx.message.guild)
        if state.player is None:
            state.player = await summoned_channel.connect(cls=wavelink.Player)
        else:
            await state.player.move_to(summoned_channel)
        state.invoked_text_channel = ctx.message.channel
        try:
            await ctx.defer(ephemeral = True)
        except InteractionResponded:
            pass
        return True
    
    @commands.hybrid_command()
    async def skip(self, ctx):
        state = await self.get_voice_state(ctx.message.guild)
        await state.skip()
        try:
            await ctx.defer(ephemeral = True)
        except InteractionResponded:
            pass
        return
        
    @commands.hybrid_command()
    async def play(self, ctx: commands.Context, *, search):
        """Play a song with the given search query.

        If not connected, connect to our voice channel.
        """
        track = await self.node_pool.get_tracks(search, cls=wavelink.YouTubeTrack)
        state = await self.get_voice_state(ctx.message.guild)
        #if not connected, join
        if state.player is None:
            success = await ctx.invoke(self.join)
            if not success:
                await ctx.send(embed=discord.Embed(title=f"On God...", description="Couldn't join the voice channel!"), delete_after=5)
                return
        await self.queue_tracks(state, track)
        try:
            await ctx.defer(ephemeral = True)
        except InteractionResponded:
            pass
        return

    @commands.hybrid_command()
    async def playlist(self, ctx: commands.Context, *, search):
        """Play a song with the given search query.

        If not connected, connect to our voice channel.
        """
        yt_playlist = await self.node_pool.get_playlist(search, cls=wavelink.YouTubePlaylist)
        state = await self.get_voice_state(ctx.message.guild)
        #if not connected, join
        if state.player is None:
            success = await ctx.invoke(self.join)
            if not success:
                await ctx.send(embed=discord.Embed(title=f"On God...", description="Couldn't join the voice channel!"), delete_after=5)
                return
        await self.queue_tracks(state, yt_playlist.tracks)
        try:
            await ctx.defer(ephemeral = True)
        except InteractionResponded:
            pass
        return
       
    async def queue_tracks(self, state: VoiceState, tracks):
        #check if already playing, if yes, add to queue, if not, play
        await state.create_player()
        for track in tracks:
            print(track)
            await state.player.queue.put_wait(track)
        await state.invoked_text_channel.send(embed=discord.Embed(title="Queued Music", description=f"Added {len(tracks)} tracks to queue."), delete_after=5)
        if not state.is_playing():
            track = state.player.queue.get()
            await state.player.play(track)
            await state.new_track_callback(track)

    @commands.hybrid_command()
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = await self.get_voice_state(ctx.message.guild)
        await state.pause_resume()
        try:
            await ctx.defer(ephemeral = True)
        except InteractionResponded:
            pass

    @commands.hybrid_command()
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        state = await self.get_voice_state(ctx.message.guild)
        await state.stop()
        await self.delete_state(ctx.message.guild)
        try:
            await ctx.defer(ephemeral = True)
        except InteractionResponded:
            pass

    async def delete_state(self, guild):
        state = await self.get_voice_state(guild)
        try:
            del self.voice_states[str(guild.id)]
            await state.player.disconnect()
        except:
            pass

    async def __unload(self):
        for state in self.voice_states.values():
            try:
                if state.player:
                    await self.bot.loop.create_task(state.player.disconnect())
            except:
                pass