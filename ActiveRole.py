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

from Constants import *
from Utilities import *

SETUP_ACTIVE_ROLE_COMMAND = "setupactiverole"
CLEAR_ACTIVE_ROLE_COMMAND = "clearactiverole"

activeRecordLast = dict()
activeRecordStart = dict()
activeCheckTime = dict()

ACTIVE_CHECK_WAIT = datetime.timedelta(hours=1)

def setupDataCache(server_id):
    if server_id not in activeRecordLast:
        activeRecordLast[server_id] = dict()
    if server_id not in activeRecordStart:
        activeRecordStart[server_id] = dict()
    if server_id not in activeCheckTime:
        activeCheckTime[server_id] = dict()

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
                serverData = c.fetchone()
                if serverData[0] > 0:
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
        serverData = c.fetchone()
        if serverData[0] > 0:
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
        serverData = c.fetchone()
        if serverData is not None:
            role = message.guild.get_role(serverData[0])
            gap = datetime.timedelta(seconds=serverData[1])
            duration = datetime.timedelta(seconds=serverData[2])
            if message.guild.id not in activeRecordLast:
                setupDataCache(message.guild.id)
            if message.author.id in activeRecordLast[message.guild.id]:
                lastMessageTime = activeRecordLast[message.guild.id][message.author.id]
                if message.created_at <= lastMessageTime + gap:
                    startMessageTime = activeRecordStart[message.guild.id][message.author.id]
                    if message.created_at >= startMessageTime + duration:
                        if message.author.roles.count(message.author.guild.get_role(serverData[0])) == 0:
                            await message.author.add_roles(role, reason="Been sending at least one message per " + timeDeltaToString(gap) + " for " + timeDeltaToString(duration) + ".")
                        c.execute('SELECT COUNT(member) FROM tbl_activity_record WHERE server = %s AND member = %s', (message.guild.id, message.author.id))
                        recordData = c.fetchone()
                        if recordData[0] > 0:
                            c.execute('UPDATE tbl_activity_record SET last_active = %s WHERE server = %s AND member = %s', (message.created_at.timestamp(), message.guild.id, message.author.id))
                        else:
                            c.execute('INSERT INTO tbl_activity_record (server, member, last_active) VALUES (%s, %s, %s)', (message.guild.id, message.author.id, message.created_at.timestamp()))
                        conn.commit()
                else:
                    activeRecordStart[message.guild.id][message.author.id] = message.created_at
            else:
                activeRecordStart[message.guild.id][message.author.id] = message.created_at
            activeRecordLast[message.guild.id][message.author.id] = message.created_at
        conn.close()

async def purgeActiveServer(server):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT role FROM tbl_active_role_settings WHERE server = %s', (server.id,))
    roleData = c.fetchone()
    conn.close()
    if roleData is not None:
        activeRole = server.get_role(roleData[0])
        for member in activeRole.members:
            await purgeActiveMember(member)

async def purgeActiveMember(member):
    if member.guild.id not in activeCheckTime:
        setupDataCache(member.guild.id)
    if member.id in activeCheckTime[member.guild.id]:
        lastCheck = activeCheckTime[member.guild.id][member.id]
    else:
        lastCheck = None

    if isinstance(member, discord.Member) and not member.bot and (lastCheck is None or lastCheck + ACTIVE_CHECK_WAIT < datetime.datetime.now()):
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT role, max FROM tbl_active_role_settings WHERE server = %s', (member.guild.id,))
        serverData = c.fetchone()
        if serverData is not None:
            role = member.guild.get_role(serverData[0])
            max = datetime.timedelta(seconds=serverData[1])
            if member.roles.count(role) > 0:
                threshold = datetime.datetime.now() - max
                c.execute('SELECT last_active FROM tbl_activity_record WHERE server = %s AND member = %s', (member.guild.id, member.id))
                recordData = c.fetchone()
                if recordData is not None and datetime.datetime.fromtimestamp(recordData[0]) < threshold:
                    await member.remove_roles(role, reason="This user has failed to meet the 'active' criteria at any time in the past " + timeDeltaToString(max) + ".")
                else:
                    activeCheckTime[member.guild.id][member.id] = datetime.datetime.now()
        conn.close()

async def persistActive(member):
    if isinstance(member, discord.Member) and not member.bot:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT role, max FROM tbl_active_role_settings WHERE server = %s', (member.guild.id,))
        serverData = c.fetchone()
        if serverData is not None:
            role = member.guild.get_role(serverData[0])
            max = datetime.timedelta(seconds=serverData[1])
            if member.roles.count(role) <= 0:
                threshold = datetime.datetime.now() - max
                c.execute('SELECT last_active FROM tbl_activity_record WHERE server = %s AND member = %s', (member.guild.id, member.id))
                recordData = c.fetchone()
                if recordData is not None and datetime.datetime.fromtimestamp(recordData[0]) >= threshold:
                    await member.remove_roles(role, reason="This user had their active role returned, since records show they met the active criteria at some point in the past " + timeDeltaToString(max) + ".")
        conn.close()
