import discord
from deep_translator import GoogleTranslator
import time
import datetime
import json
import sqlite3

TOKEN = (open("TOKEN", "r")).readline()
GUILD = (open("GUILD", "r")).readline()

client = discord.Client()

# users = sqlite3.connect(':users.db')
users = sqlite3.connect(':memory:')
cursor = users.cursor()
#Creates the table
cursor.execute("""CREATE TABLE users (
            user text,
            reputation text,
            badpoints integer
            )""")

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

async def send_dm(member: discord.Member, content):
    channel = await member.create_dm()
    await channel.send(content)

time_window_milliseconds = 7000
max_msg_per_window = 4
author_msg_times = {}

async def detect_spam(message):
    global author_msg_counts

    author_id = message.author.id
    author = message.author
    # Get current epoch time in milliseconds
    curr_time = datetime.datetime.now().timestamp() * 1000

    # Make empty list for author id, if it does not exist
    if not author_msg_times.get(author_id, False):
        author_msg_times[author_id] = []

    # Append the time of this message to the users list of message times
    author_msg_times[author_id].append(curr_time)

    # Find the beginning of our time window.
    expr_time = curr_time - time_window_milliseconds

    # Find message times which occurred before the start of our window
    expired_msgs = [
        msg_time for msg_time in author_msg_times[author_id]
        if msg_time < expr_time
    ]

    # Remove all the expired messages times from our list
    for msg_time in expired_msgs:
        author_msg_times[author_id].remove(msg_time)
    # ^ note: we probably need to use a mutex here. Multiple threads
    # might be trying to update this at the same time. Not sure though.

    if len(author_msg_times[author_id]) > max_msg_per_window:
        await send_dm(message.author, "Stop Spamming")
        await message.delete()

def count_arguments(commandstr):
    argumentlist = commandstr.split(" ")
    return len(argumentlist)-1

async def get_val_str(info, segment): # ok david forgive me but this is a garbage and inefficient function
    input_info = str(info)
    x, a = input_info.split("[('")
    a, x = a.split(")]")
    userx, reputation, badpoints = a.split(", ")
    user = userx.split("'")
    if segment == 1:
        return user
    elif segment == 2:
        return reputation
    elif segment == 3:
        return badpoints
    else:
        return None

async def register_user(username, reputation, badpoints):
    with users:
        cursor.execute("INSERT INTO users VALUES (:username, :reputation, :badpoints)",
                       {'username': username, 'reputation': reputation, 'badpoints': badpoints})

async def print_info(user, segment, message):
    info = get_users_by_name(user)
    username = get_val_str(info, 1)
    text = get_val_str(info, segment)
    if segment == 2:
        await message.channel.send("{}'s reputation = {}!".format(username, text))
    else:
        await message.channel.send("{}'s badpoints = {}!".format(username, text))

async def get_users_by_name(username):
    cursor.execute("SELECT * FROM users WHERE username=:user", {'user': username})
    return cursor.fetchall()


async def update_reputation(username, reputation, message):
    with users:
        cursor.execute("""UPDATE users SET reputation = :reputation
                    WHERE first = :first""",
                  {'username': username, 'reputation': reputation})
        await print_info(username, 2, message)

async def update_badpoints(username, badpoints, message):
    with users:
        cursor.execute("""UPDATE users SET badpoints = :badpoints
                    WHERE username = :username""",
                  {'username': username, 'badpoints': badpoints})
        await print_info(username, 3, message)

async def remove_user(username):
    with users:
        cursor.execute("DELETE from users WHERE username = :username",
                  {'username': username})

async def detect_command(message):
    if message.content.startswith("!register"):
        if count_arguments(message.content) == 3:
            command, user, reputation, badpoints  = message.content.split(" ")
            await register_user(user, reputation, badpoints)
            await message.channel.send("User {} registered!".format(user))
        else:
            string = ("Missing arguments. !register <user> <reputation> <badpoints>")
            string += (". Number of arguments given " + str(count_arguments(message.content)) + "/3.")
            await message.channel.send(string)
    if message.content.startswith("!change_rep"):
        command, user, reputation = message.content.split(" ")
        await update_reputation(user, reputation, message)
        await print_info(user, 1, message)
    if message.content.startswith("!change_bad"):
        command, user, badpoints = message.content.split(" ")
        await update_badpoints(user, badpoints, message)
        await print_info(user, 2, message)
    if message.content.startswith("!unregister"):
        command, user = message.content.split(" ")
        await remove_user(user)
        await message.channel.send("User {} unregistered!".format(user))
    if message.content.startswith("!info"):
        command, user = message.content.split(" ")
        await print_info(user, 1, message)
        await print_info(user, 2, message)
        
@client.event
async def on_message(message):
    await detect_swear(message)
    await detect_spam(message)
    await detect_command(message)
    
client.run(TOKEN)
