import discord
import deep_translator
import datetime
import sqlite3
import re

TOKEN = (open("TOKEN", "r")).readline()

client = discord.Client()

log_channel_id = None

@client.event
async def on_ready():
    global log_channel_id
    discord.Intents.members = True
    
    print(f'{client.user} is connected to the following server:\n')
    for guild in client.guilds:

        print( #prints if the bot is connected to the server
            f'{guild.name}(id: {guild.id})'
        )
    #registers all members on start
    members = await guild.fetch_members().flatten()
    for member in members:
        await register_user(member.id, 0)
    print("All members registered.")
    
    #creates a role for mute if one does not exist
    
    if discord.utils.get(guild.roles, name="Muted"):
        pass
    else:
        await guild.create_role(name="Muted", permissions=discord.Permissions(permissions=66560)) # Permission ID = View Messages + Message History
        print("Mute Role created")
    role = discord.utils.get(guild.roles, name="Muted")
    try:
        for channel in guild.channels:
            await channel.set_permissions(role, speak=False, send_messages=False, read_message_history=True, read_messages=True)
    except discord.errors.Forbidden:
        print("Missing permissions to set role permission for every channel")
    else:
        print("Mute role now cannot speak in any channel")
    finally:
        print("Mute role created.")
    
    if not discord.utils.get(guild.text_channels, name="log"):
        raise Exception("No Mute Channel")
    else:
        log_channel = discord.utils.get(guild.text_channels, name="log")
        log_channel_id = log_channel.id

#registers/removes member on join/leave
@client.event
async def on_member_join(member):
    
    discord.Intents.members = True
    print(f'{member.name} has joined this server')
    await register_user(member.id, 0)

@client.event
async def on_member_remove(member):
    
    discord.Intents.members = True
    print(f'{member.name} has left this server')
    await remove_user(member.id)
    
#Reads in list of swears
cleaned_list = []
with open("list.txt", "r") as swear_list:
    swear_list=swear_list.readlines()
    for swear in range(len(swear_list)):
        swear = swear_list[swear].replace("\n", '')
        cleaned_list.append(swear)

# Swear detection params
recorded_swears = 0
warning_count = 9
kick_count = 10

#Detects and removes swears
async def detect_swear(message):
    global recorded_swears
    msg = message.content.lower()
    author = message.author
    translated = deep_translator.GoogleTranslator(source='auto', target='en').translate(msg)
    translated_msg = translated.lower()
    for word in cleaned_list:
        if word in translated_msg:
            recorded_swears = recorded_swears + 1
            print("Number of swears recorded for: @", author, ": ",recorded_swears)
            await message.delete()
            await message.channel.send(message.author.mention+" Don't use that word 🙊! This is a warning")
            await update_badpoints(message.author.id, 3, "add")
            await log_output(author, recorded_swears)
            if recorded_swears >= warning_count:
                await message.channel.send(message.author.mention+" This is your last warning, you will be kicked")
                if recorded_swears >= kick_count:
                    await message.channel.send(message.author.mention+" You will be kicked promptly")
                    print("Kicked")
                    await log_kick(author, recorded_swears)


#send message to logging channel
async def embed(message, title, description, color=0xFF5733, link=""):
    embed=discord.Embed(title=title, url=link, description=description, color=color)
    await message.channel.send(embed=embed)

async def log_output(author, recorded_swears):
    global log_channel_id
    channel = client.get_channel(log_channel_id)
    author = str(author)
    recorded_swears = str(recorded_swears)
    logmsg="Number of swears recorded for: {0} = {1}"
    #await channel.send(logmsg.format(author, recorded_swears))
    await embed("Swearing", ("Number of swears recorded for: {} = {}").format(author, recorded_swears))

async def log_kick(author, recorded_swears):
    global log_channel_id
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

# Params for spam detection
time_window_milliseconds = 7000
max_msg_per_window = 4
author_msg_times = {} # Do not edit this
max_spam_before_kick = 5
spam_count = 0

async def detect_spam(message):
    global author_msg_counts
    global spam_count
    
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
        spam_count = spam_count + 1
        if spam_count > max_spam_before_kick:
            author.kick()
            message.channel.send("User {0} kicked for spamming.".format(author.name))
            await update_badpoints(message.author.id, 1.5, "add")

async def detect_caps(message):
    cleaned_msg_content = message.content.replace(" ","")
    if len(cleaned_msg_content) >= 20: #avoids short messages
        
        upper   = filter(str.isupper, cleaned_msg_content)
        lower   = filter(str.islower, cleaned_msg_content)
        letters = filter(str.isalpha,message.content)

        upper   = "".join(upper)
        lower   = "".join(lower)
        letters = "".join(letters)
        
        ratio = len(upper)/len(letters)

        if ratio >= 0.60: #blocks messages with upper to all letters percentage higher than 70
            await message.delete()
            await message.channel.send(message.author.mention+" Please do not excessively use caps.")
            await update_badpoints(message.author.id, 1, "add")

async def mute_member(message, member):
        
    role = discord.utils.get(message.guild.roles, name="Muted")

    await member.add_roles(role)
    await message.channel.send(member.mention + " You have been muted by {0}".format(message.author))

async def unmute(message, member):
    
    role = discord.utils.get(message.guild.roles, name="Muted")

    await member.remove_roles(role)
    await message.channel.send(member.mention + " You have been unmuted by {0}.".format(message.author))
    
    
####################################
# Start of SQL-related code #
####################################

users = sqlite3.connect(':memory:')
cursor = users.cursor()
#Creates the table
cursor.execute("""CREATE TABLE users (
            userid integer,
            badpoints integer
            )""")

async def register_user(userid, badpoints):
    with users:
        cursor.execute("INSERT INTO users VALUES (:userid, :badpoints)",
                       {'userid': userid, 'badpoints': badpoints})
        users.commit()

async def update_badpoints(userid, badpoints, operation):
    curr_badpoints = await get_badpoints(userid)
    curr_badpoints = int(curr_badpoints)
    badpoints = int(badpoints)
    if operation == "add":
        new_badpoints = curr_badpoints+badpoints
    elif operation == "remove":
        new_badpoints = curr_badpoints-badpoints        
        
    with users:
        cursor.execute("""UPDATE users SET badpoints = :badpoints
                    WHERE userid = :userid""",
                  {'userid': userid, 'badpoints': new_badpoints})
        users.commit()
        
async def get_users_by_id(userid):
    cursor.execute("SELECT * FROM users WHERE userid=:user", {'user': userid})
    return cursor.fetchall()

async def remove_user(userid):
    with users:
        cursor.execute("DELETE from users WHERE userid = :userid",
                  {'userid': userid})
        users.commit()

async def get_badpoints(userid):
    with users:
        cursor.execute("SELECT * FROM users WHERE userid=:user", {'user': userid})
        row = cursor.fetchone()
        badpoints = row[1]
        return badpoints
 
####################################
# End of SQL-related code #
####################################
command_exec = None

async def detect_command(message):
    global command_exec
    if message.author.guild_permissions.ban_members: # Limits command to privledged members
        if message.content.startswith("!register_user"):
            msgcontent = message.content
            user = message.mentions
            user = user[0]
            id = user.id
            chunks = re.split(' +', msgcontent)
            badpoints = chunks[-1]
            await register_user(id, badpoints)#
            await message.channel.send("User {0} registered!".format(user.name))
            newbp = await get_badpoints(id)
            await message.channel.send("Badpoints for user {0} is now {1}".format(user.name, newbp))
        elif message.content.startswith("!update_badpoints"):
            msgcontent = message.content
            user = message.mentions
            user = user[0]
            id = user.id
            chunks = re.split(' +', msgcontent)
            badpoints = chunks[-1]
            operation = badpoints[0]
            if operation == "+":
                operation = "add"
                badpoints = badpoints[1:]
            elif operation == "-":
                operation = "remove"
                badpoints = badpoints[1:]
            elif operation != "+" or "-":
                await message.channel.send("Operation not specified, defaulting to add")
                operation = "add"
            await update_badpoints(id, badpoints, operation)
            await message.channel.send("Updated badpoints for user {0}, {1} {2} badpoints.".format(user.name, operation, badpoints))
            newbp = await get_badpoints(id)
            await message.channel.send("Badpoints for user {0} is now {1}".format(user.name, newbp))
        elif message.content.startswith("!remove_user"):
            msgcontent = message.content
            user = message.mentions
            user = user[0]
            id = user.id
            await remove_user(id)
            await message.channel.send("Removed user {0} from database.".format(user.name))
    
    #Mute Command
    if message.author.guild_permissions.kick_members: # Limits command to members with kick
        if message.content.startswith("!mute"):
            msgcontent = message.content
            user = message.mentions
            user = user[0]
            await mute_member(message, user)
        if message.content.startswith("!unmute"):
            msgcontent = message.content
            user = message.mentions
            user = user[0]
            await unmute(message, user)
            
    #Public get_badpoints command
    if message.content.startswith("!get_badpoints"):
        msgcontent = message.content
        user = message.mentions
        user = user[0]
        id = user.id
        badpoints = await get_badpoints(id)
        await message.channel.send("Badpoints for user {0} is {1}".format(user.name, badpoints))

    # Embed
    if message.content.startswith("!embed"):
        msgcontent = message.content
        bits = msgcontent.split(" ")
        link = bits[2]

        color_in = str(bits[1])
        description = ""

        haslink = False

        if "https" in link:
            title = bits[3]
            bits.remove(bits[0])
            bits.remove(bits[0])
            bits.remove(bits[0])
            bits.remove(bits[0])
            haslink = True
        else:
            title = bits[2]
            bits.remove(bits[0])
            bits.remove(bits[0])
            bits.remove(bits[0])

        color = int(color_in, 16)
        for word in bits:
            description += word + " "

        await message.delete()

        if haslink:
            await embed(message, title, description, color, link)
        else:
            await embed(message, title, description, color)

async def check_author_badpoints(message):
    author_badpoints = await get_badpoints(message.author.id)
    
    # Kicks if sender badpoints is high
    if author_badpoints >= 10:
        mute_member(message, message.author)
    elif author_badpoints >= 20:
        message.channel.send("You will be kicked. Reason: Badpoints higher than 20 (Badpoints = {0})".format(author_badpoints))
        message.author.kick()
    elif author_badpoints >= 30:
        message.channel.send("You will be banned. Reason: Badpoints higher than 30 (Badpoints = {0})".format(author_badpoints))
        message.author.ban()

async def check_command(message):

    if message.content.startswith("!"): # Only check for command if message starts with !
        try:
            await detect_command(message)
        except BaseException as e:
            await message.channel.send("Command Failed, Reason: {0}".format(e))
        finally:
            pass
        
@client.event
async def on_message(message):
        
    if message.author.bot or message.author.guild_permissions.administrator: # Whitelists bots and admins
        pass
    else:
        try:
            await detect_swear(message)
        except deep_translator.exceptions.NotValidPayload:
            pass
            
        await detect_spam(message)
        await detect_caps(message)
    
    await check_command(message)
    await check_author_badpoints(message)
    

        
        
client.run(TOKEN)
