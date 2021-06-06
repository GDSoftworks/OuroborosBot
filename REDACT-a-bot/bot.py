import discord
from deep_translator import GoogleTranslator

TOKEN = "ODI4MjE4Nzk3ODQzNDE1MDcy.YGmY3A.PhHu5rNxzf1aAEWNech6eFkhw1M"
GUILD = "OuroborosBot Testing"

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

cleaned_list = []
with open("list.txt", "r") as swear_list:
    swear_list=swear_list.readlines()
    for swear in range(len(swear_list)):
        #swear = swear.replace("\n", "")
        swear = swear_list[swear].replace("\n", '')
        cleaned_list.append(swear)

#print(cleaned_list)
# user = ""
recorded_swears = 0
# counter = {user: recorded_swears}

#Detects and removes swears
@client.event
async def on_message(message):
    global recorded_swears
    msg = message.content.lower()
    author = message.author
    translated = GoogleTranslator(source='auto', target='en').translate(msg)
    translated_msg = translated.lower()
    #print(translated)
    for word in cleaned_list:
        if word in translated_msg:
            recorded_swears = recorded_swears + 1
            print("Number of swears recorded for: ", author, ": ",recorded_swears)
            await message.delete()
            await message.channel.send("Dont use that word 🙊! This is a warning")
    #await ctx.process_message(message)


client.run(TOKEN)
