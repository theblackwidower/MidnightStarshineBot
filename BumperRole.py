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

from Constants import *
from Utilities import *

SETUP_BUMPER_ROLE_COMMAND = "setupbumperrole"
CLEAR_BUMPER_ROLE_COMMAND = "clearbumperrole"
SCAN_BUMP_CHANNEL_COMMAND = "scanforbumps"

DISBOARD_BOT_ID = 302050872383242240
SUCCESSFUL_DISBOARD_BUMP_MESSAGE = "Bump done :thumbsup:"

async def setupBumperRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + SETUP_BUMPER_ROLE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        parsing = parsing[2].rpartition(" ")
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
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + CLEAR_BUMPER_ROLE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        conn = await getConnection()
        try:
            serverData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_bumper_role_settings WHERE server = $1', message.guild.id)
            if serverData[0] > 0:
                await conn.execute('DELETE FROM tbl_bumper_role_settings WHERE server = $1', message.guild.id)
                del invitesCache[message.guild.id]
                await message.channel.send("Bumper role feature completely cleared out. If you want to reenable it, please run `" + COMMAND_PREFIX + SETUP_BUMPER_ROLE_COMMAND + "` again.")
            else:
                await message.channel.send("Bumper role feature has not even been set up, so there's no reason to clear it.")
        finally:
            await returnConnection(conn)

async def scanForBumps(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + SCAN_BUMP_CHANNEL_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        channel = parseChannel(message.guild, parsing[2])
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

async def recordBump(message):
    if message.author.id == DISBOARD_BOT_ID:
        conn = await getConnection()
        try:
            serverData = await conn.fetch('SELECT role, bump_count FROM tbl_bumper_role_settings WHERE server = $1', message.guild.id)
            if len(serverData) > 0:
                bumper = getBumper(message)
                if bumper is not None:
                    await conn.execute('INSERT INTO tbl_bumping_record (server, bumper, response_id, timebumped) VALUES ($1, $2, $3, $4)', message.guild.id, bumper.id, message.id, message.created_at)
                    for row in serverData:
                        role = message.guild.get_role(row[0])
                        bumpCount = row[1]
                        if bumper.roles.count(role) == 0:
                            countData = await conn.fetchrow('SELECT COUNT(timebumped) FROM tbl_bumping_record WHERE server = $1 AND bumper = $2', message.guild.id, bumper.id)
                            if countData[0] >= bumpCount:
                                await bumper.add_roles(role, reason="Successfully bumped the server a total of " + str(countData[0]) + " times.")
                            else:
                                break
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
                    minBumpCount = row[1]
                    if member.roles.count(role) > 0:
                        if bumpCount < minBumpCount:
                            await member.remove_roles(role, reason="This user does not qualify for the bumper role, as they have only bumped " + str(bumpCount) + " times out of the " + str(minBumpCount) + " they need.")
                    else:
                        if bumpCount >= minBumpCount:
                            await member.add_roles(role, reason="This user had their bumper role returned, since records show they bumped " + str(bumpCount) + " times, and they only need " + str(minBumpCount) + " to qualify.")
        finally:
            await returnConnection(conn)
