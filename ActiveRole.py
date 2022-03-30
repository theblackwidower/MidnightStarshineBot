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

import datetime

from Constants import *
from Utilities import *

SETUP_ACTIVE_ROLE_COMMAND = "setupactiverole"
CLEAR_ACTIVE_ROLE_COMMAND = "clearactiverole"

activeRecordLast = dict()
activeRecordStart = dict()

def setupDataCache(server_id):
    if server_id not in activeRecordLast:
        activeRecordLast[server_id] = dict()
    if server_id not in activeRecordStart:
        activeRecordStart[server_id] = dict()

async def setupActive(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        parsing = commandArgs.rpartition(" ")
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
                conn = await getConnection()
                try:
                    serverData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_active_role_settings WHERE server = $1', message.guild.id)
                    if serverData[0] > 0:
                        await conn.execute('UPDATE tbl_active_role_settings SET role = $1, gap = $2, duration = $3, max = $4 WHERE server = $5', role.id, gap, duration, max, message.guild.id)
                        output = "Active user role successfully updated with the following parameters:\n"
                    else:
                        await conn.execute('INSERT INTO tbl_active_role_settings (server, role, gap, duration, max) VALUES ($1, $2, $3, $4, $5)', message.guild.id, role.id, gap, duration, max)
                        output = "Active user role successfully set up with the following parameters:\n"
                    output += "We'll be assigning the \"__" + role.name + "__\" role...\n"
                    output += "... to any user who sends at least one message every __" + timeDeltaToString(gap) + "__...\n"
                    output += "... for at least __" + timeDeltaToString(duration) + "__.\n"
                    output += "And we'll take the role away if they stop posting for __" + timeDeltaToString(max) + "__.\n"
                    await message.channel.send(output)
                finally:
                    await returnConnection(conn)

async def clearActive(message):
    if message.author.permissions_in(message.channel).manage_guild:
        conn = await getConnection()
        try:
            serverData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_active_role_settings WHERE server = $1', message.guild.id)
            if serverData[0] > 0:
                await conn.execute('DELETE FROM tbl_active_role_settings WHERE server = $1', message.guild.id)
                await message.channel.send("Active role feature completely cleared out. If you want to reenable it, please run `" + getPrefix(message.guild) + SETUP_ACTIVE_ROLE_COMMAND + "` again.")
            else:
                await message.channel.send("Active role feature has not even been set up, so there's no reason to clear it.")
        finally:
            await returnConnection(conn)

async def checkActive(message):
    if isinstance(message.author, discord.Member) and not message.author.bot:
        conn = await getConnection()
        try:
            serverData = await conn.fetchrow('SELECT role, gap, duration FROM tbl_active_role_settings WHERE server = $1', message.guild.id)
            if serverData is not None:
                role = message.guild.get_role(serverData[0])
                if role is None:
                    await conn.execute('DELETE FROM tbl_active_role_settings WHERE server = $1 AND role = $2', message.guild.id, serverData[0])
                else:
                    gap = serverData[1]
                    duration = serverData[2]
                    if message.guild.id not in activeRecordLast:
                        setupDataCache(message.guild.id)
                    if message.author.id in activeRecordLast[message.guild.id]:
                        lastMessageTime = activeRecordLast[message.guild.id][message.author.id]
                        if message.created_at <= lastMessageTime + gap:
                            startMessageTime = activeRecordStart[message.guild.id][message.author.id]
                            if message.created_at >= startMessageTime + duration:
                                recordData = await conn.fetchrow('SELECT COUNT(member) FROM tbl_activity_record WHERE server = $1 AND member = $2', message.guild.id, message.author.id)
                                if recordData[0] > 0:
                                    await conn.execute('UPDATE tbl_activity_record SET last_active = $1 WHERE server = $2 AND member = $3', message.created_at, message.guild.id, message.author.id)
                                else:
                                    await conn.execute('INSERT INTO tbl_activity_record (server, member, last_active) VALUES ($1, $2, $3)', message.guild.id, message.author.id, message.created_at)
                                if message.author.roles.count(message.author.guild.get_role(serverData[0])) == 0:
                                    await message.author.add_roles(role, reason="Been sending at least one message per " + timeDeltaToString(gap) + " for " + timeDeltaToString(duration) + ".")
                        else:
                            activeRecordStart[message.guild.id][message.author.id] = message.created_at
                    else:
                        activeRecordStart[message.guild.id][message.author.id] = message.created_at
                    activeRecordLast[message.guild.id][message.author.id] = message.created_at
        finally:
            await returnConnection(conn)

async def persistActive(member):
    if isinstance(member, discord.Member) and not member.bot:
        conn = await getConnection()
        try:
            serverData = await conn.fetchrow('SELECT role, max FROM tbl_active_role_settings WHERE server = $1', member.guild.id)
            if serverData is not None:
                role = member.guild.get_role(serverData[0])
                if role is None:
                    await conn.execute('DELETE FROM tbl_active_role_settings WHERE server = $1 AND role = $2', member.guild.id, serverData[0])
                else:
                    max = serverData[1]
                    threshold = datetime.datetime.utcnow() - max
                    recordData = await conn.fetchrow('SELECT last_active FROM tbl_activity_record WHERE server = $1 AND member = $2', member.guild.id, member.id)
                    if recordData is not None:
                        lastActive = recordData[0]
                    else:
                        lastActive = datetime.datetime.min
                    if member.roles.count(role) > 0:
                        if lastActive < threshold:
                            await member.remove_roles(role, reason="This user has failed to meet the 'active' criteria at any time in the past " + timeDeltaToString(max) + ".")
                    else:
                        if lastActive >= threshold:
                            await member.add_roles(role, reason="This user had their active role returned, since records show they met the active criteria at some point in the past " + timeDeltaToString(max) + ".")
        finally:
            await returnConnection(conn)
