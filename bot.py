import discord
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN') #edit .env file
GUILD = os.getenv("DISCORD_GUILD")

client = discord.Client()

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print( #prints if the bot is connected to the server
        f'{client.user} is connected to the following server:\n'
        f'{guild.name}(id: {guild.id})'
    )

#New Member join
@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to the GoldenDragons Discord server!'
    )
    
    
client.run(TOKEN)

