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

from Constants import *
from Utilities import *

MOD_MUTE_COMMAND = "mute"
MOD_UNMUTE_COMMAND = "unmute"
MOD_KICK_COMMAND = "kick"
MOD_BAN_SIMPLE_COMMAND = "ban"
MOD_BAN_DELETE_COMMAND = "spamban"

async def mute(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + MOD_MUTE_COMMAND and message.author.permissions_in(message.channel).kick_members:
        parsing = parsing[2].partition(" ")
        member = parseMember(message.guild, parsing[0])
        if member is None:
            await message.channel.send("Member not found.")
        elif member.guild_permissions.administrator:
            await message.channel.send("Cannot mute any user with full admin permissions.")
        else:
            if parsing[2] == "":
                reason = "Muting " + str(member) + " on " + str(message.author) + "'s order."
                for category, channelList in message.guild.by_category():
                    if category is not None:
                        await channelMute(category, member, reason)
                    for channel in channelList:
                        await channelMute(channel, member, reason)
                await message.channel.send("Member " + member.mention + " muted.")
            else:
                channel = parseChannel(message.guild, parsing[2])
                if channel is None:
                    await message.channel.send("Could not find specified channel.")
                else:
                    reason = "Muting " + str(member) + " in " + str(channel) + " on " + str(message.author) + "'s order."
                    await channelMute(channel, member, reason)
                    await message.channel.send("Member " + member.mention + " muted in " + str(channel) + ".")

async def channelMute(channel, member, reason):
    permissions = channel.permissions_for(member)
    if permissions.send_messages or permissions.add_reactions or permissions.speak:
        await channel.set_permissions(member, send_messages=False, add_reactions=False, speak=False, reason=reason)

async def unmute(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + MOD_UNMUTE_COMMAND and message.author.permissions_in(message.channel).kick_members:
        parsing = parsing[2].partition(" ")
        member = parseMember(message.guild, parsing[0])
        if member is None:
            await message.channel.send("Member not found.")
        else:
            if parsing[2] == "":
                reason = "Unmuting " + str(member) + " on " + str(message.author) + "'s order."
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
                    reason = "Unmuting " + str(member) + " in " + str(channel) + " on " + str(message.author) + "'s order."
                    await channelUnmute(channel, member, reason)
                    await message.channel.send("Member " + member.mention + " unmuted in " + str(channel) + ".")

async def channelUnmute(channel, member, reason):
    permissions = channel.overwrites_for(member)
    if permissions is not None and (permissions.send_messages == False or permissions.add_reactions == False or permissions.speak == False):
        permissions.update(send_messages=None, add_reactions=None, speak=None)
        if permissions.is_empty():
            await channel.set_permissions(member, overwrite=None, reason=reason)
        else:
            await channel.set_permissions(member, overwrite=permissions, reason=reason)

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
