# ------------------------------------------------------------------------------
#      MidnightStarshineBot - a multipurpose Discord bot
#      Copyright (C) 2022  T. Duke Perry
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU Affero General Public License as published
#      by the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU Affero General Public License for more details.
#
#      You should have received a copy of the GNU Affero General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

import discord

from Constants import *
from Utilities import *

SETUP_BUMPER_ROLE_COMMAND = "setupbumperrole"
CLEAR_BUMPER_ROLE_COMMAND = "clearbumperrole"
SCAN_BUMP_CHANNEL_COMMAND = "scanforbumps"
BUMP_BOARD_SET_COMMAND = "setbumpboardchannel"
BUMP_BOARD_CLEAR_COMMAND = "clearbumpboardchannel"

DISBOARD_BOT_ID = 302050872383242240
SUCCESSFUL_DISBOARD_BUMP_MESSAGE = "Bump done :thumbsup:"

async def setupBumperRole(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        parsing = commandArgs.rpartition(" ")
        bumpCountString = parsing[2]
        roleString = parsing[0]

        if roleString == "" or bumpCountString == "":
            await message.channel.send("I'm missing some information, I'm sure of it. You need to provide me with a role, and a number of bumps needed to qualify for the role.")
        else:
            role = parseRole(message.guild, roleString)
            if role is None:
                await message.channel.send("Cannot find the role entered.")
            elif not bumpCountString.isdigit():
                await message.channel.send("What you provided for number of bumps is not a number.")
            else:
                bumpCount = int(bumpCountString)
                conn = await getConnection()
                try:
                    serverCountData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_bumper_role_settings WHERE server = $1 AND bump_count = $2', message.guild.id, bumpCount)
                    serverRoleData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_bumper_role_settings WHERE server = $1 AND role = $2', message.guild.id, role.id)
                    if serverCountData[0] > 0 and serverRoleData[0] > 0:
                        output = "Bumper role has already been setup with those parameters.\n"
                    else:
                        if serverCountData[0] > 0:
                            await conn.execute('UPDATE tbl_bumper_role_settings SET role = $1 WHERE server = $2 AND bump_count = $3', role.id, message.guild.id, bumpCount)
                            output = "Bumper role successfully updated with the following parameters:\n"
                        elif serverRoleData[0] > 0:
                            await conn.execute('UPDATE tbl_bumper_role_settings SET bump_count = $1 WHERE server = $2 AND role = $3', bumpCount, message.guild.id, role.id)
                            output = "Bumper role successfully updated with the following parameters:\n"
                        else:
                            await conn.execute('INSERT INTO tbl_bumper_role_settings (server, role, bump_count) VALUES ($1, $2, $3)', message.guild.id, role.id, bumpCount)
                            output = "New bumper role successfully set up with the following parameters:\n"
                        output += "We'll be assigning the \"__" + role.name + "__\" role...\n"
                        output += "... to any user who successfully bumps the server __" + str(bumpCount) + "__ times.\n"
                    await message.channel.send(output)
                finally:
                    await returnConnection(conn)

async def clearBumperRole(message):
    if message.author.permissions_in(message.channel).manage_guild:
        conn = await getConnection()
        try:
            serverData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_bumper_role_settings WHERE server = $1', message.guild.id)
            if serverData[0] > 0:
                await conn.execute('DELETE FROM tbl_bumper_role_settings WHERE server = $1', message.guild.id)
                del invitesCache[message.guild.id]
                await message.channel.send("Bumper role feature completely cleared out. If you want to reenable it, please run `" + getPrefix(message.guild) + SETUP_BUMPER_ROLE_COMMAND + "` again.")
            else:
                await message.channel.send("Bumper role feature has not even been set up, so there's no reason to clear it.")
        finally:
            await returnConnection(conn)

async def scanForBumps(message, commandArgs, client):
    if message.author.permissions_in(message.channel).manage_guild:
        channel = parseChannel(message.guild, commandArgs)
        disboardBot = message.guild.get_member(DISBOARD_BOT_ID)
        if disboardBot is None:
            await message.channel.send("Disboard Bot is not installed on the server.")
        elif channel is None:
            await message.channel.send("Could not find specified channel.")
        else:
            count = 0
            newCount = 0
            conn = await getConnection()
            try:
                async for thisMessage in channel.history(limit=None, oldest_first=True):
                    if thisMessage.author == disboardBot:
                        bumper = getBumper(thisMessage)
                        if bumper is not None:
                            count += 1
                            repetitionCheck = await conn.fetchrow('SELECT timebumped FROM tbl_bumping_record WHERE server = $1 AND bumper = $2 AND response_id = $3 AND timebumped = $4', thisMessage.guild.id, bumper.id, thisMessage.id, thisMessage.created_at)
                            if repetitionCheck is None:
                                newCount += 1
                                await conn.execute('INSERT INTO tbl_bumping_record (server, bumper, response_id, timebumped) VALUES ($1, $2, $3, $4)', thisMessage.guild.id, bumper.id, thisMessage.id, thisMessage.created_at)
            finally:
                await returnConnection(conn)

            if count == 0:
                countString = "no"
                newString = ""
            else:
                countString = str(count)
                newString = ", "
                if newCount == 0:
                    newString += "none"
                elif newCount == count:
                    newString += "all"
                else:
                    newString += str(newCount)
                newString += " of which are new"

            await message.channel.send("Found " + str(count) + " bumps in " + channel.mention + newString + ".")
            await updateBumpLeaderboardChannel(message, client)

def getBumper(message):
    bumper = None
    if message.author.id == DISBOARD_BOT_ID:
        if len(message.embeds) > 0:
            embedContent = message.embeds[0].description
            if embedContent.find(SUCCESSFUL_DISBOARD_BUMP_MESSAGE) > -1:
                userMention = embedContent.partition(",")
                bumper = parseMember(message.guild, userMention[0])
        elif message.content.find(SUCCESSFUL_DISBOARD_BUMP_MESSAGE) > -1:
            bumper = message.mentions[0]
    return bumper

async def recordBump(message, client):
    if message.author.id == DISBOARD_BOT_ID:
        conn = await getConnection()
        try:
            serverData = await conn.fetch('SELECT role, bump_count FROM tbl_bumper_role_settings WHERE server = $1', message.guild.id)
            if len(serverData) > 0:
                bumper = getBumper(message)
                if bumper is not None:
                    await conn.execute('INSERT INTO tbl_bumping_record (server, bumper, response_id, timebumped) VALUES ($1, $2, $3, $4)', message.guild.id, bumper.id, message.id, message.created_at)
                    countData = await conn.fetchrow('SELECT COUNT(timebumped) FROM tbl_bumping_record WHERE server = $1 AND bumper = $2', message.guild.id, bumper.id)
                    await returnConnection(conn)
                    await message.channel.send(getOrdinal(countData[0]) + " bump by " + bumper.mention + " recorded.")
                    for row in serverData:
                        role = message.guild.get_role(row[0])
                        if role is None:
                            await conn.execute('DELETE FROM tbl_bumper_role_settings WHERE server = $1 AND role = $2', message.guild.id, row[0])
                        else:
                            bumpCount = row[1]
                            if bumper.roles.count(role) == 0:
                                if countData[0] >= bumpCount:
                                    await bumper.add_roles(role, reason="Successfully bumped the server a total of " + str(countData[0]) + " times.")
                                else:
                                    break
                    await updateBumpLeaderboardChannel(message, client)
        finally:
            await returnConnection(conn)

async def persistBumperRole(member):
    if isinstance(member, discord.Member) and not member.bot:
        conn = await getConnection()
        try:
            serverData = await conn.fetch('SELECT role, bump_count FROM tbl_bumper_role_settings WHERE server = $1', member.guild.id)
            if len(serverData) > 0:
                recordData = await conn.fetchrow('SELECT COUNT(timebumped) FROM tbl_bumping_record WHERE server = $1 AND bumper = $2', member.guild.id, member.id)
                bumpCount = recordData[0]
                for row in serverData:
                    role = member.guild.get_role(row[0])
                    if role is None:
                        await conn.execute('DELETE FROM tbl_bumper_role_settings WHERE server = $1 AND role = $2', member.guild.id, row[0])
                    else:
                        minBumpCount = row[1]
                        if member.roles.count(role) > 0:
                            if bumpCount < minBumpCount:
                                await member.remove_roles(role, reason="This user does not qualify for the bumper role, as they have only bumped " + str(bumpCount) + " times out of the " + str(minBumpCount) + " they need.")
                        else:
                            if bumpCount >= minBumpCount:
                                await member.add_roles(role, reason="This user had their bumper role returned, since records show they bumped " + str(bumpCount) + " times, and they only need " + str(minBumpCount) + " to qualify.")
        finally:
            await returnConnection(conn)

async def setBumpLeaderboardChannel(message, commandArgs, client):
    if message.author.permissions_in(message.channel).manage_guild:
        if commandArgs == "":
            await message.channel.send("Please specify a channel for the bump leaderboard.")
        elif len(message.channel_mentions) == 0:
            await message.channel.send("Please specify a valid channel.")
        else:
            leaderboardChannel = message.channel_mentions[0]
            server_id = message.guild.id
            conn = await getConnection()
            try:
                oldData = await conn.fetchrow('SELECT channel FROM tbl_bump_leaderboard_posting WHERE server = $1', server_id)
                if oldData is not None and oldData[0] == leaderboardChannel.id:
                    await message.channel.send("The leaderboard is already posted in that channel.")
                else:
                    leaderboardData = await conn.fetch('SELECT bumper, COUNT(response_id) FROM tbl_bumping_record WHERE server = $1 GROUP BY bumper ORDER BY COUNT(response_id) DESC', server_id)
                    count = len(leaderboardData)
                    leaderboardOutput = "**LEADERBOARD:**"
                    rank = 0
                    for i in range(count):
                        if i == 0 or leaderboardData[i - 1][1] != leaderboardData[i][1]:
                            rank = str(i + 1)
                        member = message.guild.get_member(leaderboardData[i][0])
                        if member is None:
                            member = client.get_user(leaderboardData[i][0])
                        if member is None:
                            memberName = "<@" + str(leaderboardData[i][0]) + ">"
                        else:
                            memberName = member.display_name
                        leaderboardOutput += "\n" + rank + ": " + memberName + " - " + str(leaderboardData[i][1]) + " bumps"
                    leaderboardMessage = await leaderboardChannel.send(leaderboardOutput)
                    if oldData is None:
                        await conn.execute('INSERT INTO tbl_bump_leaderboard_posting (server, channel, message) VALUES ($1, $2, $3)', server_id, leaderboardChannel.id, leaderboardMessage.id)
                    else:
                        await conn.execute('UPDATE tbl_bump_leaderboard_posting SET channel = $1, message = $2 WHERE server = $3', leaderboardChannel.id, leaderboardMessage.id, server_id)
                    await message.channel.send("Leaderboard now posted in " + leaderboardChannel.mention + ".")
            finally:
                await returnConnection(conn)

async def clearBumpLeaderboardChannel(message):
    if message.author.permissions_in(message.channel).manage_guild:
        server_id = message.guild.id
        conn = await getConnection()
        try:
            channelData = await conn.fetchrow('SELECT channel, message FROM tbl_bump_leaderboard_posting WHERE server = $1', server_id)
            if channelData is None:
                await message.channel.send("No leaderboard postings recorded.")
            else:
                leaderboardChannel = message.guild.get_channel(channelData[0])
                try:
                    leaderboardMessage = await leaderboardChannel.fetch_message(channelData[1])
                    await leaderboardMessage.delete()
                except discord.errors.NotFound:
                    pass
                await conn.execute('DELETE FROM tbl_bump_leaderboard_posting WHERE server = $1', server_id)
                await message.channel.send("Leaderboard posting in " + leaderboardChannel.mention + " has been deleted.")
        finally:
            await returnConnection(conn)

async def updateBumpLeaderboardChannel(message, client):
    server_id = message.guild.id
    conn = await getConnection()
    try:
        messageData = await conn.fetchrow('SELECT channel, message FROM tbl_bump_leaderboard_posting WHERE server = $1', server_id)
        if messageData is not None:
            try:
                leaderboardMessage = await message.guild.get_channel(messageData[0]).fetch_message(messageData[1])
                leaderboardData = await conn.fetch('SELECT bumper, COUNT(response_id) FROM tbl_bumping_record WHERE server = $1 GROUP BY bumper ORDER BY COUNT(response_id) DESC', server_id)
                count = len(leaderboardData)
                leaderboardOutput = "**LEADERBOARD:**"
                rank = 0
                for i in range(count):
                    if i == 0 or leaderboardData[i - 1][1] != leaderboardData[i][1]:
                        rank = str(i + 1)
                    member = message.guild.get_member(leaderboardData[i][0])
                    if member is None:
                        member = client.get_user(leaderboardData[i][0])
                    if member is None:
                        memberName = "<@" + str(leaderboardData[i][0]) + ">"
                    else:
                        memberName = member.display_name
                    leaderboardOutput += "\n" + rank + ": " + memberName + " - " + str(leaderboardData[i][1]) + " bumps"
                await leaderboardMessage.edit(content=leaderboardOutput)
            except discord.errors.NotFound:
                await message.channel.send("Error encountered updating leaderboard posting. Post has likely been deleted.")
    finally:
        await returnConnection(conn)
