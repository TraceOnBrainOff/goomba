import discord
import json
from src.GOOMBA import GOOMBA_AutoShardedClient

client = GOOMBA_AutoShardedClient()

token_file = open('token.txt')
token = token_file.read()
token_file.close()
client.run(token)