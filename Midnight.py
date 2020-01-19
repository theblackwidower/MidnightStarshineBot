    # ------------------------------------------------------------------------
    # MidnightStarshineBot - a multipurpose Discord bot
    # Copyright (C) 2020  T. Duke Perry
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

import discord

import datetime
import psycopg2
import math
import re

import sys
import traceback

from Constants import *
from Utilities import *

from RemoteAdmin import *
from ActiveRole import *
from PromoterRole import *
from Economy import *
from Rules import *
from Moderation import *

IS_EMOJI_CENSOR_ENABLED = False
IS_ECHO_ENABLED = True
IS_YAG_SNIPE_ENABLED = False
IS_RYLAN_SNIPE_ENABLED = False
IS_GHOST_PING_DETECTOR_ENABLED = False

HELP_COMMAND = "help"
SOURCE_CODE_COMMAND = "getsource"
SANCTUARY_COMMAND = "tosanctuary"
ECHO_COMMAND = "say"
ROLECALL_COMMAND = "rolecall"
CLEAR_DMS_COMMAND = "cleardms"

YAG_ID = 204255221017214977
RYLAN_NAME = 'rylan'

ghostReportRecord = dict()

GHOST_PING_DETECTOR_THRESHOLD = datetime.timedelta(minutes=3)

BIG_ROLE_THRESHOLD = 0.75

EMOJI_DETECTOR = re.compile("\u00a9|\u00ae|[\u2000-\u3300]|\ud83c[\ud000-\udfff]|\ud83d[\ud000-\udfff]|\ud83e[\ud000-\udfff]|[🌀-🙏]|[🚀-🛿]|[🤀-🿿]|[🇦-🇿]{2}")

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
        await setupInviteDataCache(guild)
        await yagSnipe(guild.get_member(YAG_ID))
        await rylanSnipeServer(guild)

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

        author = None
        channel = None
        if isinstance(event_method, discord.TextChannel):
            channel = event_method
        elif isinstance(event_method, discord.Message):
            author = event_method.author
            channel = event_method.channel

        if channel is not None:
            if channel.guild.me.permissions_in(channel).send_messages:
                await channel.send("Oh, what did you do!? You broke it!\nSomething went wrong. But don't worry, the necessary people have been put to work fixing the problem. Please be patient.")
            elif author is not None:
                try:
                    await author.create_dm()
                    await author.dm_channel.send("Pretty sure you broke something with that last message. But don't worry, the necessary people have been put to work fixing the problem. Please be patient.")
                except discord.Forbidden:
                    await master.dm_channel.send("Also, user " + str(author) + " (" + str(author.id) + ") blocked me. That isn't very nice.")

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
    await persistActive(member)
    await persistBuyablesMember(member)
    await persistPromoterRole(member)
    await recordRecruit(member)

@client.event
async def on_guild_join(server):
    setupDataCache(server.id)
    await yagSnipe(server.get_member(YAG_ID))
    await rylanSnipeServer(server)
    await reportServerJoin(server)

@client.event
async def on_guild_remove(server):
    await reportServerLeave(server)

@client.event
async def on_guild_role_update(before, after):
    await yagSnipe(after.guild.get_member(YAG_ID))
    await rylanSnipeServer(after.guild)

@client.event
async def on_member_update(before, after):
    await rylanSnipe(after)
    await persistActive(after)
    await persistBuyablesMember(after)

@client.event
async def on_message(message):
    await emoji_censor(message)
    if message.content.startswith(COMMAND_PREFIX):
        await help(message)
        await sourceCode(message)
        await sanctuaryInvite(message)
        await echo(message)
        if isinstance(message.channel, discord.TextChannel):
            await rolecall(message)
            await setupPayday(message)
            await clearPayday(message)
            await payday(message)
            await balance(message)
            await setupRole(message)
            await removeRole(message)
            await roleMenu(message)
            await buyRole(message)
            await refundRole(message)
            await setupActive(message)
            await clearActive(message)
            await setupPromoterRole(message)
            await clearPromoterRole(message)

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
            await listServers(message)
            await leaveServer(message)
            await listServerChannels(message)
            await getPerms(message)
    await checkActive(message)

@client.event
async def on_message_edit(old_message, message):
    await emoji_censor(message)

@client.event
async def on_message_delete(message):
    await ghostPingDetector(message)
    await reportSupressionDetector(message)

@client.event
async def on_guild_role_delete(role):
    await roleDeleted(role)

async def help(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + HELP_COMMAND:
        userPerms = message.author.permissions_in(message.channel)
        isManagePerms = userPerms.manage_guild

        output = "Hello, I am Midnight Starshine. Your friendly neighbourhood Discord bot. Here to help in any way I can.\n"

        output += "\n**COMMANDS:**\n"
        output += "`" + COMMAND_PREFIX + HELP_COMMAND + "`: Outputs this help file.\n"
        output += "`" + COMMAND_PREFIX + SOURCE_CODE_COMMAND + "`: I'm licenced under the GNU AGPL version 3. This means you are fully entitled to look at my full source code. Enter this command and I'll send you a link to my GitHub repository.\n"
        output += "`" + COMMAND_PREFIX + SANCTUARY_COMMAND + "`: Every girl needs a place to unwind. I have my very special sanctuary. If you'd like an invite to **\"Moonlight's Sanctuary\"**. Just use this command.\n"
        if isinstance(message.channel, discord.TextChannel):
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute('SELECT amount, cooldown FROM tbl_payday_settings WHERE server = %s', (message.guild.id,))
            paydayData = c.fetchone()
            c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
            currencyData = c.fetchone()
            c.execute('SELECT COUNT(role) FROM tbl_paid_roles WHERE server = %s', (message.guild.id,))
            paidRolesData = c.fetchone()
            c.execute('SELECT COUNT(content) FROM tbl_rules WHERE server = %s', (message.guild.id,))
            rulesData = c.fetchone()
            conn.close()
            if message.author.id == MIDNIGHTS_TRUE_MASTER and IS_ECHO_ENABLED:
                output += "`" + COMMAND_PREFIX + ECHO_COMMAND + "`: With this command I will repeat anything you, " + message.author.display_name + ", and only you, tell me to.\n"
            if isManagePerms:
                output += "`" + COMMAND_PREFIX + ROLECALL_COMMAND + "`: Will output a list of all members, sorted by their top role. Can be filtered by including the name of any role (case sensitive).\n"
                output += "\n*Active Role Function:*\n"
                output += "`" + COMMAND_PREFIX + SETUP_ACTIVE_ROLE_COMMAND + "`: Use to setup the active role feature. Enter the command, followed by the role, gap between messages to define as 'active', minimum duration of activity, and maximum duration of inactivity.\n"
                output += "`" + COMMAND_PREFIX + CLEAR_ACTIVE_ROLE_COMMAND + "`: Use to disable the active role feature. If you want to reenable it, you'll have to run the setup command again.\n"
                output += "\n*Promoter Role Function:*\n"
                output += "`" + COMMAND_PREFIX + SETUP_PROMOTER_ROLE_COMMAND + "`: Use to setup the promoter role feature. Enter the command, followed by the role, and the number of recrutments one would need to qualify for the role. Only one promoter role can be set up at any one time.\n"
                output += "`" + COMMAND_PREFIX + SETUP_PROMOTER_ROLE_COMMAND + "`: Use to disable the promoter role feature. If you want to reenable it, you'll have to run the setup command again.\n"
            if isManagePerms or paydayData is not None or (currencyData is not None and (userPerms.manage_roles or paidRolesData[0] > 0)):
                output += "\n*Buyable roles:*\n"
            if isManagePerms:
                output += "`" + COMMAND_PREFIX + PAYDAY_SETUP_COMMAND + "`: Can be used to set up the parameters of the payday command. Run the command, followed by the amount of money you want to give the users, the name of the currency, and finally, the cooldown time.\n"
                output += "`" + COMMAND_PREFIX + PAYDAY_CLEAR_COMMAND + "`: Use to disable the payday command. If you want to reenable it, you'll have to run the setup command again.\n"
            if paydayData is not None:
                output += "`" + COMMAND_PREFIX + PAYDAY_COMMAND + "`: Will put " + str(paydayData[0]) + " " + currencyData[0] + " into your account. Can only be run once every " + timeDeltaToString(datetime.timedelta(seconds=paydayData[1])) + ".\n"
                output += "`" + COMMAND_PREFIX + BALANCE_COMMAND + "`: Will display your account balance.\n"
            if currencyData is not None:
                if userPerms.manage_roles:
                    output += "`" + COMMAND_PREFIX + BUY_ROLE_SETUP_COMMAND + "`: Will allow you to set up a role for purchase. Just provide the role, and the cost in " + currencyData[0] + ".\n"
                    output += "`" + COMMAND_PREFIX + BUY_ROLE_REMOVE_COMMAND + "`: Will allow you to remove a role from the purchase list. Just name the role, and it'll be removed.\n"
                if paidRolesData[0] > 0:
                    output += "`" + COMMAND_PREFIX + LIST_ROLES_COMMAND + "`: Will display a list of all roles available for purchase in " + currencyData[0] + ".\n"
                    output += "`" + COMMAND_PREFIX + BUY_ROLE_COMMAND + "`: Will allow you to buy any specified role for " + currencyData[0] + ".\n"
                    output += "`" + COMMAND_PREFIX + REFUND_ROLE_COMMAND + "`: Will allow you to return any specified role, and get a full refund in " + currencyData[0] + ".\n"
            if rulesData[0] > 0 or isManagePerms:
                output += "\n*Rule management:*\n"
            if rulesData[0] > 0:
                output += "`" + COMMAND_PREFIX + RULE_GET_COMMAND + "`: Will output any rule I know of with the given number.\n"
            if isManagePerms:
                output += "`" + COMMAND_PREFIX + RULE_SET_COMMAND + "`: Use this command to inform me of a server rule I need to know about.\n"
                output += "`" + COMMAND_PREFIX + RULE_EDIT_COMMAND + "`: Use this command if you need to edit a server rule. Just provide the number, and the new rule.\n"
                output += "`" + COMMAND_PREFIX + RULE_DELETE_COMMAND + "`: Use this command if you want me to forget a particular server rule. Just provide the number, and I'll forget all about it.\n"
            if rulesData[0] > 0:
                output += "`" + COMMAND_PREFIX + RULE_GET_ALL_COMMAND + "`: Will send a copy of the server rules to your DMs.\n"
                if isManagePerms:
                    output += "`" + COMMAND_PREFIX + RULE_GET_BACKUP_COMMAND + "`: Will send a backup of the server rules to your DMs, to allow for easy recovery in the event of a database failure.\n"
                    output += "`" + COMMAND_PREFIX + RULE_CHANNEL_SET_COMMAND + "`: Will set which channel to post the server rules in. This post will be continually updated as the rules change.\n"
                    output += "`" + COMMAND_PREFIX + RULE_CHANNEL_CLEAR_COMMAND + "`: Will delete the official posting of the server rules.\n"
            if userPerms.kick_members or userPerms.ban_members:
                output += "\n*Moderation:*\n"
            if userPerms.kick_members:
                output += "`" + COMMAND_PREFIX + MOD_MUTE_COMMAND + "`: Will mute the specified user in the specified channel, or all channels if none is specified.\n"
                output += "`" + COMMAND_PREFIX + MOD_UNMUTE_COMMAND + "`: Will unmute the specified user in the specified channel, or all channels if none is specified.\n"
                output += "`" + COMMAND_PREFIX + MOD_KICK_COMMAND + "`: Will kick the specified user. Specify the reason after mentioning the user.\n"
            if userPerms.ban_members:
                output += "`" + COMMAND_PREFIX + MOD_BAN_SIMPLE_COMMAND + "`: Will ban the specified user. Specify the reason after mentioning the user.\n"
                if userPerms.manage_messages:
                    output += "`" + COMMAND_PREFIX + MOD_BAN_DELETE_COMMAND + "`: Will ban the specified user, and delete all messages over the past 24 hours. Specify the reason after mentioning the user.\n"
        elif isinstance(message.channel, discord.DMChannel):
            if message.author.id == MIDNIGHTS_TRUE_MASTER and IS_ECHO_ENABLED:
                output += "`" + COMMAND_PREFIX + ECHO_COMMAND + "`: With this command I will forward anything you tell me to, to the channel ID specified, assuming I can actually access the channel specified.\n"
            output += "`" + COMMAND_PREFIX + CLEAR_DMS_COMMAND + "`: Will delete any DM I've sent to you, when specified with a message ID. Will delete all my DMs if no ID is provided.\n"
            if message.author.id == MIDNIGHTS_TRUE_MASTER:
                output += "`" + COMMAND_PREFIX + REMOTE_ADMIN_SERVER_LIST_COMMAND + "`: Will list all servers I'm currently running on.\n"
                output += "`" + COMMAND_PREFIX + REMOTE_ADMIN_SERVER_REMOVE_COMMAND + "`: Will remove me from whatever server is specified by ID or full name.\n"
                output += "`" + COMMAND_PREFIX + REMOTE_ADMIN_CHANNEL_LIST_COMMAND + "`: Will list all channels I can see in the specified server.\n"
                output += "`" + COMMAND_PREFIX + REMOTE_ADMIN_GET_PERMS_COMMAND + "`: Will list all my permissions in the channel or server specified.\n"

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

async def sourceCode(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + SOURCE_CODE_COMMAND:
        if isinstance(message.channel, discord.TextChannel):
            await message.channel.send("A link has been sent to your DMs.")
            await message.author.create_dm()
            DMChannel = message.author.dm_channel
        else:
            DMChannel = message.channel
        output = "So, you would like to take a look at my full source code... Naughty...\n"
        output += "Well, I'm licenced under the GNU AGPL version 3, so I guess I'm obliged.\n"
        output += "It's available at: https://github.com/theblackwidower/MidnightStarshineBot"
        await DMChannel.send(output)

async def sanctuaryInvite(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + SANCTUARY_COMMAND:
        if isinstance(message.channel, discord.TextChannel):
            await message.channel.send("An invite has been sent to your DMs.")
            await message.author.create_dm()
            DMChannel = message.author.dm_channel
        else:
            DMChannel = message.channel
        output = "You want to visit my personal sanctuary?\n"
        output += "Well... come on in...\n"
        output += "https://discord.gg/Qekr2CW"
        await DMChannel.send(output)

async def ghostPingDetector(message):
    if IS_GHOST_PING_DETECTOR_ENABLED and message.created_at + GHOST_PING_DETECTOR_THRESHOLD >= datetime.datetime.now():
        roleMentions = message.role_mentions
        bigRolesMentioned = []
        if len(roleMentions) > 0:
            memberCount = message.guild.member_count
            threshold = math.floor(memberCount * BIG_ROLE_THRESHOLD)
            for role in roleMentions:
                if len(role.members) >= threshold:
                    bigRolesMentioned.append(role)
        if message.mention_everyone or len(bigRolesMentioned) > 0:
            roleList = ""
            if len(bigRolesMentioned) > 0:
                roleList += " to"
                for role in bigRolesMentioned:
                    roleList += " '" + role.name + "',"
            output = await message.channel.send("The preceding *ghost ping*" + roleList + " was brought to you by " + message.author.mention + " for reasons unknown.")
            ghostReportRecord[output.id] = (message.author, roleList, 0)

async def reportSupressionDetector(message):
    if message.id in ghostReportRecord and message.created_at + GHOST_PING_DETECTOR_THRESHOLD >= datetime.datetime.now():
        culprit, roleList, count = ghostReportRecord[message.id]
        count += 1
        outputContent = "The preceding "
        for i in range(count):
            outputContent += "supression of a report of a "
        outputContent += "*ghost ping*" + roleList + " was brought to you by " + culprit.mention + " for reasons well-known... "
        if count < 5:
            outputContent += "their own cowardace."
        else:
            outputContent += "their own ridiculously, pathetically persistant cowardace."
        output = await message.channel.send(outputContent)
        ghostReportRecord[output.id] = (culprit, count)
        del ghostReportRecord[message.id]

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

        content = content.strip()
        messageLength = len(content)

        unicodeEmojis = EMOJI_DETECTOR.findall(content)
        emojiCount += len(unicodeEmojis)
        messageLength -= len(unicodeEmojis)

        if (emojiCount > 0 and (messageLength < 3 or messageLength <= emojiCount)):
            await message.delete()

async def echo(message):
    if IS_ECHO_ENABLED:
        parsing = message.content.partition(" ")
        if parsing[0] == COMMAND_PREFIX + ECHO_COMMAND and message.author.id == MIDNIGHTS_TRUE_MASTER:
            if isinstance(message.channel, discord.DMChannel):
                parsing = parsing[2].partition(" ")
                if parsing[0].isdigit():
                    channel = await client.fetch_channel(int(parsing[0]))
                    if channel is None:
                        await message.channel.send("Can't find channel.")
                    else:
                        await channel.send(parsing[2])
                        await message.channel.send("Message posted.")
                else:
                    await message.channel.send("Invalid channel ID.")
            else:
                await message.channel.send(parsing[2])
                await message.delete()

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

client.run(DISCORD_TOKEN)
