import discord
import json
from GOOMBA import *
import os

token = ""
with open("/run/secrets/discord_token") as f:
    token = f.read()
client.run(token)