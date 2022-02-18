import discord
from discord.ext import commands
import json
import requests
import re
import datetime
import subprocess as sp
import os
import time

#class GOOMBA_AutoShardedBot(discord.AutoShardedBot):
#    async def on_ready(self):
#        print('Logged on as {0}!'.format(self.user))
#
#    async def on_message(self, message):
#        pass

client = commands.AutoShardedBot(command_prefix='&')

@client.event
async def on_ready():
    print('Logged on as {0}!'.format(client.user))

@client.command()
async def nigel(ctx):
    await ctx.send("Monky")

@client.command()
async def createActivity(ctx, activity_name='youtube'):
    token_file = open('token.txt')
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

@client.command()
async def shitpost(ctx, *args):
    text = " ".join(args[:])
    if text == "":
        text = "I HAVE PEERED INTO THE ABYSS AND FOUND THE ANSWERS I SEEK."
    voice_channel = ctx.author.voice.channel
    channel = None
    if voice_channel != None:
        #Query the VFProxy
        original_wd = os.getcwd()
        os.chdir("VFProxy")
        vfcommand_out = sp.run(
            "venv/bin/python3 main.py -voice_name Shouty -encode -no_save_wav -text \"{0}\"".format(text),
            shell = True,
            text = True,
            capture_output = True
        )
        #Process the resulting string
        mp3_location = re.findall(r"(?<=MP3_LOCATION:).*", vfcommand_out.stdout)[0]
        #Convert the mp3 file with ffmpeg to 44100 and 2 channels
        today = datetime.datetime.now()
        file_name = str("shitpost_{0}".format(today.strftime("%m-%d-%Y %H-%M-%S")))
        ffmpegcommand_out = sp.run(
            "ffmpeg -i \"{0}\" -ar 44100 -ac 2 \"{1}.mp3\"".format(mp3_location, file_name),
            shell = True
        )
        #Mix with pledge of demon in /assets for resulting file
        os.chdir(original_wd)
        soxcommand_out = sp.run(
            "sox -m \"VFProxy/{0}.mp3\" assets/pl.mp3 \"assets/{0}.mp3\" trim 0 `soxi -D \"VFProxy/{0}.mp3\"`".format(file_name),
            shell = True
        )
        #Play
        channel = voice_channel.name
        vc = await voice_channel.connect()
        full_dir = os.path.join(original_wd, "assets", "{0}.mp3".format(file_name))
        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=full_dir))
        # Sleep while audio is playing.
        while vc.is_playing():
            time.sleep(2.5)
        await vc.disconnect()
        os.system("rm \"assets/{0}.mp3\"".format(file_name)) #clean up
        os.system("rm \"VFProxy/{0}.mp3\"".format(file_name)) #clean up
    else:
        await ctx.send(str(ctx.author.name) + "is not in a channel.")
