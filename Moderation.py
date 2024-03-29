# ------------------------------------------------------------------------------
#      MidnightStarshineBot - a multipurpose Discord bot
#      Copyright (C) 2020  T. Duke Perry
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

from Constants import *
from Utilities import *

MOD_MUTE_ROLE_SETUP_COMMAND = "setupmuterole"
MOD_MUTE_COMMAND = "mute"
MOD_UNMUTE_COMMAND = "unmute"
MOD_TIMEOUT_SETUP_COMMAND = "setuptimeout"
MOD_TIMEOUT_ROLE_SETUP_COMMAND = "setuptimeoutrole"
MOD_TIMEOUT_COMMAND = "timeout"
MOD_TIMEIN_COMMAND = "return"
MOD_KICK_COMMAND = "kick"
MOD_BAN_SIMPLE_COMMAND = "ban"
MOD_BAN_DELETE_COMMAND = "spamban"

async def setupMuteRole(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        role = parseRole(message.guild, commandArgs)
        if role is None:
            await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
        else:
            conn = await getConnection()
            try:
                serverData = await conn.fetchrow('SELECT role FROM tbl_mute_roles WHERE server = $1', message.guild.id)
                if serverData is None:
                    await conn.execute('INSERT INTO tbl_mute_roles (server, role) VALUES ($1, $2)', message.guild.id, role.id)
                    output = "Mute role now set to " + role.mention
                else:
                    if serverData[0] == role.id:
                        output = "Reran setup of the mute role " + role.mention
                    else:
                        await conn.execute('UPDATE tbl_mute_roles SET role = $1 WHERE server = $2', role.id, message.guild.id)
                        output = "Mute role now updated to " + role.mention
            finally:
                await returnConnection(conn)
            reason="Setting up muted role."
            await allChannelMute(role, reason)
            await message.channel.send(output)

async def mute(message, commandArgs):
    if message.author.permissions_in(message.channel).kick_members:
        parsing = commandArgs.partition(" ")
        member = parseMember(message.guild, parsing[0])
        if member is None:
            await message.channel.send("Member not found.")
        elif member.guild_permissions.administrator:
            await message.channel.send("Cannot mute any user with full admin permissions.")
        else:
            conn = await getConnection()
            try:
                if parsing[2] == "":
                    muteData = await conn.fetchrow('SELECT channel FROM tbl_muted_members WHERE server = $1 AND member = $2 AND channel = 0', member.guild.id, member.id)
                    if muteData is None:
                        await conn.execute('INSERT INTO tbl_muted_members (server, member) VALUES ($1, $2)', message.guild.id, member.id)
                    reason = "Muting " + str(member) + " on " + str(message.author) + "'s order."
                    roleData = await conn.fetchrow('SELECT role FROM tbl_mute_roles WHERE server = $1', member.guild.id)
                    await returnConnection(conn)
                    if roleData is not None:
                        role = member.guild.get_role(roleData[0])
                        if role is not None:
                            await member.add_roles(role, reason=reason)
                    await allChannelMute(member, reason)
                    await message.channel.send("Member " + member.mention + " muted.")
                else:
                    channel = parseChannel(message.guild, parsing[2])
                    if channel is None:
                        await message.channel.send("Could not find specified channel.")
                    else:
                        muteData = await conn.fetchrow('SELECT channel FROM tbl_muted_members WHERE server = $1 AND member = $2 AND channel = $3', member.guild.id, member.id, channel.id)
                        if muteData is None:
                            await conn.execute('INSERT INTO tbl_muted_members (server, member, channel) VALUES ($1, $2, $3)', message.guild.id, member.id, channel.id)
                        reason = "Muting " + str(member) + " in " + str(channel) + " on " + str(message.author) + "'s order."
                        await channelMute(channel, member, reason)
                        await message.channel.send("Member " + member.mention + " muted in " + str(channel) + ".")
            finally:
                await returnConnection(conn)

async def allChannelMute(subject, reason):
    for category, channelList in subject.guild.by_category():
        if category is not None:
            await channelMute(category, subject, reason)
        for channel in channelList:
            await channelMute(channel, subject, reason)

async def channelMute(channel, subject, reason):
    if isinstance(subject, discord.Role):
        permissions = discord.Permissions.all_channel()
    else:
        permissions = channel.permissions_for(subject)
    if permissions.send_messages or permissions.add_reactions or permissions.speak:
        botPermissions = channel.permissions_for(channel.guild.me)
        if botPermissions.read_messages:
            overwrite = channel.overwrites_for(subject)
            if botPermissions.send_messages:
                overwrite.update(send_messages=False)
            if botPermissions.add_reactions:
                overwrite.update(add_reactions=False)
            if botPermissions.speak:
                overwrite.update(speak=False)

            await channel.set_permissions(subject, overwrite=overwrite, reason=reason)

async def unmute(message, commandArgs):
    if message.author.permissions_in(message.channel).kick_members:
        parsing = commandArgs.partition(" ")
        member = parseMember(message.guild, parsing[0])
        if member is None:
            await message.channel.send("Member not found.")
        else:
            conn = await getConnection()
            try:
                if parsing[2] == "":
                    await conn.execute('DELETE FROM tbl_muted_members WHERE server = $1 AND member = $2', message.guild.id, member.id)
                    reason = "Unmuting " + str(member) + " on " + str(message.author) + "'s order."
                    roleData = await conn.fetchrow('SELECT role FROM tbl_mute_roles WHERE server = $1', member.guild.id)
                    await returnConnection(conn)
                    if roleData is not None:
                        role = member.guild.get_role(roleData[0])
                        if role is not None:
                            await member.remove_roles(role, reason=reason)
                    for category, channelList in message.guild.by_category():
                        if category is not None:
                            await channelUnmute(category, member, reason)
                        for channel in channelList:
                            await channelUnmute(channel, member, reason)
                    await message.channel.send("Member " + member.mention + " unmuted.")
                else:
                    channel = parseChannel(message.guild, parsing[2])
                    if channel is None:
                        await message.channel.send("Could not find specified channel.")
                    else:
                        await conn.execute('DELETE FROM tbl_muted_members WHERE server = $1 AND member = $2 AND channel = $3', message.guild.id, member.id, channel.id)
                        reason = "Unmuting " + str(member) + " in " + str(channel) + " on " + str(message.author) + "'s order."
                        await channelUnmute(channel, member, reason)
                        await message.channel.send("Member " + member.mention + " unmuted in " + str(channel) + ".")
            finally:
                await returnConnection(conn)

async def channelUnmute(channel, member, reason):
    permissions = channel.overwrites_for(member)
    if permissions is not None and (permissions.send_messages == False or permissions.add_reactions == False or permissions.speak == False):
        permissions.update(send_messages=None, add_reactions=None, speak=None)
        if permissions.is_empty():
            await channel.set_permissions(member, overwrite=None, reason=reason)
        else:
            await channel.set_permissions(member, overwrite=permissions, reason=reason)

async def persistMute(member):
    conn = await getConnection()
    try:
        muteData = await conn.fetch('SELECT channel FROM tbl_muted_members WHERE server = $1 AND member = $2', member.guild.id, member.id)
        if len(muteData) > 0:
            reason = "Remuting " + str(member) + " based on persistance record."
            for row in muteData:
                if row[0] == 0:
                    roleData = await conn.fetchrow('SELECT role FROM tbl_mute_roles WHERE server = $1', member.guild.id)
                    if roleData is not None:
                        role = member.guild.get_role(roleData[0])
                        if role is not None:
                            await member.add_roles(role, reason=reason)
                    await allChannelMute(member, reason)
                else:
                    channel = member.guild.get_channel(row[0])
                    await channelMute(channel, member, reason)
    finally:
        await returnConnection(conn)

async def setupTimeout(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        channel = parseChannel(message.guild, commandArgs)
        if channel is None:
            await message.channel.send("Could not find specified channel.")
        else:
            conn = await getConnection()
            try:
                oldChannelData = await conn.fetchrow('SELECT channel FROM tbl_timeout_channel WHERE server = $1', message.guild.id)
                roleData = await conn.fetchrow('SELECT role FROM tbl_timeout_roles WHERE server = $1', message.guild.id)
                if oldChannelData is not None:
                    await conn.execute('UPDATE tbl_timeout_channel SET channel = $1 WHERE server = $2', channel.id, message.guild.id)
                    output = "Timeout command now updated to send people to " + channel.mention
                else:
                    await conn.execute('INSERT INTO tbl_timeout_channel (server, channel) VALUES ($1, $2)', message.guild.id, channel.id)
                    output = "Timeout command now setup to send people to " + channel.mention
                if roleData is not None:
                    timeoutRole = message.guild.get_role(roleData[0])
                    if timeoutRole is not None:
                        reason = "Updating timeout channel."
                        if oldChannelData is not None:
                            oldChannel = message.guild.get_channel(oldChannelData[0])
                            if oldChannel is not None:
                                await channelBanishForTimeout(oldChannel, timeoutRole, reason)
                        await channelOpenForTimeout(channel, timeoutRole, reason)
                await message.channel.send(output)
            finally:
                await returnConnection(conn)

async def setupTimeoutRole(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        role = parseRole(message.guild, commandArgs)
        if role is None:
            await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
        else:
            conn = await getConnection()
            try:
                channelData = await conn.fetchrow('SELECT channel FROM tbl_timeout_channel WHERE server = $1', message.guild.id)
                if channelData is None:
                    await message.channel.send("Please set up the timeout channel using the `" + getPrefix(message.guild) + MOD_TIMEOUT_SETUP_COMMAND + "` command before setting up the role.")
                else:
                    timeoutChannel = message.guild.get_channel(channelData[0])
                    if timeoutChannel is None:
                        await message.channel.send("Cannot find the designated timeout channel. Was it deleted somehow?")
                    else:
                        serverData = await conn.fetchrow('SELECT role FROM tbl_timeout_roles WHERE server = $1', message.guild.id)
                        if serverData is None:
                            await conn.execute('INSERT INTO tbl_timeout_roles (server, role) VALUES ($1, $2)', message.guild.id, role.id)
                            output = "Timeout role now set to " + role.mention
                        else:
                            if serverData[0] == role.id:
                                output = "Reran setup of the timeout role " + role.mention
                            else:
                                await conn.execute('UPDATE tbl_timeout_roles SET role = $1 WHERE server = $2', role.id, message.guild.id)
                                output = "Timeout role now updated to " + role.mention
                        await returnConnection(conn)
                        reason="Setting up timeout role."
                        await allChannelTimeout(role, reason, timeoutChannel)
                        await message.channel.send(output)
            finally:
                await returnConnection(conn)

async def timeout(message, commandArgs):
    if message.author.permissions_in(message.channel).kick_members:
        conn = await getConnection()
        try:
            channelData = await conn.fetchrow('SELECT channel FROM tbl_timeout_channel WHERE server = $1', message.guild.id)
            if channelData is not None:
                member = parseMember(message.guild, commandArgs)
                timeoutChannel = message.guild.get_channel(channelData[0])
                if timeoutChannel is None:
                    await message.channel.send("Cannot find the designated timeout channel. Was it deleted somehow?")
                elif member is None:
                    await message.channel.send("Member not found.")
                elif member.guild_permissions.administrator:
                    await message.channel.send("Cannot timeout any user with full admin permissions.")
                else:
                    timeoutData = await conn.fetchrow('SELECT COUNT(member) FROM tbl_timedout_members WHERE server = $1 AND member = $2', member.guild.id, member.id)
                    if timeoutData[0] == 0:
                        await conn.execute('INSERT INTO tbl_timedout_members (server, member) VALUES ($1, $2)', message.guild.id, member.id)
                    reason = "Sending " + str(member) + " to a timeout on " + str(message.author) + "'s order."
                    roleData = await conn.fetchrow('SELECT role FROM tbl_timeout_roles WHERE server = $1', member.guild.id)
                    await returnConnection(conn)
                    if roleData is not None:
                        role = member.guild.get_role(roleData[0])
                        if role is not None:
                            await member.add_roles(role, reason=reason)
                    await allChannelTimeout(member, reason, timeoutChannel)
                    await message.channel.send("Member " + member.mention + " sent to a timeout.")
        finally:
            await returnConnection(conn)

async def allChannelTimeout(subject, reason, timeoutChannel):
    for category, channelList in subject.guild.by_category():
        if category == timeoutChannel:
            if category is not None:
                await channelOpenForTimeout(category, subject, reason)
            for channel in channelList:
                await channelOpenForTimeout(channel, subject, reason)
        else:
            if category is not None:
                await channelBanishForTimeout(category, subject, reason)
            for channel in channelList:
                if channel == timeoutChannel:
                    await channelOpenForTimeout(channel, subject, reason)
                else:
                    await channelBanishForTimeout(channel, subject, reason)

async def channelBanishForTimeout(channel, subject, reason):
    if isinstance(subject, discord.Role):
        permissions = discord.Permissions.all_channel()
    else:
        permissions = channel.permissions_for(subject)
    if permissions.read_messages:
        botPermissions = channel.permissions_for(channel.guild.me)
        if botPermissions.read_messages:
            overwrite = channel.overwrites_for(subject)
            overwrite.update(read_messages=False)

            await channel.set_permissions(subject, overwrite=overwrite, reason=reason)

async def channelOpenForTimeout(channel, subject, reason):
    if isinstance(subject, discord.Role):
        permissions = discord.Permissions.none()
    else:
        permissions = channel.permissions_for(subject)
    if not permissions.read_messages or not permissions.send_messages:
        botPermissions = channel.permissions_for(channel.guild.me)
        if botPermissions.read_messages:
            overwrite = channel.overwrites_for(subject)
            overwrite.update(read_messages=True)
            if botPermissions.send_messages:
                overwrite.update(send_messages=True)

            await channel.set_permissions(subject, overwrite=overwrite, reason=reason)

async def timein(message, commandArgs):
    if message.author.permissions_in(message.channel).kick_members:
        conn = await getConnection()
        try:
            channelData = await conn.fetchrow('SELECT channel FROM tbl_timeout_channel WHERE server = $1', message.guild.id)
            if channelData is not None:
                member = parseMember(message.guild, commandArgs)
                timeoutChannel = message.guild.get_channel(channelData[0])
                if member is None:
                    await message.channel.send("Member not found.")
                else:
                    await conn.execute('DELETE FROM tbl_timedout_members WHERE server = $1 AND member = $2', message.guild.id, member.id)
                    reason = "Removing " + str(member) + " from a timeout on " + str(message.author) + "'s order."
                    roleData = await conn.fetchrow('SELECT role FROM tbl_timeout_roles WHERE server = $1', member.guild.id)
                    await returnConnection(conn)
                    if roleData is not None:
                        role = member.guild.get_role(roleData[0])
                        if role is not None:
                            await member.remove_roles(role, reason=reason)
                    for category, channelList in message.guild.by_category():
                        if category == timeoutChannel:
                            if category is not None:
                                await channelCloseForTimein(category, member, reason)
                            for channel in channelList:
                                await channelCloseForTimein(channel, member, reason)
                        else:
                            if category is not None:
                                await channelReturnForTimein(category, member, reason)
                            for channel in channelList:
                                if channel == timeoutChannel:
                                    await channelCloseForTimein(channel, member, reason)
                                else:
                                    await channelReturnForTimein(channel, member, reason)
                    await message.channel.send("Member " + member.mention + " returned from a timeout.")
        finally:
            await returnConnection(conn)

async def channelReturnForTimein(channel, member, reason):
    permissions = channel.overwrites_for(member)
    if permissions is not None and permissions.read_messages == False:
        permissions.update(read_messages=None)
        if permissions.is_empty():
            await channel.set_permissions(member, overwrite=None, reason=reason)
        else:
            await channel.set_permissions(member, overwrite=permissions, reason=reason)

async def channelCloseForTimein(channel, member, reason):
    permissions = channel.overwrites_for(member)
    if permissions is not None and (permissions.read_messages == True or permissions.send_messages == True):
        permissions.update(read_messages=None, send_messages=None)
        if permissions.is_empty():
            await channel.set_permissions(member, overwrite=None, reason=reason)
        else:
            await channel.set_permissions(member, overwrite=permissions, reason=reason)

async def persistTimeout(member):
    conn = await getConnection()
    try:
        timeoutData = await conn.fetchrow('SELECT COUNT(member) FROM tbl_timedout_members WHERE server = $1 AND member = $2', member.guild.id, member.id)
        if timeoutData[0] > 0:
            channelData = await conn.fetchrow('SELECT channel FROM tbl_timeout_channel WHERE server = $1', member.guild.id)
            if channelData is not None:
                timeoutChannel = member.guild.get_channel(channelData[0])
                if timeoutChannel is not None:
                    reason = "Returning " + str(member) + " to timeout based on persistance record."
                    roleData = await conn.fetchrow('SELECT role FROM tbl_timeout_roles WHERE server = $1', member.guild.id)
                    await returnConnection(conn)
                    if roleData is not None:
                        role = member.guild.get_role(roleData[0])
                        if role is not None:
                            await member.add_roles(role, reason=reason)
                    await allChannelTimeout(member, reason, timeoutChannel)
    finally:
        await returnConnection(conn)

async def setupChannelModRoles(channel):
    conn = await getConnection()
    try:
        timeoutChannelData = await conn.fetchrow('SELECT channel FROM tbl_timeout_channel WHERE server = $1', channel.guild.id)
        muteData = await conn.fetchrow('SELECT role FROM tbl_mute_roles WHERE server = $1', channel.guild.id)
        timeoutData = await conn.fetchrow('SELECT role FROM tbl_timeout_roles WHERE server = $1', channel.guild.id)
    finally:
        await returnConnection(conn)
    if muteData is not None or timeoutData is not None:
        muteRole = None
        timeoutRole = None
        if muteData is not None:
            muteRole = channel.guild.get_role(muteData[0])
        if timeoutData is not None:
            timeoutRole = channel.guild.get_role(timeoutData[0])

        reason = "Setting up new channel for the "
        if muteRole is not None and timeoutRole is not None:
            reason += "Mute and Timeout functions."
        elif muteRole is not None:
            reason += "Mute function."
        elif timeoutRole is not None:
            reason += "Timeout function."

        if muteRole is not None:
            await channelMute(channel, muteRole, reason)
        if timeoutRole is not None:
            if channel.id == timeoutChannelData[0]:
                await channelOpenForTimeout(channel, timeoutRole, reason)
            else:
                await channelBanishForTimeout(channel, timeoutRole, reason)

async def kick(message, commandArgs):
    if message.author.permissions_in(message.channel).kick_members:
        parsing = commandArgs.partition(" ")
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

async def ban(message, commandArgs):
    if message.author.permissions_in(message.channel).ban_members:
        parsing = commandArgs.partition(" ")
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

async def banDelete(message, commandArgs):
    if message.author.permissions_in(message.channel).ban_members and message.author.permissions_in(message.channel).manage_messages:
        parsing = commandArgs.partition(" ")
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
