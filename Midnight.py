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
import math
import re

import sys
import traceback

from Constants import *
from Utilities import *

from RemoteAdmin import *
from ActiveRole import *
from PromoterRole import *
from BumperRole import *
from Economy import *
from Rules import *
from Moderation import *
from RoleControl import *
from CustomizedCode import *

IS_EMOJI_CENSOR_ENABLED = False
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

ALTERNATE_SPEAKERS = [MIDNIGHTS_TRUE_MASTER, 643983207649509376, 189392828546154497, 459194971522727940]

ghostReportRecord = dict()

GHOST_PING_DETECTOR_THRESHOLD = datetime.timedelta(minutes=3)

BIG_ROLE_THRESHOLD = 0.75

# ref: https://gist.github.com/Vexs/a8fd95377ca862ca13fe6d0f0e42737e
EMOJI_DETECTOR = re.compile("<a?:[A-z_]+:\d+>|(?:\U0001f1e6[\U0001f1e8-\U0001f1ec\U0001f1ee\U0001f1f1\U0001f1f2\U0001f1f4\U0001f1f6-\U0001f1fa\U0001f1fc\U0001f1fd\U0001f1ff])|(?:\U0001f1e7[\U0001f1e6\U0001f1e7\U0001f1e9-\U0001f1ef\U0001f1f1-\U0001f1f4\U0001f1f6-\U0001f1f9\U0001f1fb\U0001f1fc\U0001f1fe\U0001f1ff])|(?:\U0001f1e8[\U0001f1e6\U0001f1e8\U0001f1e9\U0001f1eb-\U0001f1ee\U0001f1f0-\U0001f1f5\U0001f1f7\U0001f1fa-\U0001f1ff])|(?:\U0001f1e9[\U0001f1ea\U0001f1ec\U0001f1ef\U0001f1f0\U0001f1f2\U0001f1f4\U0001f1ff])|(?:\U0001f1ea[\U0001f1e6\U0001f1e8\U0001f1ea\U0001f1ec\U0001f1ed\U0001f1f7-\U0001f1fa])|(?:\U0001f1eb[\U0001f1ee-\U0001f1f0\U0001f1f2\U0001f1f4\U0001f1f7])|(?:\U0001f1ec[\U0001f1e6\U0001f1e7\U0001f1e9-\U0001f1ee\U0001f1f1-\U0001f1f3\U0001f1f5-\U0001f1fa\U0001f1fc\U0001f1fe])|(?:\U0001f1ed[\U0001f1f0\U0001f1f2\U0001f1f3\U0001f1f7\U0001f1f9\U0001f1fa])|(?:\U0001f1ee[\U0001f1e8-\U0001f1ea\U0001f1f1-\U0001f1f4\U0001f1f6-\U0001f1f9])|(?:\U0001f1ef[\U0001f1ea\U0001f1f2\U0001f1f4\U0001f1f5])|(?:\U0001f1f0[\U0001f1ea\U0001f1ec-\U0001f1ee\U0001f1f2\U0001f1f3\U0001f1f5\U0001f1f7\U0001f1fc\U0001f1fe\U0001f1ff])|(?:\U0001f1f1[\U0001f1e6-\U0001f1e8\U0001f1ee\U0001f1f0\U0001f1f7-\U0001f1fb\U0001f1fe])|(?:\U0001f1f2[\U0001f1e6\U0001f1e8-\U0001f1ed\U0001f1f0-\U0001f1ff])|(?:\U0001f1f3[\U0001f1e6\U0001f1e8\U0001f1ea-\U0001f1ec\U0001f1ee\U0001f1f1\U0001f1f4\U0001f1f5\U0001f1f7\U0001f1fa\U0001f1ff])|\U0001f1f4\U0001f1f2|(?:\U0001f1f4[\U0001f1f2])|(?:\U0001f1f5[\U0001f1e6\U0001f1ea-\U0001f1ed\U0001f1f0-\U0001f1f3\U0001f1f7-\U0001f1f9\U0001f1fc\U0001f1fe])|\U0001f1f6\U0001f1e6|(?:\U0001f1f6[\U0001f1e6])|(?:\U0001f1f7[\U0001f1ea\U0001f1f4\U0001f1f8\U0001f1fa\U0001f1fc])|(?:\U0001f1f8[\U0001f1e6-\U0001f1ea\U0001f1ec-\U0001f1f4\U0001f1f7-\U0001f1f9\U0001f1fb\U0001f1fd-\U0001f1ff])|(?:\U0001f1f9[\U0001f1e6\U0001f1e8\U0001f1e9\U0001f1eb-\U0001f1ed\U0001f1ef-\U0001f1f4\U0001f1f7\U0001f1f9\U0001f1fb\U0001f1fc\U0001f1ff])|(?:\U0001f1fa[\U0001f1e6\U0001f1ec\U0001f1f2\U0001f1f8\U0001f1fe\U0001f1ff])|(?:\U0001f1fb[\U0001f1e6\U0001f1e8\U0001f1ea\U0001f1ec\U0001f1ee\U0001f1f3\U0001f1fa])|(?:\U0001f1fc[\U0001f1eb\U0001f1f8])|\U0001f1fd\U0001f1f0|(?:\U0001f1fd[\U0001f1f0])|(?:\U0001f1fe[\U0001f1ea\U0001f1f9])|(?:\U0001f1ff[\U0001f1e6\U0001f1f2\U0001f1fc])|(?:\U0001f3f3\ufe0f\u200d\U0001f308)|(?:\U0001f441\u200d\U0001f5e8)|(?:[\U0001f468\U0001f469]\u200d\u2764\ufe0f\u200d(?:\U0001f48b\u200d)?[\U0001f468\U0001f469])|(?:(?:(?:\U0001f468\u200d[\U0001f468\U0001f469])|(?:\U0001f469\u200d\U0001f469))(?:(?:\u200d\U0001f467(?:\u200d[\U0001f467\U0001f466])?)|(?:\u200d\U0001f466\u200d\U0001f466)))|(?:(?:(?:\U0001f468\u200d\U0001f468)|(?:\U0001f469\u200d\U0001f469))\u200d\U0001f466)|[\u2194-\u2199]|[\u23e9-\u23f3]|[\u23f8-\u23fa]|[\u25fb-\u25fe]|[\u2600-\u2604]|[\u2638-\u263a]|[\u2648-\u2653]|[\u2692-\u2694]|[\u26f0-\u26f5]|[\u26f7-\u26fa]|[\u2708-\u270d]|[\u2753-\u2755]|[\u2795-\u2797]|[\u2b05-\u2b07]|[\U0001f191-\U0001f19a]|[\U0001f1e6-\U0001f1ff]|[\U0001f232-\U0001f23a]|[\U0001f300-\U0001f321]|[\U0001f324-\U0001f393]|[\U0001f399-\U0001f39b]|[\U0001f39e-\U0001f3f0]|[\U0001f3f3-\U0001f3f5]|[\U0001f3f7-\U0001f3fa]|[\U0001f400-\U0001f4fd]|[\U0001f4ff-\U0001f53d]|[\U0001f549-\U0001f54e]|[\U0001f550-\U0001f567]|[\U0001f573-\U0001f57a]|[\U0001f58a-\U0001f58d]|[\U0001f5c2-\U0001f5c4]|[\U0001f5d1-\U0001f5d3]|[\U0001f5dc-\U0001f5de]|[\U0001f5fa-\U0001f64f]|[\U0001f680-\U0001f6c5]|[\U0001f6cb-\U0001f6d2]|[\U0001f6e0-\U0001f6e5]|[\U0001f6f3-\U0001f6f6]|[\U0001f910-\U0001f91e]|[\U0001f920-\U0001f927]|[\U0001f933-\U0001f93a]|[\U0001f93c-\U0001f93e]|[\U0001f940-\U0001f945]|[\U0001f947-\U0001f94b]|[\U0001f950-\U0001f95e]|[\U0001f980-\U0001f991]|\u00a9|\u00ae|\u203c|\u2049|\u2122|\u2139|\u21a9|\u21aa|\u231a|\u231b|\u2328|\u23cf|\u24c2|\u25aa|\u25ab|\u25b6|\u25c0|\u260e|\u2611|\u2614|\u2615|\u2618|\u261d|\u2620|\u2622|\u2623|\u2626|\u262a|\u262e|\u262f|\u2660|\u2663|\u2665|\u2666|\u2668|\u267b|\u267f|\u2696|\u2697|\u2699|\u269b|\u269c|\u26a0|\u26a1|\u26aa|\u26ab|\u26b0|\u26b1|\u26bd|\u26be|\u26c4|\u26c5|\u26c8|\u26ce|\u26cf|\u26d1|\u26d3|\u26d4|\u26e9|\u26ea|\u26fd|\u2702|\u2705|\u270f|\u2712|\u2714|\u2716|\u271d|\u2721|\u2728|\u2733|\u2734|\u2744|\u2747|\u274c|\u274e|\u2757|\u2763|\u2764|\u27a1|\u27b0|\u27bf|\u2934|\u2935|\u2b1b|\u2b1c|\u2b50|\u2b55|\u3030|\u303d|\u3297|\u3299|\U0001f004|\U0001f0cf|\U0001f170|\U0001f171|\U0001f17e|\U0001f17f|\U0001f18e|\U0001f201|\U0001f202|\U0001f21a|\U0001f22f|\U0001f250|\U0001f251|\U0001f396|\U0001f397|\U0001f56f|\U0001f570|\U0001f587|\U0001f590|\U0001f595|\U0001f596|\U0001f5a4|\U0001f5a5|\U0001f5a8|\U0001f5b1|\U0001f5b2|\U0001f5bc|\U0001f5e1|\U0001f5e3|\U0001f5e8|\U0001f5ef|\U0001f5f3|\U0001f6e9|\U0001f6eb|\U0001f6ec|\U0001f6f0|\U0001f930|\U0001f9c0|[#|0-9]\u20e3")

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
    await persistBumperRole(member)
    await persistMute(member)
    await persistTimeout(member)
    await recordRecruit(member)

@client.event
async def on_guild_join(server):
    setupDataCache(server.id)
    await yagSnipe(server.get_member(YAG_ID))
    await rylanSnipeServer(server)
    await reportServerJoin(server, client)

@client.event
async def on_guild_remove(server):
    await reportServerLeave(server, client)

@client.event
async def on_guild_role_update(before, after):
    await yagSnipe(after.guild.get_member(YAG_ID))
    await rylanSnipeServer(after.guild)

@client.event
async def on_member_update(before, after):
    await rylanSnipe(after)
    await persistActive(after)
    await persistBuyablesMember(after)
    await persistPromoterRole(after)
    await persistBumperRole(after)
    await checkRoleControl(before, after)
    await ponyVersePersistElementRole(after)

@client.event
async def on_message(message):
    await emojiCensor(message)
    if message.content.casefold().startswith(COMMAND_PREFIX):
        parsing = message.content.partition(" ")
        command = parsing[0][len(COMMAND_PREFIX):].casefold()
        commandArgs = parsing[2].strip()
        if command == HELP_COMMAND:
            await help(message)
        elif command == SOURCE_CODE_COMMAND:
            await sourceCode(message)
        elif command == SANCTUARY_COMMAND:
            await sanctuaryInvite(message)
        elif command == ECHO_COMMAND:
            await echo(message, commandArgs)
        elif isinstance(message.channel, discord.TextChannel):
            if command == ROLECALL_COMMAND:
                await rolecall(message, commandArgs)

            elif command == PAYDAY_SETUP_COMMAND:
                await setupPayday(message, commandArgs)
            elif command == PAYDAY_CLEAR_COMMAND:
                await clearPayday(message)
            elif command == PAYDAY_COMMAND:
                await payday(message)
            elif command == BALANCE_COMMAND:
                await balance(message)
            elif command == BUY_ROLE_SETUP_COMMAND:
                await setupRole(message, commandArgs)
            elif command == BUY_ROLE_REMOVE_COMMAND:
                await removeRole(message, commandArgs)
            elif command == LIST_ROLES_COMMAND:
                await roleMenu(message)
            elif command == BUY_ROLE_COMMAND:
                await buyRole(message, commandArgs)
            elif command == REFUND_ROLE_COMMAND:
                await refundRole(message, commandArgs)

            elif command == SETUP_ACTIVE_ROLE_COMMAND:
                await setupActive(message, commandArgs)
            elif command == CLEAR_ACTIVE_ROLE_COMMAND:
                await clearActive(message)
            elif command == SETUP_PROMOTER_ROLE_COMMAND:
                await setupPromoterRole(message, commandArgs)
            elif command == CLEAR_PROMOTER_ROLE_COMMAND:
                await clearPromoterRole(message)
            elif command == SETUP_BUMPER_ROLE_COMMAND:
                await setupBumperRole(message, commandArgs)
            elif command == CLEAR_BUMPER_ROLE_COMMAND:
                await clearBumperRole(message)
            elif command == SCAN_BUMP_CHANNEL_COMMAND:
                await scanForBumps(message, commandArgs, client)
            elif command == BUMP_BOARD_SET_COMMAND:
                await setBumpLeaderboardChannel(message, commandArgs, client)
            elif command == BUMP_BOARD_CLEAR_COMMAND:
                await clearBumpLeaderboardChannel(message)

            elif command == CREATE_ROLE_GROUP_COMMAND:
                await createRoleGroup(message, commandArgs)
            elif command == DELETE_ROLE_GROUP_COMMAND:
                await deleteRoleGroup(message, commandArgs)
            elif command == ADD_TO_ROLE_GROUP_COMMAND:
                await addToRoleGroup(message, commandArgs)
            elif command == REMOVE_FROM_ROLE_GROUP_COMMAND:
                await removeFromRoleGroup(message, commandArgs)

            elif command == RULE_SET_COMMAND:
                await setRule(message, commandArgs)
            elif command == RULE_GET_COMMAND:
                await getRule(message, commandArgs)
            elif command == RULE_EDIT_COMMAND:
                await editRule(message, commandArgs)
            elif command == RULE_DELETE_COMMAND:
                await deleteRule(message, commandArgs)
            elif command == RULE_GET_ALL_COMMAND:
                await getAllRules(message)
            elif command == RULE_GET_BACKUP_COMMAND:
                await getRuleBackup(message)
            elif command == RULE_CHANNEL_SET_COMMAND:
                await setRuleChannel(message, commandArgs)
            elif command == RULE_CHANNEL_CLEAR_COMMAND:
                await clearRuleChannel(message)

            elif command == MOD_MUTE_ROLE_SETUP_COMMAND:
                await setupMuteRole(message, commandArgs)
            elif command == MOD_MUTE_COMMAND:
                await mute(message, commandArgs)
            elif command == MOD_UNMUTE_COMMAND:
                await unmute(message, commandArgs)
            elif command == MOD_TIMEOUT_SETUP_COMMAND:
                await setupTimeout(message, commandArgs)
            elif command == MOD_TIMEOUT_ROLE_SETUP_COMMAND:
                await setupTimeoutRole(message, commandArgs)
            elif command == MOD_TIMEOUT_COMMAND:
                await timeout(message, commandArgs)
            elif command == MOD_TIMEIN_COMMAND:
                await timein(message, commandArgs)
            elif command == MOD_KICK_COMMAND:
                await kick(message, commandArgs)
            elif command == MOD_BAN_SIMPLE_COMMAND:
                await ban(message, commandArgs)
            elif command == MOD_BAN_DELETE_COMMAND:
                await banDelete(message, commandArgs)
        elif isinstance(message.channel, discord.DMChannel):
            if command == CLEAR_DMS_COMMAND:
                await clearDms(message, commandArgs)
            elif command == REMOTE_ADMIN_SERVER_LIST_COMMAND:
                await listServers(message, client)
            elif command == REMOTE_ADMIN_SERVER_REMOVE_COMMAND:
                await leaveServer(message, commandArgs, client)
            elif command == REMOTE_ADMIN_CHANNEL_LIST_COMMAND:
                await listServerChannels(message, commandArgs, client)
            elif command == REMOTE_ADMIN_GET_PERMS_COMMAND:
                await getPerms(message, commandArgs, client)
    await recordBump(message, client)
    await checkActive(message)

@client.event
async def on_message_edit(old_message, message):
    await emojiCensor(message)

@client.event
async def on_message_delete(message):
    await ghostPingDetector(message)
    await reportSupressionDetector(message)

@client.event
async def on_guild_role_delete(role):
    await roleDeleted(role)

@client.event
async def on_member_ban(server, user):
    await deleteInvites(server, user)

@client.event
async def on_guild_channel_create(channel):
    await setupChannelModRoles(channel)

async def help(message):
    userPerms = message.author.permissions_in(message.channel)
    isManagePerms = userPerms.manage_guild

    output = "Hello, I am Midnight Starshine. Your friendly neighbourhood Discord bot. Here to help in any way I can.\n"

    output += "\n**COMMANDS:**\n"
    output += "`" + COMMAND_PREFIX + HELP_COMMAND + "`: Outputs this help file.\n"
    output += "`" + COMMAND_PREFIX + SOURCE_CODE_COMMAND + "`: I'm licenced under the GNU AGPL version 3. This means you are fully entitled to look at my full source code. Enter this command and I'll send you a link to my GitHub repository.\n"
    output += "`" + COMMAND_PREFIX + SANCTUARY_COMMAND + "`: Every girl needs a place to unwind. I have my very special sanctuary. If you'd like an invite to **\"Moonlight's Sanctuary\"**. Just use this command.\n"
    if isinstance(message.channel, discord.TextChannel):
        conn = await getConnection()
        try:
            paydayData = await conn.fetchrow('SELECT amount, cooldown FROM tbl_payday_settings WHERE server = $1', message.guild.id)
            currencyData = await conn.fetchrow('SELECT currency_name FROM tbl_currency WHERE server = $1', message.guild.id)
            paidRolesData = await conn.fetchrow('SELECT COUNT(role) FROM tbl_paid_roles WHERE server = $1', message.guild.id)
            rulesData = await conn.fetchrow('SELECT COUNT(content) FROM tbl_rules WHERE server = $1', message.guild.id)
            timeoutData = await conn.fetchrow('SELECT channel FROM tbl_timeout_channel WHERE server = $1', message.guild.id)
        finally:
            await returnConnection(conn)
        if message.author.id in ALTERNATE_SPEAKERS:
            output += "`" + COMMAND_PREFIX + ECHO_COMMAND + "`: With this command I will repeat anything you, " + message.author.display_name + ", and a select few, tell me to.\n"
        if isManagePerms:
            output += "`" + COMMAND_PREFIX + ROLECALL_COMMAND + "`: Will output a list of all members, sorted by their top role. Can be filtered by including the name of any role (case sensitive).\n"
            output += "\n*Active Role Function:*\n"
            output += "`" + COMMAND_PREFIX + SETUP_ACTIVE_ROLE_COMMAND + "`: Use to setup the active role feature. Enter the command, followed by the role, gap between messages to define as 'active', minimum duration of activity, and maximum duration of inactivity.\n"
            output += "`" + COMMAND_PREFIX + CLEAR_ACTIVE_ROLE_COMMAND + "`: Use to disable the active role feature. If you want to reenable it, you'll have to run the setup command again.\n"
            output += "\n*Promoter Role Function:*\n"
            output += "`" + COMMAND_PREFIX + SETUP_PROMOTER_ROLE_COMMAND + "`: Use to setup the promoter role feature. Enter the command, followed by the role, and the number of recrutments one would need to qualify for the role.\n"
            output += "`" + COMMAND_PREFIX + CLEAR_PROMOTER_ROLE_COMMAND + "`: Use to disable the promoter role feature. If you want to reenable it, you'll have to run the setup command again.\n"
            output += "\n*Bumper Role Function:*\n"
            output += "`" + COMMAND_PREFIX + SETUP_BUMPER_ROLE_COMMAND + "`: Use to setup the bumper role feature. Enter the command, followed by the role, and the number of successful bumps one would need to have done to qualify for the role.\n"
            output += "`" + COMMAND_PREFIX + CLEAR_BUMPER_ROLE_COMMAND + "`: Use to disable the bumper role feature. If you want to reenable it, you'll have to run the setup command again.\n"
            output += "`" + COMMAND_PREFIX + SCAN_BUMP_CHANNEL_COMMAND + "`: Use to scan a particular channel for any and all server bump records. This is so any historical bumps will be counted toward the total, even if they occured before the feature was first implemented.\n"
            output += "`" + COMMAND_PREFIX + BUMP_BOARD_SET_COMMAND + "`: Will set which channel to post the bump leaderboard in. This post will be continually updated as bumps are made.\n"
            output += "`" + COMMAND_PREFIX + BUMP_BOARD_CLEAR_COMMAND + "`: Will delete the official posting of the bump leaderboard.\n"
            output += "\n*Role restrictions:*\n"
            output += "`" + COMMAND_PREFIX + CREATE_ROLE_GROUP_COMMAND + "`: Creates a new role group. This will restrict all members to select only one role from each group.\n"
            output += "`" + COMMAND_PREFIX + DELETE_ROLE_GROUP_COMMAND + "`: Deletes an existant role group.\n"
            output += "`" + COMMAND_PREFIX + ADD_TO_ROLE_GROUP_COMMAND + "`: Adds a role to a group. Provide the group name, and then the role.\n"
            output += "`" + COMMAND_PREFIX + REMOVE_FROM_ROLE_GROUP_COMMAND + "`: Removes a role from a group. Provide the group name, and then the role.\n"
        if isManagePerms or paydayData is not None or (currencyData is not None and (userPerms.manage_roles or paidRolesData[0] > 0)):
            output += "\n*Buyable roles:*\n"
        if isManagePerms:
            output += "`" + COMMAND_PREFIX + PAYDAY_SETUP_COMMAND + "`: Can be used to set up the parameters of the payday command. Run the command, followed by the amount of money you want to give the users, the name of the currency, and finally, the cooldown time.\n"
            output += "`" + COMMAND_PREFIX + PAYDAY_CLEAR_COMMAND + "`: Use to disable the payday command. If you want to reenable it, you'll have to run the setup command again.\n"
        if paydayData is not None:
            output += "`" + COMMAND_PREFIX + PAYDAY_COMMAND + "`: Will put " + str(paydayData[0]) + " " + currencyData[0] + " into your account. Can only be run once every " + timeDeltaToString(paydayData[1]) + ".\n"
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
        if isManagePerms or userPerms.kick_members or userPerms.ban_members:
            output += "\n*Moderation:*\n"
        if isManagePerms:
            output += "`" + COMMAND_PREFIX + MOD_MUTE_ROLE_SETUP_COMMAND + "`: Can be used to set up a special role for the mute function. This'll speed up and simplify excution while still maintaining the system's strength.\n"
        if userPerms.kick_members:
            output += "`" + COMMAND_PREFIX + MOD_MUTE_COMMAND + "`: Will mute the specified user in the specified channel, or all channels if none is specified.\n"
            output += "`" + COMMAND_PREFIX + MOD_UNMUTE_COMMAND + "`: Will unmute the specified user in the specified channel, or all channels if none is specified.\n"
        if isManagePerms:
            output += "`" + COMMAND_PREFIX + MOD_TIMEOUT_SETUP_COMMAND + "`: Can be used to set up timeouts, which restricts a user to a single channel or category specifically for that purpose. Just specify the channel or category, and you're all set.\n"
            output += "`" + COMMAND_PREFIX + MOD_TIMEOUT_ROLE_SETUP_COMMAND + "`: Can be used to set up a special role for the timeout function. This'll speed up and simplify excution while still maintaining the system's strength."
            if timeoutData is None:
                output += " Please be sure to run the `" + COMMAND_PREFIX + MOD_TIMEOUT_SETUP_COMMAND + "` command before attempting to set up the role."
            output += "\n"
        if userPerms.kick_members:
            if timeoutData is not None:
                output += "`" + COMMAND_PREFIX + MOD_TIMEOUT_COMMAND + "`: Will isolate the specified user to a single channel: <#" + str(timeoutData[0]) + ">\n"
                output += "`" + COMMAND_PREFIX + MOD_TIMEIN_COMMAND + "`: Will return the specified user from their timeout in <#" + str(timeoutData[0]) + ">.\n"
            output += "`" + COMMAND_PREFIX + MOD_KICK_COMMAND + "`: Will kick the specified user. Specify the reason after mentioning the user.\n"
        if userPerms.ban_members:
            output += "`" + COMMAND_PREFIX + MOD_BAN_SIMPLE_COMMAND + "`: Will ban the specified user. Specify the reason after mentioning the user.\n"
            if userPerms.manage_messages:
                output += "`" + COMMAND_PREFIX + MOD_BAN_DELETE_COMMAND + "`: Will ban the specified user, and delete all messages over the past 24 hours. Specify the reason after mentioning the user.\n"
    elif isinstance(message.channel, discord.DMChannel):
        if message.author.id in ALTERNATE_SPEAKERS:
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

async def emojiCensor(message):
    if isinstance(message.channel, discord.TextChannel) and IS_EMOJI_CENSOR_ENABLED:
        emojiCount = 0
        textLength = len(message.content)

        emojis = EMOJI_DETECTOR.findall(message.content)
        for emoji in emojis:
            emojiCount += 1
            textLength -= len(emoji)

        if (emojiCount > 0 and (textLength < 3 or textLength <= emojiCount)):
            await message.delete()

async def echo(message, commandArgs):
    if message.author.id in ALTERNATE_SPEAKERS:
        sentMessage = None
        if isinstance(message.channel, discord.DMChannel):
            parsing = commandArgs.partition(" ")
            if parsing[0].isdigit():
                channel = await client.fetch_channel(int(parsing[0]))
                if channel is None:
                    await message.channel.send("Can't find channel.")
                else:
                    sentMessage = await channel.send(parsing[2])
                    await message.channel.send("Message posted.")
            else:
                await message.channel.send("Invalid channel ID.")
        else:
            sentMessage = await message.channel.send(parsing[2])
            await message.delete()
        if message.author.id != MIDNIGHTS_TRUE_MASTER:
            master = client.get_user(MIDNIGHTS_TRUE_MASTER)
            await master.create_dm()
            await master.dm_channel.send(message.author.mention + " told me to say: \"" + sentMessage.content + "\" in: " + sentMessage.guild.name + " " + sentMessage.channel.mention)

async def rolecall(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        scannedRole = None
        if len(commandArgs) > 0:
            scannedRole = parseRole(message.guild, commandArgs)
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

async def clearDms(message, commandArgs):
    meBot = message.channel.me
    if commandArgs == "":
        async for thisMessage in message.channel.history(limit=1000000, oldest_first=False):
            if thisMessage.author == meBot:
                await thisMessage.delete()
        await message.channel.send("Cleared all DMs I sent to you.")
    elif commandArgs.isdigit():
        try:
            thisMessage = await message.channel.fetch_message(int(commandArgs))
            if thisMessage.author == meBot:
                await thisMessage.delete()
            else:
                await message.channel.send("This isn't my message.")
        except discord.NotFound:
            await message.channel.send("Message " + commandArgs + " not found.")
    else:
        await message.channel.send("Not a valid message number.")

client.run(DISCORD_TOKEN)
