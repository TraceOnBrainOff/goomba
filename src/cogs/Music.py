import asyncio
import discord
from discord.ext import commands
from discord import ui as ui
import wavelink
from wavelink.ext import spotify
import typing

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
            await self.player.stop()
            await self.invoked_text_channel.send(embed=discord.Embed(title=f"Skipping track..."), delete_after=30)

    async def stop(self):
        if self.is_playing():
            self.player.queue.reset()
            await self.player.stop()
            await self.message_player.delete()
            await self.wave_music.delete_state(self.player.guild)

    async def pause_resume(self):
        await self.player.set_pause(not self.player.is_paused())

    async def disconnect_message(self):
        await self.invoked_text_channel.send(embed=discord.Embed(title=f"Empty Queue", description="Disconnecting."), delete_after=30)

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

class SkipButton(ui.Button):
    def __init__(self, voice_state: VoiceState):
        super().__init__(custom_id="skip_button", style=discord.ButtonStyle.primary, emoji="⏭️", disabled=False)
        self.voice_state = voice_state
    async def callback(self, interaction: discord.Interaction):
        await self.voice_state.skip()

class StopButton(ui.Button):
    def __init__(self, voice_state: VoiceState):
        super().__init__(custom_id="stop_button", style=discord.ButtonStyle.primary, emoji="⏹️", disabled=False)
        self.voice_state = voice_state
    async def callback(self, interaction: discord.Interaction):
        await self.voice_state.stop()

class ServiceSelector(ui.View):
    def __init__(self, wave_music, voice_state, service_results: dict):
        super().__init__(timeout=30)
        self.wave_music = wave_music
        self.voice_state = voice_state
        self.service_results = service_results
        self.createSelectorItems()
    def createSelectorItems(self):
        for service_name in self.service_results.keys():
            self.add_item(ServiceButton(self.wave_music, self.voice_state, service_name, self.service_results.get(service_name, [])))
        pass
    async def on_timeout(self):
        pass

class ServiceButton(ui.Button):
    def __init__(self, wave_music, voice_state, label, service_tracks):
        super().__init__(style=discord.ButtonStyle.primary, label=label, disabled=False)
        self.wave_music = wave_music
        self.voice_state = voice_state
        self.service_tracks = service_tracks
    async def callback(self, interaction: discord.Interaction):
        await self.wave_music.queue_tracks(self.voice_state, self.service_tracks)
        self.view.stop()

class WaveMusic(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.voice_states = {}
        token_file = open('spotify_token.txt')
        self.spotify_client_id = token_file.readline()
        self.spotify_client_secret = token_file.readline()
        token_file.close()
        self.node_pool = wavelink.NodePool()

    @commands.Cog.listener("on_ready")
    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()
        await self.node_pool.create_node(
            identifier="node1",
            bot=self.bot,
            host='0.0.0.0',
            port=2333,
            password='apeshitmonkey',
            spotify_client=spotify.SpotifyClient(client_id=self.spotify_client_id, client_secret=self.spotify_client_secret)
        )

    async def get_voice_state(self, server):
        state = self.voice_states.get(str(server.id))
        if state is None:
            state = VoiceState(self)
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
        state = await self.get_voice_state(player.guild)
        if player.queue.is_empty:
            await state.disconnect_message()
            await state.stop()
            await self.delete_state(state.player.guild)
        else:
            track = player.queue.get()
            await state.new_track_callback(track)
            await player.play(track)

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
            await ctx.send(embed=discord.Embed(title=f"On God...", description="You are not in a voice channel."), delete_after=30)
            return False
        summoned_channel = ctx.author.voice.channel
        state = await self.get_voice_state(ctx.message.guild)
        if state.player is None:
            state.player = await summoned_channel.connect(cls=wavelink.Player)
        else:
            await state.player.move_to(summoned_channel)
        state.invoked_text_channel = ctx.message.channel
        return True
    
    @commands.hybrid_command()
    async def skip(self, ctx):
        state = await self.get_voice_state(ctx.message.guild)
        await state.skip()

    async def yt_search(self, search):
        node = self.node_pool.nodes.get("node1")
        youtube_tracklist = {}
        try:
            yt_playlist = await node.get_playlist(cls=wavelink.YouTubePlaylist, identifier=search)
            if yt_playlist:
                youtube_tracklist["playlist"] = yt_playlist.tracks
            yt_track = await wavelink.YouTubeTrack.search(query=search, return_first=True)
            youtube_tracklist["track"] = [yt_track]
            return youtube_tracklist
        except Exception as e:
            print(e)
            return
    
    async def sc_search(self, search):
        soundcloud_tracklist = {}
        try:
            sc_track = await wavelink.SoundCloudTrack.search(query=search, return_first=True)
            soundcloud_tracklist["track"] = [sc_track]
            return soundcloud_tracklist
        except Exception as e:
            #print(e)
            return

    async def spot_search(self, search):
        spotify_tracklist = {}
        try:
            spotify_tracklist["album"] = await spotify.SpotifyTrack.search(query=search)
            spotify_track = await spotify.SpotifyTrack.search(query=search, return_first=True)
            spotify_tracklist["track"] = [spotify_track]
            return spotify_tracklist
        except Exception as e:
            #print(e)
            return

    async def search_services(self, search):
        y = await self.yt_search(search)
        sc = await self.sc_search(search)
        sp = await self.spot_search(search)
        return {
            "youtube": y,
            "soundcloud": sc,
            "spotify": sp,
        }
        
    @commands.hybrid_command()
    async def play(self, ctx: commands.Context, *, search):
        """Play a song with the given search query.

        If not connected, connect to our voice channel.
        """
        state = await self.get_voice_state(ctx.message.guild)
        results_map = await self.search_services(search) #keys are services, values are lists with tracks
        results_map = {k: v for k, v in results_map.items() if v is not None} #filter out nonetypes
        services_found = len(results_map.keys())
        if services_found == 0:
            await ctx.send(embed=discord.Embed(title="On God...", description="No results found"), delete_after=30)
            return
        #if not connected, join
        if state.player is None:
            success = await ctx.invoke(self.join)
            if not success:
                await ctx.send(embed=discord.Embed(title=f"On God...", description="Couldn't join the voice channel!"), delete_after=30)
                return
        if services_found == 1:
            sole_key = list(results_map.keys())[0]
            await self.queue_tracks(state, results_map.get(sole_key, [])) #
        elif services_found > 1:
            await ctx.send(embed=discord.Embed(title="Found multiple sources", description="Choose your source below"), view=ServiceSelector(self, state, results_map), delete_after=30)
       
    async def queue_tracks(self, state: VoiceState, sub_tree): #subtree: {track: wavelink track and/or playlist: list(wavelink track)}
        #check if already playing, if yes, add to queue, if not, play
        print(sub_tree)
        if type(sub_tree) == dict:
            if len(list(sub_tree.keys())) > 1:
                await state.invoked_text_channel.send(embed=discord.Embed(title="Found multiple result types", description="Choose which below"), view=ServiceSelector(self, state, sub_tree), delete_after=30)
                return #if it contains both a playlist and a track, do the selector and recursively call the function (dict is knocked down to a list)
            sub_tree = list(sub_tree.values())[0] #knocks it down from a dict to a list of track/tracks
        await state.create_player()
        for track in sub_tree:
            await state.player.queue.put_wait(track)
        await state.invoked_text_channel.send(embed=discord.Embed(title="Queued Music", description=f"Added {len(sub_tree)} tracks to queue."), delete_after=15)
        if not state.is_playing():
            track = state.player.queue.get()
            await state.player.play(track)
            await state.new_track_callback(track)

    @commands.hybrid_command()
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = await self.get_voice_state(ctx.message.guild)
        await state.pause_resume()

    @commands.hybrid_command()
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        state = await self.get_voice_state(ctx.message.guild)
        await state.stop()
        await self.delete_state(ctx.message.guild)

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