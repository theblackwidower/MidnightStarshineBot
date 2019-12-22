    # ------------------------------------------------------------------------
    # MidnightStarshineBot - a multipurpose Discord bot
    # Copyright (C) 2019  T. Duke Perry
    #
    # This program is free software: you can redistribute it and/or modify
    # it under the terms of the GNU Affero General Public License as published
    # by the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.
    #
    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU Affero General Public License for more details.
    #
    # You should have received a copy of the GNU Affero General Public License
    # along with this program.  If not, see <https://www.gnu.org/licenses/>.
    # ------------------------------------------------------------------------

import os

import discord
from dotenv import load_dotenv

import datetime
import psycopg2
import math

import sys
import traceback

COMMAND_PREFIX = "ms!"

IS_EMOJI_CENSOR_ENABLED = False
IS_ECHO_ENABLED = True
IS_YAG_SNIPE_ENABLED = True
IS_RYLAN_SNIPE_ENABLED = False

MIDNIGHTS_TRUE_MASTER = 204818040628576256

HELP_COMMAND = "help"
ECHO_COMMAND = "say"
ROLECALL_COMMAND = "rolecall"
PAYDAY_SETUP_COMMAND = "setuppayday"
PAYDAY_CLEAR_COMMAND = "clearpayday"
PAYDAY_COMMAND = "payday"
BUY_ROLE_SETUP_COMMAND = "setuprole"
BUY_ROLE_REMOVE_COMMAND = "removerole"
LIST_ROLES_COMMAND = "rolemenu"
CLEAR_DMS_COMMAND = "cleardms"
SETUP_ACTIVE_ROLE_COMMAND = "setupactiverole"
CLEAR_ACTIVE_ROLE_COMMAND = "clearactiverole"

RULE_GET_COMMAND = "getrule"
RULE_SET_COMMAND = "setrule"
RULE_EDIT_COMMAND = "editrule"
RULE_DELETE_COMMAND = "deleterule"
RULE_GET_ALL_COMMAND = "getallrules"
RULE_GET_BACKUP_COMMAND = "getrulebackup"
RULE_CHANNEL_SET_COMMAND = "setrulechannel"
RULE_CHANNEL_CLEAR_COMMAND = "clearrulechannel"

MOD_MUTE_COMMAND = "mute"
MOD_UNMUTE_COMMAND = "unmute"
MOD_KICK_COMMAND = "kick"
MOD_BAN_SIMPLE_COMMAND = "ban"
MOD_BAN_DELETE_COMMAND = "spamban"

TRANSACTION_PAYDAY = "Payday"

MAX_CHARS = 2000

YAG_ID = 204255221017214977
RYLAN_NAME = 'rylan'

activeRecordLast = dict()
activeRecordStart = dict()
activeCheckTime = dict()

ACTIVE_CHECK_WAIT = datetime.timedelta(hours=1)

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ERROR_LOG = os.getenv('ERROR_LOG')
DATABASE_URL = os.getenv('DATABASE_URL')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'Successfully connected to the following servers:')

    status = COMMAND_PREFIX + HELP_COMMAND + " for the obvious."
    activity = discord.Activity(type=discord.ActivityType.listening, name=status)
    await client.change_presence(activity=activity)

    for guild in client.guilds:
        print(f'{guild.name}(id: {guild.id})')
        setupDataCache(guild.id)
        await yagSnipe(guild.get_member(YAG_ID))
        await rylanSnipeServer(guild)
        await purgeActiveServer(guild)

@client.event
async def on_error(self, event_method, *args, **kwargs):
    try:
        log = open(ERROR_LOG, "a+", encoding='utf-8')
        log.write("\n\nException occurred at " + datetime.datetime.now().isoformat() + ":\n")
        log.write('Ignoring exception in {}'.format(event_method) + "\n")
        log.write(traceback.format_exc())
        log.close()

        master = client.get_user(MIDNIGHTS_TRUE_MASTER)
        await master.create_dm()
        await master.dm_channel.send("Encountered an exception. Check logs at: " + datetime.datetime.now().isoformat())
    except:
        master = client.get_user(MIDNIGHTS_TRUE_MASTER)
        await master.create_dm()
        await master.dm_channel.send("Encountered an exception. Also encounted a problem logging the exception. Sorry.")

    finally:
        # Copy of parent code from client.py
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()

@client.event
async def on_member_join(member):
    await yagSnipe(member)
    await rylanSnipe(member)

@client.event
async def on_guild_join(server):
    setupDataCache(server.id)
    await yagSnipe(server.get_member(YAG_ID))
    await rylanSnipeServer(server)

@client.event
async def on_guild_role_update(before, after):
    await yagSnipe(after.guild.get_member(YAG_ID))
    await rylanSnipeServer(after.guild)

@client.event
async def on_member_update(before, after):
    await rylanSnipe(after)
    await purgeActiveMember(after)

@client.event
async def on_message(message):
    await emoji_censor(message)
    if message.content.startswith(COMMAND_PREFIX):
        await help(message)
        if isinstance(message.channel, discord.TextChannel):
            await echo(message)
            await rolecall(message)
            await setupPayday(message)
            await clearPayday(message)
            await payday(message)
            await setupRole(message)
            await removeRole(message)
            await roleMenu(message)
            await setupActive(message)
            await clearActive(message)

            await setRule(message)
            await getRule(message)
            await editRule(message)
            await deleteRule(message)
            await getAllRules(message)
            await getRuleBackup(message)
            await setRuleChannel(message)
            await clearRuleChannel(message)

            await mute(message)
            await unmute(message)
            await kick(message)
            await ban(message)
            await banDelete(message)
        elif isinstance(message.channel, discord.DMChannel):
            await clearDms(message)
    await checkActive(message)

@client.event
async def on_message_edit(old_message, message):
    await emoji_censor(message)

async def help(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + HELP_COMMAND:
        userPerms = message.author.permissions_in(message.channel)
        isManagePerms = userPerms.manage_guild

        output = "Hello, I am Midnight Starshine. Your friendly neighbourhood Discord bot. Here to help in any way I can.\n"
        output += "Would you like to take a look at my full source code? Naughty...\n"
        output += "It's available at <https://github.com/theblackwidower/MidnightStarshineBot>, and I'm licenced under the GNU AGPL version 3.\n"
        output += "If you're not sure what that means, don't worry, I'm not sure I understand either.\n"

        output += "\n**COMMANDS:**\n"
        output += "`" + COMMAND_PREFIX + HELP_COMMAND + "`: Outputs this help file.\n"
        if isinstance(message.channel, discord.TextChannel):
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute('SELECT amount, cooldown FROM tbl_payday_settings WHERE server = %s', (message.guild.id,))
            paydayData = c.fetchone()
            c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
            currencyData = c.fetchone()
            c.execute('SELECT COUNT(role) FROM tbl_paid_roles WHERE server = %s', (message.guild.id,))
            paidRolesData = c.fetchone()
            conn.close()
            if message.author.id == MIDNIGHTS_TRUE_MASTER and IS_ECHO_ENABLED:
                output += "`" + COMMAND_PREFIX + ECHO_COMMAND + "`: With this command I will repeat anything you, " + message.author.display_name + ", and only you, tell me to.\n"
            if isManagePerms:
                output += "`" + COMMAND_PREFIX + ROLECALL_COMMAND + "`: Will output a list of all members, sorted by their top role. Can be filtered by including the name of any role (case sensitive).\n"
                output += "`" + COMMAND_PREFIX + SETUP_ACTIVE_ROLE_COMMAND + "`: Use to setup the active role feature. Enter the command, followed by the role, gap between messages to define as 'active', minimum duration of activity, and maximum duration of inactivity.\n"
                output += "`" + COMMAND_PREFIX + CLEAR_ACTIVE_ROLE_COMMAND + "`: Use to disable the active role feature. If you want to reenable it, you'll have to run the setup command again.\n"
                output += "`" + COMMAND_PREFIX + PAYDAY_SETUP_COMMAND + "`: Can be used to set up the parameters of the payday command. Run the command, followed by the amount of money you want to give the users, the name of the currency, and finally, the cooldown time.\n"
                output += "`" + COMMAND_PREFIX + PAYDAY_CLEAR_COMMAND + "`: Use to disable the payday command. If you want to reenable it, you'll have to run the setup command again.\n"
            if paydayData is not None:
                output += "`" + COMMAND_PREFIX + PAYDAY_COMMAND + "`: Will put " + str(paydayData[0]) + " " + currencyData[0] + " into your account. Can only be run once every " + timeDeltaToString(datetime.timedelta(seconds=paydayData[1])) + ".\n"
            if currencyData is not None:
                if userPerms.manage_roles:
                    output += "`" + COMMAND_PREFIX + BUY_ROLE_SETUP_COMMAND + "`: Will allow you to set up a role for purchase. Just provide the role, and the cost in " + currencyData[0] + ".\n"
                    output += "`" + COMMAND_PREFIX + BUY_ROLE_REMOVE_COMMAND + "`: Will allow you to remove a role from the purchase list. Just name the role, and it'll be removed.\n"
                if paidRolesData[0] > 0:
                    output += "`" + COMMAND_PREFIX + LIST_ROLES_COMMAND + "`: Will display a list of all roles available for purchase in " + currencyData[0] + ".\n"
            output += "`" + COMMAND_PREFIX + RULE_GET_COMMAND + "`: Will output any rule I know of with the given number.\n"
            if isManagePerms:
                output += "`" + COMMAND_PREFIX + RULE_SET_COMMAND + "`: Use this command to inform me of a server rule I need to know about.\n"
                output += "`" + COMMAND_PREFIX + RULE_EDIT_COMMAND + "`: Use this command if you need to edit a server rule. Just provide the number, and the new rule.\n"
                output += "`" + COMMAND_PREFIX + RULE_DELETE_COMMAND + "`: Use this command if you want me to forget a particular server rule. Just provide the number, and I'll forget all about it.\n"
            output += "`" + COMMAND_PREFIX + RULE_GET_ALL_COMMAND + "`: Will send a copy of the server rules to your DMs.\n"
            if isManagePerms:
                output += "`" + COMMAND_PREFIX + RULE_GET_BACKUP_COMMAND + "`: Will send a backup of the server rules to your DMs, to allow for easy recovery in the event of a database failure.\n"
                output += "`" + COMMAND_PREFIX + RULE_CHANNEL_SET_COMMAND + "`: Will set which channel to post the server rules in. This post will be continually updated as the rules change.\n"
                output += "`" + COMMAND_PREFIX + RULE_CHANNEL_CLEAR_COMMAND + "`: Will delete the official posting of the server rules.\n"
            if userPerms.kick_members:
                output += "`" + COMMAND_PREFIX + MOD_MUTE_COMMAND + "`: Will mute the specified user in all channels.\n"
                output += "`" + COMMAND_PREFIX + MOD_UNMUTE_COMMAND + "`: Will unmute the specified user in all channels.\n"
                output += "`" + COMMAND_PREFIX + MOD_KICK_COMMAND + "`: Will kick the specified user. Specify the reason after mentioning the user.\n"
            if userPerms.ban_members:
                output += "`" + COMMAND_PREFIX + MOD_BAN_SIMPLE_COMMAND + "`: Will ban the specified user. Specify the reason after mentioning the user.\n"
                if userPerms.manage_messages:
                    output += "`" + COMMAND_PREFIX + MOD_BAN_DELETE_COMMAND + "`: Will ban the specified user, and delete all messages over the past 24 hours. Specify the reason after mentioning the user.\n"
        elif isinstance(message.channel, discord.DMChannel):
            output += "`" + COMMAND_PREFIX + CLEAR_DMS_COMMAND + "`: Will delete any DM I've sent to you, when specified with a message ID. Will delete all my DMs if no ID is provided.\n"

        if len(output) > MAX_CHARS:
            outputLines = output.split("\n")
            output = ""
            for line in outputLines:
                if len(output) + len(line) <= MAX_CHARS - 2:
                    output += line + "\n"
                else:
                    await message.channel.send(output)
                    output = line + "\n"

        await message.channel.send(output)

def setupDataCache(server_id):
    activeRecordLast[server_id] = dict()
    activeRecordStart[server_id] = dict()
    activeCheckTime[server_id] = dict()

async def emoji_censor(message):
    if isinstance(message.channel, discord.TextChannel) and IS_EMOJI_CENSOR_ENABLED:
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
        if parsing[0] == COMMAND_PREFIX + ECHO_COMMAND and message.author.id == MIDNIGHTS_TRUE_MASTER:
            await message.channel.send(parsing[2])
            await message.delete()

def parseRole(server, string):
    role = None
    if string.startswith("<@&") and string.endswith(">"):
        roleId = string[3:len(string) - 1]
        if roleId.isdigit():
            role = server.get_role(int(roleId))
    elif string.isdigit():
        role = server.get_role(int(string))
    if role is None:
        role = discord.utils.get(server.roles, name=string)
    return role

def parseMember(server, string):
    member = None
    if string.startswith("<@") and string.endswith(">"):
        memberId = string[2:len(string) - 1]
        if memberId.isdigit():
            member = server.get_member(int(memberId))
    return member

async def rolecall(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + ROLECALL_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        content = parsing[2].strip()
        scannedRole = None
        if len(content) > 0:
            scannedRole = parseRole(message.guild, content)
            if scannedRole is None:
                await message.channel.send("Invalid role name.")
                return
        users = 0
        if scannedRole is None:
            users = message.channel.guild.members
        else:
            users = scannedRole.members

        index = []
        count = []
        roles = message.channel.guild.roles
        for role in roles:
            index.append("")
            count.append(0)

        for user in users:
            if (user.nick is None):
                name = user.name
            else:
                name = user.nick + " (" + user.name + ")"
            index[user.top_role.position] += "   " + name + "\n"
            count[user.top_role.position] += 1

        output = "**RoleCall**\n"
        for i in range(len(index) - 1, -1, -1):
            if count[i] > 0:
                if count[i] == 1:
                    countString = str(count[i]) + " member"
                else:
                    countString = str(count[i]) + " members"
                output += "*" + discord.utils.escape_mentions(roles[i].name) + "* - (" + countString + ")\n" + index[i] + "\n"
        output += "\nTotal of **" + str(len(users)) + "** members listed"
        if len(output) > MAX_CHARS:
            outputLines = output.split("\n")
            output = ""
            for line in outputLines:
                if len(output) + len(line) <= MAX_CHARS - 2:
                    output += line + "\n"
                else:
                    await message.channel.send(output)
                    output = line + "\n"

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

def parseTimeDelta(string):
    num = string[:len(string) - 1]
    if num.isdigit():
        num = int(num)
        if string.endswith('d'):
            return datetime.timedelta(days=num)
        elif string.endswith('h'):
            return datetime.timedelta(hours=num)
        elif string.endswith('m'):
            return datetime.timedelta(minutes=num)
        elif string.endswith('s'):
            return datetime.timedelta(seconds=num)
    return None

async def setupActive(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + SETUP_ACTIVE_ROLE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        parsing = parsing[2].rpartition(" ")
        maxString = parsing[2]
        parsing = parsing[0].rpartition(" ")
        durationString = parsing[2]
        parsing = parsing[0].rpartition(" ")
        gapString = parsing[2]
        roleString = parsing[0]

        if roleString == "" or gapString == "" or durationString == "" or maxString == "":
            await message.channel.send("I'm missing some information, I'm sure of it. You need to provide me with a role, a maximum gap between messages to be considered 'active,' a minimum duration of activity, and a maximum duration of inactivity.")
        else:
            role = parseRole(message.guild, roleString)
            gap = parseTimeDelta(gapString)
            duration = parseTimeDelta(durationString)
            max = parseTimeDelta(maxString)
            if role is None:
                await message.channel.send("Cannot find the role entered.")
            elif gap is None:
                await message.channel.send("Cannot interpret what you entered for activity gap. Please enter a number, followed by 'd', 'h', 'm', or 's', for day, hour, minute, or second.")
            elif duration is None:
                await message.channel.send("Cannot interpret what you entered for minimum activity duration. Please enter a number, followed by 'd', 'h', 'm', or 's', for day, hour, minute, or second.")
            elif max is None:
                await message.channel.send("Cannot interpret what you entered for maximum period of inactivity. Please enter a number, followed by 'd', 'h', 'm', or 's', for day, hour, minute, or second.")
            elif gap >= duration or duration >= max:
                await message.channel.send("The *activity gap* has to be less than the *minimum activity duration*, which has to be less than the *maximum period of inactivity*.")
            else:
                conn = psycopg2.connect(DATABASE_URL)
                c = conn.cursor()
                c.execute('SELECT COUNT(server) FROM tbl_active_role_settings WHERE server = %s', (message.guild.id,))
                data = c.fetchone()
                if data[0] > 0:
                    c.execute('UPDATE tbl_active_role_settings SET role = %s, gap = %s, duration = %s, max = %s WHERE server = %s', (role.id, gap.total_seconds(), duration.total_seconds(), max.total_seconds(), message.guild.id))
                    output = "Active user role successfully updated with the following parameters:\n"
                else:
                    c.execute('INSERT INTO tbl_active_role_settings (server, role, gap, duration, max) VALUES (%s, %s, %s, %s, %s)', (message.guild.id, role.id, gap.total_seconds(), duration.total_seconds(), max.total_seconds()))
                    output = "Active user role successfully set up with the following parameters:\n"
                output += "We'll be assigning the \"__" + role.name + "__\" role...\n"
                output += "... to any user who sends at least one message every __" + timeDeltaToString(gap) + "__...\n"
                output += "... for at least __" + timeDeltaToString(duration) + "__.\n"
                output += "And we'll take the role away if they stop posting for __" + timeDeltaToString(max) + "__.\n"
                await message.channel.send(output)
                conn.commit()
                conn.close()

async def clearActive(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + CLEAR_ACTIVE_ROLE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT COUNT(server) FROM tbl_active_role_settings WHERE server = %s', (message.guild.id,))
        data = c.fetchone()
        if data[0] > 0:
            c.execute('DELETE FROM tbl_active_role_settings WHERE server = %s', (message.guild.id,))
            await message.channel.send("Active role feature completely cleared out. If you want to reenable it, please run `" + COMMAND_PREFIX + SETUP_ACTIVE_ROLE_COMMAND + "` again.")
            conn.commit()
        else:
            await message.channel.send("Active role feature has not even been set up, so there's no reason to clear it.")
        conn.close()

async def checkActive(message):
    if isinstance(message.author, discord.Member) and not message.author.bot:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT role, gap, duration FROM tbl_active_role_settings WHERE server = %s', (message.guild.id,))
        data = c.fetchone()
        conn.close()
        if data is not None:
            role = message.guild.get_role(data[0])
            gap = datetime.timedelta(seconds=data[1])
            duration = datetime.timedelta(seconds=data[2])
            if message.author.roles.count(message.author.guild.get_role(data[0])) == 0:
                try:
                    lastMessageTime = activeRecordLast[message.guild.id][message.author.id]
                    if message.created_at <= lastMessageTime + gap:
                        startMessageTime = activeRecordStart[message.guild.id][message.author.id]
                        if message.created_at >= startMessageTime + duration:
                            await message.author.add_roles(role, reason="Been sending at least one message per " + timeDeltaToString(gap) + " for " + timeDeltaToString(duration) + ".")
                    else:
                        activeRecordStart[message.guild.id][message.author.id] = message.created_at
                except KeyError:
                    activeRecordStart[message.guild.id][message.author.id] = message.created_at
                activeRecordLast[message.guild.id][message.author.id] = message.created_at

async def purgeActiveServer(server):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT role FROM tbl_active_role_settings WHERE server = %s', (server.id,))
    data = c.fetchone()
    conn.close()
    if data is not None:
        activeRole = server.get_role(data[0])
        for member in activeRole.members:
            await purgeActiveMember(member)

async def purgeActiveMember(member):
    try:
        lastCheck = activeCheckTime[member.guild.id][member.id]
    except KeyError:
        lastCheck = None

    if isinstance(member, discord.Member) and not member.bot and (lastCheck is None or lastCheck + ACTIVE_CHECK_WAIT < datetime.datetime.now()):
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT role, max FROM tbl_active_role_settings WHERE server = %s', (member.guild.id,))
        data = c.fetchone()
        conn.close()
        if data is not None:
            role = member.guild.get_role(data[0])
            max = datetime.timedelta(seconds=data[1])
            if member.roles.count(role) > 0:
                threshold = datetime.datetime.now() - max

                history = await member.history(limit=1, oldest_first=False).flatten()
                try:
                    if isinstance(history[0].channel, discord.TextChannel):
                        lastMessageTime = history[0].created_at
                    else:
                        lastMessageTime = None
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
                    await member.remove_roles(role, reason="Can't find any messages from this user in the past " + timeDeltaToString(max) + ".")
                else:
                    activeCheckTime[member.guild.id][member.id] = datetime.datetime.now()

async def setupPayday(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + PAYDAY_SETUP_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        parsing = parsing[2].partition(" ")
        amountString = parsing[0]
        parsing = parsing[2].rpartition(" ")
        currencyName = parsing[0]
        cooldownString = parsing[2]
        if amountString == "" or currencyName == "" or cooldownString == "":
            await message.channel.send("I'm missing some information, I'm sure of it. You need to provide me with an amount of money to dole out, a currency name, and a cooldown time.")
        elif not amountString.isdigit():
            await message.channel.send("Please enter a number for the amount of money we're expected to dole out each payday.")
        else:
            amount = int(amountString)
            cooldown = parseTimeDelta(cooldownString)
            if cooldown is None:
                await message.channel.send("Cannot interpret what you entered for cooldown time. Please enter a number, followed by 'd', 'h', 'm', or 's', for day, hour, minute, or second.")
            else:
                conn = psycopg2.connect(DATABASE_URL)
                c = conn.cursor()
                c.execute('SELECT COUNT(server) FROM tbl_payday_settings WHERE server = %s', (message.guild.id,))
                data = c.fetchone()
                if data[0] > 0:
                    c.execute('UPDATE tbl_payday_settings SET amount = %s, cooldown = %s WHERE server = %s', (amount, cooldown.total_seconds(), message.guild.id))
                    output = "Payday function successfully updated with the following parameters:\n"
                else:
                    c.execute('INSERT INTO tbl_payday_settings (server, amount, cooldown) VALUES (%s, %s, %s)', (message.guild.id, amount, cooldown.total_seconds()))
                    output = "Payday function successfully set up with the following parameters:\n"
                c.execute('SELECT COUNT(server) FROM tbl_currency WHERE server = %s', (message.guild.id,))
                data = c.fetchone()
                if data[0] > 0:
                    c.execute('UPDATE tbl_currency SET currency_name = %s WHERE server = %s', (currencyName, message.guild.id))
                else:
                    c.execute('INSERT INTO tbl_currency (server, currency_name) VALUES (%s, %s)', (message.guild.id, currencyName))
                output += "We'll be giving out __" + amountString + "__ '__" + currencyName + "__' to any user who runs the payday command.\n"
                output += "And after running the command they must wait __" + timeDeltaToString(cooldown) + "__ before running it again.\n"
                await message.channel.send(output)
                conn.commit()
                conn.close()

async def clearPayday(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + PAYDAY_CLEAR_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT COUNT(server) FROM tbl_payday_settings WHERE server = %s', (message.guild.id,))
        data = c.fetchone()
        if data[0] > 0:
            c.execute('DELETE FROM tbl_payday_settings WHERE server = %s', (message.guild.id,))
            await message.channel.send("Payday feature completely cleared out. If you want to reenable it, please run `" + COMMAND_PREFIX + PAYDAY_SETUP_COMMAND + "` again.")
            conn.commit()
        else:
            await message.channel.send("Payday feature has not even been set up, so there's no reason to clear it.")
        conn.close()

async def payday(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + PAYDAY_COMMAND:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT amount, cooldown FROM tbl_payday_settings WHERE server = %s', (message.guild.id,))
        serverData = c.fetchone()
        c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
        currencyData = c.fetchone()
        if serverData is not None and currencyData is not None:
            paydayAmount = serverData[0]
            currencyName = currencyData[0]
            cooldown = datetime.timedelta(seconds=serverData[1])
            c.execute('SELECT funds, last_payday FROM tbl_accounts WHERE server = %s AND member = %s', (message.guild.id, message.author.id))
            memberData = c.fetchone()
            if memberData is None:
                currentFunds = paydayAmount
                c.execute('INSERT INTO tbl_accounts (server, member, funds, last_payday) VALUES (%s, %s, %s, %s)', (message.guild.id, message.author.id, currentFunds, datetime.datetime.now().timestamp()))
                c.execute('INSERT INTO tbl_transactions (date, server, member, amount_in, notes) VALUES (%s, %s, %s, %s, %s)', (datetime.datetime.now().timestamp(), message.guild.id, message.author.id, paydayAmount, TRANSACTION_PAYDAY))
                await message.channel.send("Welcome, " + message.author.mention + "! We've started you off with " + str(currentFunds) + " " + currencyName + " in your account.")
            else:
                currentFunds = memberData[0]
                lastPayday = datetime.datetime.fromtimestamp(memberData[1])
                currentTime = datetime.datetime.now()
                if lastPayday + cooldown < currentTime:
                    currentFunds += paydayAmount
                    c.execute('UPDATE tbl_accounts SET funds = %s, last_payday = %s WHERE server = %s AND member = %s', (currentFunds, currentTime.timestamp(), message.guild.id, message.author.id))
                    c.execute('INSERT INTO tbl_transactions (date, server, member, amount_in, notes) VALUES (%s, %s, %s, %s, %s)', (datetime.datetime.now().timestamp(), message.guild.id, message.author.id, paydayAmount, TRANSACTION_PAYDAY))
                    await message.channel.send(message.author.mention + "! You now have " + str(currentFunds) + " " + currencyName + " in your account.")
                else:
                    timeLeft = lastPayday + cooldown - currentTime
                    await message.channel.send(message.author.mention + "! Please wait another " + timeDeltaToString(timeLeft) + " before attempting another payday.")
            conn.commit()
        conn.close()

async def setupRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + BUY_ROLE_SETUP_COMMAND and message.author.permissions_in(message.channel).manage_roles:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
        currencyData = c.fetchone()
        if currencyData is not None:
            currencyName = currencyData[0]
            parsing = parsing[2].rpartition(" ")
            roleString = parsing[0]
            costString = parsing[2]
            if roleString == "" or costString == "":
                await message.channel.send("I'm missing some information, I'm sure of it. You need to provide me with a role, and a cost.")
            elif not costString.isdigit():
                await message.channel.send("Please enter a number for the cost of the role.")
            else:
                role = parseRole(message.guild, roleString)
                cost = int(costString)
                if role is None:
                    await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
                else:
                    c.execute('SELECT COUNT(server) FROM tbl_paid_roles WHERE server = %s AND role = %s', (message.guild.id, role.id))
                    roleCountData = c.fetchone()
                    if roleCountData[0] > 0:
                        c.execute('UPDATE tbl_paid_roles SET cost = %s WHERE server = %s AND role = %s', (cost, message.guild.id, role.id))
                        output = "Role '" + role.name + "' now set to cost " + costString + " " + currencyName + "."
                    else:
                        c.execute('INSERT INTO tbl_paid_roles (server, role, cost) VALUES (%s, %s, %s)', (message.guild.id, role.id, cost))
                        output = "Role '" + role.name + "' now added to the menu, and costs " + costString + " " + currencyName + "."
                    await message.channel.send(output)
                    conn.commit()
        conn.close()

async def removeRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + BUY_ROLE_REMOVE_COMMAND and message.author.permissions_in(message.channel).manage_roles:
        role = parseRole(message.guild, parsing[2])
        if role is None:
            await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
        else:
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute('SELECT COUNT(server) FROM tbl_paid_roles WHERE server = %s AND role = %s', (message.guild.id, role.id))
            data = c.fetchone()
            if data[0] > 0:
                c.execute('DELETE FROM tbl_paid_roles WHERE server = %s AND role = %s', (message.guild.id, role.id))
                await message.channel.send("'" + role.name + "' has been removed from the role menu.")
                conn.commit()
            else:
                await message.channel.send("Can't find that role in the menu.")
            conn.close()

async def roleMenu(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + LIST_ROLES_COMMAND:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
        currencyData = c.fetchone()
        c.execute('SELECT role, cost FROM tbl_paid_roles WHERE server = %s', (message.guild.id,))
        allData = c.fetchall()
        conn.close()
        if currencyData is not None and len(allData) > 0:
            output = "**Available Roles**\n"
            for roleData in allData:
                role = message.guild.get_role(roleData[0])
                output += role.name + ": " + str(roleData[1]) + " " + currencyData[0] + "\n"
        await message.channel.send(output)

def timeDeltaToString(timeDelta):
    totalSeconds = timeDelta.total_seconds()
    days = math.floor(totalSeconds // (60 * 60 * 24))
    hours = math.floor(totalSeconds // (60 * 60)) % 24
    minutes = math.floor(totalSeconds // 60) % 60
    seconds = math.floor(totalSeconds % 60)

    totalTimeParts = []
    if days == 1:
        totalTimeParts.append("1 day")
    elif days > 1:
        totalTimeParts.append(str(days) + " days")
    if hours == 1:
        totalTimeParts.append("1 hour")
    elif hours > 1:
        totalTimeParts.append(str(hours) + " hours")
    if minutes == 1:
        totalTimeParts.append("1 minute")
    elif minutes > 1:
        totalTimeParts.append(str(minutes) + " minutes")
    if seconds == 1:
        totalTimeParts.append("1 second")
    elif seconds > 1:
        totalTimeParts.append(str(seconds) + " seconds")

    if len(totalTimeParts) == 1:
        totalTimeString = totalTimeParts[0]
    elif len(totalTimeParts) == 2:
        totalTimeString = totalTimeParts[0] + " and " + totalTimeParts[1]
    elif len(totalTimeParts) == 3:
        totalTimeString = totalTimeParts[0] + ", " + totalTimeParts[1] + " and " + totalTimeParts[2]
    elif len(totalTimeParts) == 4:
        totalTimeString = totalTimeParts[0] + ", " + totalTimeParts[1] + ", " + totalTimeParts[2] + " and " + totalTimeParts[3]
    else:
        raise Exception("Invalid number of totalTimeParts: " + len(totalTimeParts))

    return totalTimeString

async def clearDms(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + CLEAR_DMS_COMMAND:
        meBot = message.channel.me
        if parsing[2] == "":
            async for thisMessage in message.channel.history(limit=1000000, oldest_first=False):
                if thisMessage.author == meBot:
                    await thisMessage.delete()
            await message.channel.send("Cleared all DMs I sent to you.")
        elif parsing[2].isdigit():
            try:
                thisMessage = await message.channel.fetch_message(int(parsing[2]))
                if thisMessage.author == meBot:
                    await thisMessage.delete()
                else:
                    await message.channel.send("This isn't my message.")
            except discord.NotFound:
                await message.channel.send("Message " + parsing[2] + " not found.")
        else:
            await message.channel.send("Not a valid message number.")

async def setRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_SET_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        server_id = message.guild.id
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('INSERT INTO tbl_rules (server, content) VALUES (%s, %s)', (server_id, parsing[2]))
        c.execute('SELECT COUNT(id) FROM tbl_rules WHERE server = %s', (server_id,))
        data = c.fetchone()
        await message.channel.send("Rule #" + str(data[0]) + " has been set to: " + parsing[2])
        conn.commit()
        conn.close()
        await updateRuleChannel(message)

async def getRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_GET_COMMAND:
        if parsing[2].isdigit():
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute('SELECT content FROM tbl_rules WHERE server = %s ORDER BY id', (message.guild.id,))
            data = c.fetchall()
            conn.close()
            rule_num = int(parsing[2])
            if rule_num <= len(data) and rule_num > 0:
                await message.channel.send("Rule #" + parsing[2] + ": " + data[rule_num - 1][0])
            else:
                await message.channel.send("There is no rule #" + parsing[2])
        else:
            await message.channel.send("Please provide a valid number.")


def getRuleId(server_id, rule_num):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT id FROM tbl_rules WHERE server = %s', (server_id,))
    data = c.fetchall()
    conn.close()
    if rule_num <= len(data) and rule_num > 0:
        returnValue = data[rule_num - 1][0]
    else:
        returnValue = None
    return returnValue

async def editRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_EDIT_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        parsing = parsing[2].partition(" ")
        if parsing[0].isdigit():
            rule_id = getRuleId(message.guild.id, int(parsing[0]))
            if rule_id is not None:
                conn = psycopg2.connect(DATABASE_URL)
                c = conn.cursor()
                c.execute('UPDATE tbl_rules SET content = %s WHERE id = %s', (parsing[2], rule_id))
                await message.channel.send("Rule #" + parsing[0] + " is now: " + parsing[2])
                conn.commit()
                conn.close()
                await updateRuleChannel(message)
            else:
                await message.channel.send("There is no rule #" + parsing[0])
        else:
            await message.channel.send("Please provide a valid number.")

async def deleteRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_DELETE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        if parsing[2].isdigit():
            rule_id = getRuleId(message.guild.id, int(parsing[2]))
            if rule_id is not None:
                conn = psycopg2.connect(DATABASE_URL)
                c = conn.cursor()
                c.execute('DELETE FROM tbl_rules WHERE id = %s', (rule_id,))
                await message.channel.send("Rule #" + parsing[2] + " has been deleted")
                conn.commit()
                conn.close()
                await updateRuleChannel(message)
            else:
                await message.channel.send("There is no rule #" + parsing[2])
        else:
            await message.channel.send("Please provide a valid number.")

async def getAllRules(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_GET_ALL_COMMAND:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT content FROM tbl_rules WHERE server = %s ORDER BY id', (message.guild.id,))
        data = c.fetchall()
        conn.close()
        count = len(data)
        output = "**SERVER RULES** for " + message.guild.name + ":"
        for i in range(count):
            # TODO: add some kind of length control
            output += "\nRule #" + str(i + 1) + ": " + data[i][0]
        await message.author.create_dm()
        await message.author.dm_channel.send(output)

        await message.channel.send(message.author.mention + "! A copy of the complete server rules have been sent to your DMs.")

async def getRuleBackup(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_GET_BACKUP_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT content FROM tbl_rules WHERE server = %s ORDER BY id', (message.guild.id,))
        data = c.fetchall()
        conn.close()
        count = len(data)
        output = "**BACKUP OF SERVER RULES** for " + message.guild.name + ": \n```"
        for i in range(count):
            # TODO: add some kind of length control
            output += "\n" + COMMAND_PREFIX + RULE_SET_COMMAND + " " + data[i][0]
        output += "```"
        await message.author.create_dm()
        await message.author.dm_channel.send(output)

        await message.channel.send(message.author.mention + "! A backup of the complete server rules has been sent to your DMs.")

async def setRuleChannel(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_CHANNEL_SET_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        if parsing[2] == "":
            await message.channel.send("Please specify a rule channel.")
        elif len(message.channel_mentions) == 0:
            await message.channel.send("Please specify a valid rule channel.")
        else:
            ruleChannel = message.channel_mentions[0]
            server_id = message.guild.id
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute('SELECT channel FROM tbl_rule_posting WHERE server = %s', (server_id,))
            oldData = c.fetchone()
            if oldData is not None and oldData[0] == ruleChannel.id:
                await message.channel.send("The rules are already posted in that channel.")
            else:
                c.execute('SELECT content FROM tbl_rules WHERE server = %s ORDER BY id', (server_id,))
                rulesData = c.fetchall()
                count = len(rulesData)
                ruleOutput = "**RULES:**"
                for i in range(count):
                    # TODO: add some kind of length control
                    ruleOutput += "\n\n" + str(i + 1) + ": " + rulesData[i][0]
                ruleMessage = await ruleChannel.send(ruleOutput)
                if oldData is None:
                    c.execute('INSERT INTO tbl_rule_posting (server, channel, message) VALUES (%s, %s, %s)', (server_id, ruleChannel.id, ruleMessage.id))
                else:
                    c.execute('UPDATE tbl_rule_posting SET channel = %s, message = %s WHERE server = %s', (ruleChannel.id, ruleMessage.id, server_id))
                await message.channel.send("Rules now posted in " + ruleChannel.mention + ".")
                conn.commit()
            conn.close()

async def clearRuleChannel(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_CHANNEL_CLEAR_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        server_id = message.guild.id
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT channel, message FROM tbl_rule_posting WHERE server = %s', (server_id,))
        data = c.fetchone()
        if data is None:
            await message.channel.send("No rule postings recorded.")
        else:
            ruleChannel = message.guild.get_channel(data[0])
            try:
                ruleMessage = await ruleChannel.fetch_message(data[1])
                await ruleMessage.delete()
            except discord.errors.NotFound:
                pass
            c.execute('DELETE FROM tbl_rule_posting WHERE server = %s', (server_id,))
            await message.channel.send("Rule posting in " + ruleChannel.mention + " has been deleted.")
            conn.commit()
        conn.close()

async def updateRuleChannel(message):
    server_id = message.guild.id
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT channel, message FROM tbl_rule_posting WHERE server = %s', (server_id,))
    messageData = c.fetchone()
    if messageData is not None:
        try:
            ruleMessage = await message.guild.get_channel(messageData[0]).fetch_message(messageData[1])
            c.execute('SELECT content FROM tbl_rules WHERE server = %s ORDER BY id', (server_id,))
            rulesData = c.fetchall()
            count = len(rulesData)
            ruleOutput = "**RULES:**"
            for i in range(count):
                # TODO: add some kind of length control
                ruleOutput += "\n\n" + str(i + 1) + ": " + rulesData[i][0]
            await ruleMessage.edit(content=ruleOutput)
        except discord.errors.NotFound:
            await message.channel.send("Error encountered updating rule posting. Post has likely been deleted.")
    conn.close()

async def mute(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + MOD_MUTE_COMMAND and message.author.permissions_in(message.channel).kick_members:
        member = parseMember(message.guild, parsing[2])
        if member is None:
            await message.channel.send("Member not found.")
        elif member.guild_permissions.administrator:
            await message.channel.send("Cannot mute any user with full admin permissions.")
        else:
            reason = "Muting " + str(member) + " on " + str(message.author) + "'s order."
            for channel in message.guild.channels:
                permissions = channel.permissions_for(member)
                if permissions.send_messages or permissions.speak:
                    await channel.set_permissions(member, send_messages=False, speak=False, reason=reason)
            await message.channel.send("Member " + member.mention + " muted.")

async def unmute(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + MOD_UNMUTE_COMMAND and message.author.permissions_in(message.channel).kick_members:
        member = parseMember(message.guild, parsing[2])
        if member is None:
            await message.channel.send("Member not found.")
        else:
            reason = "Unmuting " + str(member) + " on " + str(message.author) + "'s order."
            for channel in message.guild.channels:
                permissions = channel.overwrites_for(member)
                if permissions is not None and (permissions.send_messages == False or permissions.speak == False):
                    permissions.update(send_messages=None, speak=None)
                    if permissions.is_empty():
                        await channel.set_permissions(member, overwrite=None, reason=reason)
                    else:
                        await channel.set_permissions(member, overwrite=permissions, reason=reason)
            await message.channel.send("Member " + member.mention + " unmuted.")

async def kick(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + MOD_KICK_COMMAND and message.author.permissions_in(message.channel).kick_members:
        parsing = parsing[2].partition(" ")
        member = parseMember(message.guild, parsing[0])
        if member is None:
            await message.channel.send("Member not found.")
        else:
            reason_record = "by: " + str(message.author)
            if parsing[2] == "":
                reason_message = "."
                reason_record += " With No Reason Given."
            else:
                reason_message = " for: " + parsing[2]
                reason_record += " for: " + parsing[2]
            await member.create_dm()
            await member.dm_channel.send("You were kicked from " + message.guild.name + reason_message)
            await member.kick(reason=reason_record)
            await message.channel.send("Member " + member.mention + " kicked" + reason_message)

async def ban(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + MOD_BAN_SIMPLE_COMMAND and message.author.permissions_in(message.channel).ban_members:
        parsing = parsing[2].partition(" ")
        member = parseMember(message.guild, parsing[0])
        if member is None:
            await message.channel.send("Member not found.")
        else:
            reason_record = "by: " + str(message.author)
            if parsing[2] == "":
                reason_message = "."
                reason_record += " With No Reason Given."
            else:
                reason_message = " for: " + parsing[2]
                reason_record += " for: " + parsing[2]
            await member.create_dm()
            await member.dm_channel.send("You were banned from " + message.guild.name + reason_message)
            await member.ban(reason=reason_record, delete_message_days=0)
            await message.channel.send("Member " + member.mention + " banned" + reason_message)

async def banDelete(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + MOD_BAN_DELETE_COMMAND and message.author.permissions_in(message.channel).ban_members and message.author.permissions_in(message.channel).manage_messages:
        parsing = parsing[2].partition(" ")
        member = parseMember(message.guild, parsing[0])
        if member is None:
            await message.channel.send("Member not found.")
        else:
            reason_record = "by: " + str(message.author)
            if parsing[2] == "":
                reason_message = "."
                reason_record += " With No Reason Given."
            else:
                reason_message = " for: " + parsing[2]
                reason_record += " for: " + parsing[2]
            await member.create_dm()
            await member.dm_channel.send("You were banned from " + message.guild.name + reason_message)
            await member.ban(reason=reason_record, delete_message_days=1)
            await message.channel.send("Member " + member.mention + " has had all messages from the past day deleted and has been banned" + reason_message)

client.run(DISCORD_TOKEN)
