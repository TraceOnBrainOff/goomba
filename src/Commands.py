from discord.ext import commands
import json
import requests

bot = commands.Bot(command_prefix='$')

@commands.command(name='test')
async def test(ctx):
    await ctx.send("Monky")

bot.add_command(test)

@commands.command(name='createActivity')
async def createActivity(ctx, activity_name):
    token_file = open('token.txt')
    token = token_file.read() #Required for the authentication for whatever reason
    token_file.close() 

    activities_file = open('util/discordActivities.json')
    activities = json.load(activities_file)
    activity_id = activities.get(activity_name, '880218394199220334') #Default to youtube's ID if the thing isn't found
    voice_chat_id = ctx.author.voice.channel
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
            "Authentication": "Bot {0}".format(token),
            "Content-Type": "application/json"
        })
        invite = json.loads(res)
        if (invite.error or not invite.code):
            print("Error retreiving invite data.")
        if (int(invite.code)==50013):
            print("Bot lacks the perms to do this.")
        await ctx.send("https://discord.com/invite/{0}".format(invite.code))
    activities_file.close()

bot.add_command(createActivity)