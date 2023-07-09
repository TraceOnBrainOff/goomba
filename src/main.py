import discord
import json
from GOOMBA import *

token_file = open('discord_token.txt')
token = token_file.read()
token_file.close()
client.run(token)