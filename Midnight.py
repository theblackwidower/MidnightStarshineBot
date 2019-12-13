import os

import discord
from dotenv import load_dotenv

import datetime
import sqlite3
import math

COMMAND_PREFIX = "ms!"

DATABASE_LOCATION='Midnight.db'

IS_EMOJI_CENSOR_ENABLED = True
IS_ECHO_ENABLED = True
IS_YAG_SNIPE_ENABLED = True
IS_RYLAN_SNIPE_ENABLED = True

ECHO_USER = 204818040628576256

ECHO_COMMAND = "say"
ROLECALL_COMMAND = "rolecall"
PAYDAY_COMMAND = "payday"

RULE_GET_COMMAND = "getrule"
RULE_SET_COMMAND = "setrule"
RULE_EDIT_COMMAND = "editrule"
RULE_DELETE_COMMAND = "deleterule"

PAYDAY_AMOUNT = 250
PAYDAY_COOLDOWN = datetime.timedelta(minutes=30)

YAG_ID = 204255221017214977
RYLAN_NAME = 'rylan'

ACTIVE_ROLE = 635253363440877599

activeRecordLast = dict()
activeRecordStart = dict()
activeCheckTime = dict()

ACTIVE_GAP = datetime.timedelta(seconds=30)
ACTIVE_DURATION = datetime.timedelta(minutes=5)

ACTIVE_MAX = datetime.timedelta(days=3)
ACTIVE_CHECK_WAIT = datetime.timedelta(hours=1)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'Successfully connected to the following servers:')

    for guild in client.guilds:
        print(f'{guild.name}(id: {guild.id})')
        await yagSnipe(guild.get_member(YAG_ID))
        await rylanSnipeServer(guild)
        await purgeActiveServer(guild)

@client.event
async def on_member_join(member):
    await yagSnipe(member)
    await rylanSnipe(member)

@client.event
async def on_guild_join(server):
    await yagSnipe(server.get_member(YAG_ID))
    await rylanSnipeServer(server)

@client.event
async def on_guild_role_update(before, after):
    await yagSnipe(after.guild.get_member(YAG_ID))
    await rylanSnipeServer(after.guild)

@client.event
async def on_member_update(before, after):
    await rylanSnipe(after)
    if after.guild.get_role(ACTIVE_ROLE) is not None and isinstance(after, discord.Member) and not after.bot and isActive(after):
        await purgeActiveMember(after)

@client.event
async def on_message(message):
    await emoji_censor(message)
    if message.content.startswith(COMMAND_PREFIX):
        await echo(message)
        await rolecall(message)
        await payday(message)
        await setRule(message)
        await getRule(message)
        await editRule(message)
        await deleteRule(message)
    if isinstance(message.author, discord.Member) and not message.author.bot and not isActive(message.author):
        await checkActive(message)

@client.event
async def on_message_edit(old_message, message):
    await emoji_censor(message)

async def emoji_censor(message):
    if IS_EMOJI_CENSOR_ENABLED:
        content = message.content

        emojiCount = 0
        while True:
            # <:AnnoyedSweetieBelle:650749086105993218>
            customEmojiStart = content.find("<:")
            if customEmojiStart == -1:
                break
            customEmojiMid = content.find(":", customEmojiStart + 1)
            if customEmojiMid == -1:
                break
            customEmojiEnd = content.find(">", customEmojiMid + 1)
            if customEmojiEnd == -1:
                break

            # if content[customEmojiMid + 2:customEmojiEnd - 2].isdigit():
            content = content[0:customEmojiStart] + content[customEmojiEnd + 1:]
            emojiCount += 1

        # TODO: Detect Unicode emojis

        content = content.strip()
        messageLength = len(content)

        if (emojiCount > 0 and (messageLength < 3 or messageLength <= emojiCount)):
            await message.delete()

async def echo(message):
    if IS_ECHO_ENABLED:
        parsing = message.content.partition(" ")
        if parsing[0] == COMMAND_PREFIX + ECHO_COMMAND and message.author.id == ECHO_USER:
            await message.channel.send(parsing[2])
            await message.delete()

async def rolecall(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + ROLECALL_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        content = parsing[2].strip()
        scannedRole = 0
        if len(content) > 0:
            for role in message.channel.guild.roles:
                if role.name == content:
                    scannedRole = role
                    break
            if scannedRole == 0:
                await message.channel.send("Invalid role name.")
                return
        users = 0
        if scannedRole == 0:
            users = message.channel.guild.members
        else:
            users = scannedRole.members

        index = [""]
        roles = message.channel.guild.roles
        for role in roles:
            index.append("")

        for user in users:
            if (user.nick is None):
                name = user.name
            else:
                name = user.nick + " (" + user.name + ")"
            index[user.top_role.position] += "   " + name + "\n"

        output = "**RoleCall**\n"
        for i in range(len(index) - 1, -1, -1):
            if len(index[i]) > 0:
                output += "*" + discord.utils.escape_mentions(roles[i].name) + "*:\n" + index[i] + "\n"

        await message.channel.send(output)

async def yagSnipe(member):
    if IS_YAG_SNIPE_ENABLED and member is not None and member.id == YAG_ID:
        permissions = member.guild.me.guild_permissions
        if member.top_role.position >= member.guild.me.top_role.position:
            print("Can't kick " + member.name + " in " + member.guild.name + ". Too low a role.")
        elif permissions.ban_members or permissions.administrator:
            await member.ban(reason="Being a shit bot.", delete_message_days=0)
        elif permissions.kick_members:
            await member.kick(reason="Being a shit bot.")
        else:
            print("Can't kick " + member.name + " in " + member.guild.name + ". Lacking permissions.")

async def rylanSnipeServer(server):
    if IS_RYLAN_SNIPE_ENABLED:
        for member in server.members:
            if member.display_name == RYLAN_NAME:
                await rylanSnipe(member)

async def rylanSnipe(member):
    if IS_RYLAN_SNIPE_ENABLED and member is not None and member.display_name == RYLAN_NAME:
        permissions = member.guild.me.guild_permissions
        if member.top_role.position >= member.guild.me.top_role.position:
            print("Can't kick " + member.name + " in " + member.guild.name + ". Too low a role.")
        elif permissions.ban_members or permissions.administrator:
            await member.create_dm()
            await member.dm_channel.send("TOO MANY RYLANS!!!")
            await member.ban(reason="Too many rylans.", delete_message_days=0)
        elif permissions.kick_members:
            await member.create_dm()
            await member.dm_channel.send("TOO MANY RYLANS!!!")
            await member.kick(reason="Too many rylans.")
        else:
            print("Can't kick " + member.name + " in " + member.guild.name + ". Lacking permissions.")

def isActive(member):
    try:
        member.roles.index(member.guild.get_role(ACTIVE_ROLE))
        return True
    except ValueError:
        return False

async def checkActive(message):
    try:
        lastMessageTime = activeRecordLast[message.author.id]
        if message.created_at <= lastMessageTime + ACTIVE_GAP:
            startMessageTime = activeRecordStart[message.author.id]
            if message.created_at >= startMessageTime + ACTIVE_DURATION:
                await message.author.add_roles(message.guild.get_role(ACTIVE_ROLE))
        else:
            activeRecordStart[message.author.id] = message.created_at
    except KeyError:
        activeRecordStart[message.author.id] = message.created_at
    activeRecordLast[message.author.id] = message.created_at

async def purgeActiveServer(server):
    activeRole = server.get_role(ACTIVE_ROLE)
    if activeRole is not None:
        for member in activeRole.members:
            await purgeActiveMember(member)

async def purgeActiveMember(member):
    try:
        lastCheck = activeCheckTime[member.id]
    except KeyError:
        lastCheck = None

    if lastCheck is None or lastCheck + ACTIVE_CHECK_WAIT < datetime.datetime.now():
        threshold = datetime.datetime.now() - ACTIVE_MAX

        history = await member.history(limit=1, oldest_first=False).flatten()
        try:
            lastMessageTime = history[0].created_at
        except IndexError:
            lastMessageTime = None

        # BACKUP CODE - Significantly less efficient. Should only be used if there's something seriously wrong with Discord's search function.
        if lastMessageTime is None:
            print("Running purgeActive backup code in " + member.guild.name + " on " + str(member) + " at " + datetime.datetime.now().isoformat())
            for channel in member.guild.channels:
                if isinstance(channel, discord.channel.TextChannel) and member.guild.me.permissions_in(channel).read_message_history:
                    memberMessages = []
                    async for message in channel.history(limit=100000000, after=threshold, oldest_first=False):
                        if message.author == member:
                            memberMessages.append(message)
                    for message in memberMessages:
                        if lastMessageTime is None:
                            lastMessageTime = message.created_at
                        elif lastMessageTime < message.created_at:
                            lastMessageTime = message.created_at
            if lastMessageTime is None:
                lastMessageTime = threshold

        if lastMessageTime <= threshold:
            await member.remove_roles(member.guild.get_role(ACTIVE_ROLE))
        else:
            activeCheckTime[member.id] = datetime.datetime.now()

async def payday(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + PAYDAY_COMMAND:
        conn = sqlite3.connect(DATABASE_LOCATION)

        c = conn.cursor()
        c.execute('SELECT funds, last_payday FROM tbl_currency WHERE server_id = ? AND member_id = ?', (message.guild.id, message.author.id))
        data = c.fetchone()
        if data is None:
            currentFunds = PAYDAY_AMOUNT
            c.execute('INSERT INTO tbl_currency VALUES (?, ?, ?, ?)', (message.guild.id, message.author.id, currentFunds, datetime.datetime.now().timestamp()))
            await message.channel.send("Welcome, " + message.author.mention + "! We've started you off with " + str(currentFunds) + " bits in your account.")

        else:
            currentFunds = data[0]
            lastPayday = datetime.datetime.fromtimestamp(data[1])
            currentTime = datetime.datetime.now()
            if lastPayday + PAYDAY_COOLDOWN < currentTime:
                currentFunds += PAYDAY_AMOUNT
                c.execute('UPDATE tbl_currency SET funds = ?, last_payday = ? WHERE server_id = ? AND member_id = ?', (currentFunds, currentTime.timestamp(), message.guild.id, message.author.id))
                await message.channel.send(message.author.mention + "! You now have " + str(currentFunds) + " bits in your account.")
            else:
                timeLeft = lastPayday + PAYDAY_COOLDOWN - currentTime
                totalSeconds = timeLeft.total_seconds()
                hours = math.floor(totalSeconds // (60 * 60))
                minutes = math.floor(totalSeconds // 60) % 60
                seconds = math.floor(totalSeconds % 60)

                totalTimeParts = []
                if hours > 0:
                    totalTimeParts.append(str(hours) + " hours")
                if minutes > 0:
                    totalTimeParts.append(str(minutes) + " minutes")
                if seconds > 0:
                    totalTimeParts.append(str(seconds) + " seconds")

                if len(totalTimeParts) == 1:
                    totalTimeString = totalTimeParts[0]
                elif len(totalTimeParts) == 2:
                    totalTimeString = totalTimeParts[0] + " and " + totalTimeParts[1]
                elif len(totalTimeParts) == 3:
                    totalTimeString = totalTimeParts[0] + ", " + totalTimeParts[1] + " and " + totalTimeParts[2]
                else:
                    raise Exception("Invalid number of totalTimeParts: " + len(totalTimeParts))

                await message.channel.send(message.author.mention + "! Please wait another " + totalTimeString + " before attempting another payday.")


        conn.commit()
        conn.close()

async def setRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_SET_COMMAND:
        conn = sqlite3.connect(DATABASE_LOCATION)

        server_id = message.guild.id
        c = conn.cursor()
        c.execute('INSERT INTO tbl_rules (server, content) VALUES (?, ?);', (server_id, parsing[2]))
        c.execute('SELECT COUNT(id) FROM tbl_rules WHERE server = ?', (server_id,))
        data = c.fetchone()
        await message.channel.send("Rule #" + str(data[0]) + " has been set to: " + parsing[2])

        conn.commit()
        conn.close()

async def getRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_GET_COMMAND:
        if parsing[2].isdigit():
            conn = sqlite3.connect(DATABASE_LOCATION)
            server_id = message.guild.id
            c = conn.cursor()
            c.execute('SELECT content FROM tbl_rules WHERE server = ? ORDER BY id', (server_id,))
            data = c.fetchall()
            count = len(data)
            rule_num = int(parsing[2])
            if rule_num <= count and rule_num > 0:
                await message.channel.send("Rule #" + parsing[2] + ": " + data[rule_num - 1][0])
            else:
                await message.channel.send("There is no rule #" + parsing[2])
            conn.commit()
            conn.close()
        else:
            await message.channel.send("Please provide a valid number.")


async def getRuleId(server_id, rule_num):
    conn = sqlite3.connect(DATABASE_LOCATION)

    c = conn.cursor()
    c.execute('SELECT id FROM tbl_rules WHERE server = ?', (server_id,))
    data = c.fetchall()
    count = len(data)
    if rule_num <= count and rule_num > 0:
        returnValue = data[rule_num - 1][0]
    else:
        returnValue = None

    conn.commit()
    conn.close()

    return returnValue

async def editRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_EDIT_COMMAND:
        parsing = parsing[2].partition(" ")
        if parsing[0].isdigit():
            server_id = message.guild.id
            rule_num = int(parsing[0])
            rule_id = await getRuleId(server_id, rule_num)
            if rule_id is not None:
                conn = sqlite3.connect(DATABASE_LOCATION)
                c = conn.cursor()
                c.execute('UPDATE tbl_rules SET content = ? WHERE id = ?', (parsing[2], rule_id))
                conn.commit()
                conn.close()
                await message.channel.send("Rule #" + parsing[0] + " is now: " + parsing[2])
            else:
                await message.channel.send("There is no rule #" + parsing[0])
        else:
            await message.channel.send("Please provide a valid number.")

async def deleteRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_DELETE_COMMAND:
        if parsing[2].isdigit():
            server_id = message.guild.id
            rule_num = int(parsing[2])
            rule_id = await getRuleId(server_id, rule_num)
            if rule_id is not None:
                conn = sqlite3.connect(DATABASE_LOCATION)
                c = conn.cursor()
                c.execute('DELETE FROM tbl_rules WHERE id = ?', (rule_id,))
                conn.commit()
                conn.close()
                await message.channel.send("Rule #" + parsing[2] + " has been deleted")
            else:
                await message.channel.send("There is no rule #" + parsing[2])
        else:
            await message.channel.send("Please provide a valid number.")

client.run(token)
