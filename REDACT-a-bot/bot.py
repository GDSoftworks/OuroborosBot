import discord
from deep_translator import GoogleTranslator
from time import sleep
import jellyfish
import multiprocessing
TOKEN = (open("TOKEN", "r")).readline()
GUILD = (open("GUILD", "r")).readline()

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

#Reads in list of swears
cleaned_list = []
with open("list.txt", "r") as swear_list:
    swear_list=swear_list.readlines()
    for swear in range(len(swear_list)):
        swear = swear_list[swear].replace("\n", '')
        cleaned_list.append(swear)

recorded_swears = 0
warning_count = 9
kick_count = 10

def most_frequent(List):
    counter = 0
    num = List[0]
      
    for i in List:
        curr_frequency = List.count(i)
        if(curr_frequency> counter):
            counter = curr_frequency
            num = i
  
    return num

#Detects and removes swears
async def detect_swear(message):
    global recorded_swears
    msg = message.content.lower()
    author = message.author
    translated = GoogleTranslator(source='auto', target='en').translate(msg)
    translated_msg = translated.lower()
    for word in cleaned_list:
        if word in translated_msg:
            recorded_swears = recorded_swears + 1
            print("Number of swears recorded for: ", author, ": ",recorded_swears)
            await message.delete()
            await message.channel.send(message.author.mention+" Dont use that word 🙊! This is a warning")
            await log_output(author, recorded_swears)
            if recorded_swears >= warning_count:
                await message.channel.send(message.author.mention+" This is your last warning, you will be kicked")
                if recorded_swears >= kick_count:
                    await message.channel.send(message.author.mention+" You will be kicked promptly")
                    print("Kicked")
                    await log_kick(author, recorded_swears)

           
log_channel_id = 852202389896560650
#send message to logging channel
async def log_output(author, recorded_swears):
    channel = client.get_channel(log_channel_id)
    author = str(author)
    recorded_swears = str(recorded_swears)
    logmsg="Number of swears recorded for: {0} = {1}"
    await channel.send(logmsg.format(author, recorded_swears))

async def log_kick(author, recorded_swears):
    channel = client.get_channel(log_channel_id)
    author_name = str(author)
    recorded_swears = str(recorded_swears)
    logmsg="Kicked {0}, {0} has used swears for {1} times"
    await channel.send(logmsg.format(author_name, recorded_swears))
    #(Un)comment to enable/disable kick
    await author.kick()

authorlist = []
async def detect_spam(message):
    messages = await message.channel.history(limit=10).flatten()
    async for elem in message.channel.history(limit=15):
        elem.author.append(authorlist)
    if jellyfish.levenshtein_distance(messages) <= 2:
        author = most_frequent(authorlist)
        await author.kick(reason="Spamming")
        await message.channel.send("Kicked {0} for spamming.".format(author.name))
        if jellyfish.levenshtein_distance(messages) <= 4:
            await message.channel.slowmode_delay(30)
            await message.channel.send("Possible Spam detected! Enabling slowmode. Slowmode will end in 10 minutes")
            slowmode_timer = multiprocessing.Process(target=sleep(600))
            slowmode_timer.start()
    
    

                                     
@client.event
async def on_message(message):
    await detect_swear(message)
    await award_rep(message)

    
client.run(TOKEN)
