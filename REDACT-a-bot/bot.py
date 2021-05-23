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

#Reads in swear list
with open("list.txt", "r") as swear_list:
    swears=swear_list.readlines()

#Detects and removes swears
@client.event
async def on_message(message):
    msg = message.content
    for word in swears:
        if word in msg:
            await message.delete()
            await ctx.send("Dont use that word 🙊! This is a warning")
    #I have no idea why this works...
    await ctx.process_message(message)


client.run(TOKEN)
