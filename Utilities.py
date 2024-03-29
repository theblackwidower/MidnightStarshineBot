# ------------------------------------------------------------------------------
#      MidnightStarshineBot - a multipurpose Discord bot
#      Copyright (C) 2020-2022  T. Duke Perry
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
import asyncpg
import math

import Constants

connPool = None

async def getConnection():
    global connPool
    if connPool is None:
        connPool = await asyncpg.create_pool(Constants.DATABASE_URL)
    return await connPool.acquire()

async def returnConnection(conn):
    await connPool.release(conn)

async def roleDeleted(role):
    conn = await getConnection()
    try:
        await deleteDbRole(conn, role, 'tbl_paid_roles')
        await deleteDbRole(conn, role, 'tbl_active_role_settings')
        await deleteDbRole(conn, role, 'tbl_promoter_role_settings')
        await deleteDbRole(conn, role, 'tbl_bumper_role_settings')
        await deleteDbRole(conn, role, 'tbl_controlled_roles')
        await deleteDbRole(conn, role, 'tbl_mute_roles')
        await deleteDbRole(conn, role, 'tbl_timeout_roles')
    finally:
        await returnConnection(conn)

async def deleteDbRole(conn, role, dbName):
    roleData = await conn.fetchrow('SELECT COUNT(server) FROM ' + dbName + ' WHERE server = $1 AND role = $2', role.guild.id, role.id)
    if roleData[0] > 0:
        await conn.execute('DELETE FROM ' + dbName + ' WHERE server = $1 AND role = $2', role.guild.id, role.id)

def parseRole(server, string):
    string = string.strip()
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
    string = string.strip()
    member = None
    if string.startswith("<@") and string.endswith(">"):
        memberId = string[2:len(string) - 1]
        if memberId.startswith("!"):
            memberId = memberId[1:]
        if memberId.isdigit():
            member = server.get_member(int(memberId))
    return member

def parseChannel(server, string):
    string = string.strip()
    member = None
    if string.startswith("<#") and string.endswith(">"):
        channelId = string[2:len(string) - 1]
        if channelId.isdigit():
            member = server.get_channel(int(channelId))
    return member

def parseTimeDelta(string):
    string = string.strip()
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
        raise Exception("Invalid number of totalTimeParts: " + str(len(totalTimeParts)))

    return totalTimeString

def getOrdinal(number):
    output = str(math.floor(number))
    digitCount = len(output)
    if digitCount > 1 and output[digitCount - 2] == "1":
        output += "th"
    elif output[digitCount - 1] == "1":
        output += "st"
    elif output[digitCount - 1] == "2":
        output += "nd"
    elif output[digitCount - 1] == "3":
        output += "rd"
    else:
        output += "th"

    return output
