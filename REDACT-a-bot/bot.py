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


with open("list.txt", "r") as swear_list:
    swear_list=swear_list.readlines()
    for swear in range(len(swear_list)):
        #swear = swear.replace("\n", "")
        swear = swear_list[swear].replace("\n", '')
        cleaned_list = []
        cleaned_list.append(swear)



"""
#Detects and removes swears
@client.event
async def on_message(ctx, message):
    global swears
    msg = message.content.lower()
    for word in swears:
        if word in msg:
            await message.delete()
            await message.channel.send("Dont use that word 🙊! This is a warning")
    await ctx.process_message(message)


client.run(TOKEN)
"""