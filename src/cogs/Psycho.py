import discord
from discord.ext import commands
import os
import time
import random
import math
import json
import urllib.request
import requests
import re
import datetime
import subprocess as sp
from urllib.parse import urlparse # for python 3+ use: from urllib.parse import urlparse
import psycopg2

class Psycho(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.meme_database_url = 'postgres://bgblvevu:kRNuONH2_nMNzcR3IgMt2-QER53_RhbV@dumbo.db.elephantsql.com/bgblvevu'

    @commands.Cog.listener("on_message")
    async def insult_bots(self, message: discord.Message): #bot acting as advertised
        if not message.author.bot:
            return
        if message.author.id == self.bot.user.id:
            return
        with urllib.request.urlopen("https://evilinsult.com/generate_insult.php?lang=en&type=json") as url:
            data = json.load(url)
            insult = data.get('insult', "On god...")
            await message.reply(insult, mention_author=True, delete_after=30)

    @commands.hybrid_command()
    async def neveser(self, ctx: commands.Context):
        try:
            token_file = open('neveser_token.txt')
            token = token_file.read()
            token_file.close()
        except:
            print("Put a neveser token in the root folder")
        result = urlparse(token)
        connection = psycopg2.connect(
            database = result.path[1:],
            user = result.username,
            password = result.password,
            host = result.hostname,
            port = result.port
        )
        table_name = "quote"
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        table_len = cursor.fetchone()
        cursor.execute(f"SELECT * FROM {table_name} WHERE ID={random.randint(1,table_len[0])}")
        quote = cursor.fetchone()
        await ctx.send(embed=discord.Embed(title="Neveser says", description=quote[1]))

    @commands.command()
    async def createActivity(self, ctx, activity_name='youtube'):
        """Forcefully creates a Discord Activity regardless of availibility for the current guild."""
        token_file = open('discord_token.txt')
        token = token_file.read() #Required for the authentication for whatever reason
        token_file.close() 

        activities_file = open('src/util/discordActivities.json')
        activities = json.load(activities_file)
        activity_id = activities.get(activity_name)
        voice_chat_id = ctx.author.voice.channel.id
        if voice_chat_id != None:
            res = requests.post("https://discord.com/api/v8/channels/{0}/invites".format(voice_chat_id), data = json.dumps(
                {
                    "max_age": 86400,
                    "max_uses": 0,
                    "target_application_id": activity_id,
                    "target_type": 2,
                    "temporary": False,
                    "validate": None,
                }
            ),
            headers={
                "Authorization": "Bot {0}".format(token),
                "Content-Type": "application/json"
            })
            invite = json.loads(res.content)
            if (('error' in invite.keys()) or not ('code' in invite.keys())):
                print("Error retreiving invite data.")
            await ctx.send("https://discord.com/invite/{0}".format(invite['code']))
        activities_file.close()

    @commands.command()
    async def shitpost(self, ctx, *args):
        """Makes the bot angrily say stuff."""
        if ctx.author.voice != None:
            #Join all arguments into a single message
            text = " ".join(args[:])
            if text == "":
                text = "I HAVE PEERED INTO THE ABYSS AND I HAVE FOUND THE ANSWERS I SEEK."
            encoded_text = text.encode("ascii", "ignore")
            text = encoded_text.decode() #Hacky code to remove non ascii characters because the api doesn't like it
            text.replace("\"", "")
            text.replace("\'", "")
            text.replace("’", "") #Discord.py doesn't like quotations of any kind in arguments
            #Query the VFProxy
            original_wd = os.getcwd()
            os.chdir("VFProxy")
            #Split apart the message into sub-messages with a max size of 512 (VoiceForge's API goes apeshit)
            curr_size = len(text)
            max_size = 512
            n_files = math.ceil(curr_size/max_size)
            mp3_locations = []
            for i in range(n_files):
                sub_text = text[(max_size*i):(max_size*(i+1))]
                vfcommand_out = sp.run(
                    "venv/bin/python3 main.py -voice_name Shouty -encode -no_save_wav -text \"{0}\"".format(sub_text),
                    shell = True,
                    text = True,
                    capture_output = True
                )
                #Process the resulting string
                mp3_location = re.findall(r"(?<=MP3_LOCATION:).*", vfcommand_out.stdout)[0]
                mp3_locations.append("\"{0}\"".format(mp3_location))
            today = datetime.datetime.now()
            concat_file_name = str("concat_{0}".format(today.strftime("%m-%d-%Y %H-%M-%S")))
            concatsox_out = sp.run(
                "sox {0} \"{1}.mp3\"".format(" ".join(mp3_locations[:]), concat_file_name),
                shell = True
            )
            #Convert the mp3 file with ffmpeg to 44100 and 2 channels
            
            file_name = str("shitpost_{0}".format(today.strftime("%m-%d-%Y %H-%M-%S")))
            ffmpegcommand_out = sp.run(
                "ffmpeg -i \"{0}.mp3\" -ar 48000 -ac 2 \"{1}.mp3\"".format(concat_file_name, file_name),
                shell = True
            )
            #Mix with pledge of demon in /assets for resulting file
            os.chdir(original_wd)
            playlist_dir = "assets/dw_playlist/processed"
            background_track = random.choice(os.listdir(playlist_dir))
            background_track_path = os.path.join(playlist_dir, background_track)
            soxcommand_out = sp.run(
                "sox -m \"VFProxy/{0}.mp3\" \"{1}\" \"assets/{0}.mp3\" trim 0 `soxi -D \"VFProxy/{0}.mp3\"`".format(file_name, background_track_path),
                shell = True
            )
            #Play
            voice_channel = ctx.author.voice.channel
            vc = await voice_channel.connect()
            full_dir = os.path.join(original_wd, "assets", "{0}.mp3".format(file_name))
            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=full_dir))
            # Sleep while audio is playing.
            while vc.is_playing():
                time.sleep(2.5)
            await vc.disconnect()
            os.system("rm \"assets/{0}.mp3\"".format(file_name)) #clean up
            os.system("rm \"VFProxy/{0}.mp3\"".format(file_name)) #clean up
            os.system("rm \"VFProxy/{0}.mp3\"".format(concat_file_name)) #clean up
            for mp3_location in mp3_locations:
                original_wd = os.getcwd()
                os.chdir("VFProxy")
                os.system("rm {0}".format(mp3_location)) #clean up
                os.chdir(original_wd)
        else:
            await ctx.send(str(ctx.author.name) + "is not in a channel.")