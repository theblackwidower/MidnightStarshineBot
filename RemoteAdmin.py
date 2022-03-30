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

import discord

from Constants import *
from Utilities import *

REMOTE_ADMIN_SERVER_LIST_COMMAND = "listservers"
REMOTE_ADMIN_SERVER_REMOVE_COMMAND = "pullserver"
REMOTE_ADMIN_CHANNEL_LIST_COMMAND = "listchannels"
REMOTE_ADMIN_GET_PERMS_COMMAND = "getperms"

async def listServers(message, client):
    if message.author.id == MIDNIGHTS_TRUE_MASTER:
        output = "Currently attached to the following servers:"
        for server in client.guilds:
            output += "\n" + server.name + " (id: " + str(server.id) + ")"
        await message.channel.send(output)

async def leaveServer(message, commandArgs, client):
    if message.author.id == MIDNIGHTS_TRUE_MASTER:
        if commandArgs.isdigit():
            server = discord.utils.get(client.guilds, id=int(commandArgs))
        else:
            server = discord.utils.get(client.guilds, name=commandArgs)

        if server is None:
            await message.channel.send("Can't find that server. Don't think I'm actually on it, if it exists at all.")
        else:
            await server.leave()

async def reportServerJoin(server, client):
    master = client.get_user(MIDNIGHTS_TRUE_MASTER)
    await master.create_dm()
    await master.dm_channel.send("Joined a new server: " + server.name + " (id: " + str(server.id) + ")")

async def reportServerLeave(server, client):
    master = client.get_user(MIDNIGHTS_TRUE_MASTER)
    await master.create_dm()
    await master.dm_channel.send("Left server: " + server.name + " (id: " + str(server.id) + ")")

async def listServerChannels(message, commandArgs, client):
    if message.author.id == MIDNIGHTS_TRUE_MASTER:
        if commandArgs.isdigit():
            server = discord.utils.get(client.guilds, id=int(commandArgs))
        else:
            server = discord.utils.get(client.guilds, name=commandArgs)

        if server is None:
            await message.channel.send("Can't find that server. Don't think I'm actually on it, if it exists at all.")
        else:
            categoryList = server.by_category()
            output = "Channel list for " + server.name + " (id: " + str(server.id) + "):"
            for category, channelList in categoryList:
                if category is not None:
                    output += "\n    +" + category.name + " (id: " + str(category.id) + ")"
                for channel in channelList:
                    output += "\n    "
                    if category is not None:
                        output += "    "
                    if isinstance(channel, discord.TextChannel):
                        output += "#"
                    elif isinstance(channel, discord.VoiceChannel):
                        output += "🔊"
                    else:
                        output += "?"
                    output += channel.name + " (id: " + str(channel.id) + ")"

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

async def getPerms(message, commandArgs, client):
    if message.author.id == MIDNIGHTS_TRUE_MASTER:
        if commandArgs.isdigit():
            subject = discord.utils.get(client.guilds, id=int(commandArgs))
            if subject is None:
                subject = await client.fetch_channel(int(commandArgs))
        else:
            subject = discord.utils.get(client.guilds, name=commandArgs)
            if subject is None:
                channels = []
                for server in client.guilds:
                    oneChannel = discord.utils.get(server.channels, name=commandArgs)
                    if oneChannel is not None:
                        channels.append(oneChannel)
                if len(channels) == 1:
                    subject = channels[0]
                elif len(channels) > 1:
                    subject = channels

        if subject is None:
            await message.channel.send("Can't find any server or channel with that ID or name. Don't think I actually have access to it, if it exists at all.")
        elif isinstance(subject, list):
            output = "Found " + str(len(subject)) + " channels that fit the criteria:"
            for channel in subject:
                output += "\n    "
                if isinstance(channel, discord.CategoryChannel):
                    output += "+"
                elif isinstance(channel, discord.TextChannel):
                    output += "#"
                elif isinstance(channel, discord.VoiceChannel):
                    output += "🔊"
                else:
                    output += "?"
                output += channel.name + " (id: " + str(channel.id) + ") in " + channel.guild.name
            output += "\nPlease try again, specifying the channel ID."
            await message.channel.send(output)
        else:
            if isinstance(subject, discord.Guild):
                output = "Global permissions I currently hold in " + subject.name + " (id: " + str(subject.id) + "):"
                perms = subject.me.guild_permissions
            elif isinstance(subject, discord.abc.GuildChannel):
                output = "Channel permissions I currently hold in the " + subject.name + " "
                if isinstance(subject, discord.CategoryChannel):
                    output += "Category"
                elif isinstance(subject, discord.TextChannel):
                    output += "Text Channel"
                elif isinstance(subject, discord.VoiceChannel):
                    output += "Voice Channel"
                else:
                    output += "Unknown Channel Type"
                output += " (id: " + str(subject.id) + ") from " + subject.guild.name + ":"
                perms = subject.guild.me.permissions_in(message.channel)

            for permission, value in iter(perms):
                if value:
                    output += "\n" + str(permission)
            await message.channel.send(output)
