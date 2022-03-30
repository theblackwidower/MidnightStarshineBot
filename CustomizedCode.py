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

import re
import os

from Constants import *
from Utilities import *

ELEMENT_FINDER = re.compile("^element of .*", flags=re.IGNORECASE)

async def ponyVersePersistElementRole(member):
    if member.guild.id == 682755852238848037 or member.guild.id == 700056528379707515:
        isMatch = ELEMENT_FINDER.fullmatch(member.display_name) is not None
        if member.guild.id == 682755852238848037:
            role = member.guild.get_role(683401036974915645)
        elif member.guild.id == 700056528379707515:
            role = member.guild.get_role(700056528711057489)
        if role is not None:
            if member.roles.count(role) > 0:
                if not isMatch:
                    await member.remove_roles(role, reason="They're not an element.")
            else:
                if isMatch:
                    await member.add_roles(role, reason="They're now an element.")

CALL = "Sunshine, sunshine, ladybugs awake..."
RESPONSE_IDENTIFIER = re.compile("^clap\s+your\s+hooves\s+and\s+do\s+a\s+little\s+shake.?", flags=re.IGNORECASE)
VERIFICATION_QUEUE_FILE = "VerificationQueue.txt"

verificationQueue = []

if os.path.isfile(VERIFICATION_QUEUE_FILE):
    with open(VERIFICATION_QUEUE_FILE, "r", encoding='utf-8') as file:
        verificationQueue = file.readlines()

async def stormyVerificationCall(member):
    if member.guild.id == 549660245618720770:
        await member.create_dm()
        DMChannel = member.dm_channel
        await DMChannel.send(CALL)
        verificationQueue.append(member.id)
        with open(VERIFICATION_QUEUE_FILE, "a+", encoding='utf-8') as file:
            file.write(str(member.id) + "\n")


async def stormyVerificationResponse(message, client):
    if isinstance(message.channel, discord.DMChannel) and message.author.id in verificationQueue:
        if RESPONSE_IDENTIFIER.fullmatch(message.content) is not None:
            server = discord.utils.get(client.guilds, id=549660245618720770)
            member = server.get_member(message.author.id)
            if member is not None:
                role = server.get_role(704794251392843817)
                await member.add_roles(role, reason="They have been verified.")
                await message.channel.send("Welcome to " + server.name)
                verificationQueue.remove(message.author.id)
                with open(VERIFICATION_QUEUE_FILE, 'r+', encoding='utf-8') as file:
                    file.truncate()
                    for id in verificationQueue:
                        file.write(str(id) + "\n")
        else:
            await message.channel.send("No dice. Please try again...")
            await message.channel.send(CALL)
