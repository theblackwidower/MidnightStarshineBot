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
import os

from Constants import *
from Utilities import *

AMBIENCE_DIRECTORY = "Ambience"
AMBIENCE_FILE_EXT = "opus"

START_AMBIENCE_COMMAND = "startambience"
STOP_AMBIENCE_COMMAND = "stopambience"
LIST_AMBIENCE_COMMAND = "listambience"

connectionCache = dict()
ambienceList = []

if os.path.exists(AMBIENCE_DIRECTORY):
    for root, dirs, files in os.walk(AMBIENCE_DIRECTORY):
        for filename in files:
            if filename.endswith("." + AMBIENCE_FILE_EXT):
                ambienceList.append(filename[:-len(AMBIENCE_FILE_EXT) - 1])

async def listAmbience(message):
    if len(ambienceList) > 0:
        list = ""
        for track in ambienceList:
            list += track + "\n"
        await message.channel.send("Here's a list of all available ambience tracks:\n```\n" + list + "```")

async def startAmbience(message, commandArgs):
    if len(ambienceList) > 0:
        voiceState = message.author.voice
        if voiceState is None:
            await message.channel.send("You need to be connected to a voice channel.")
        else:
            if message.guild.id in connectionCache:
                await message.channel.send("Already connected to a voice channel.")
            elif commandArgs not in ambienceList:
                await message.channel.send("Cannot find specified track. Try running `" + COMMAND_PREFIX + LIST_AMBIENCE_COMMAND + "`.")
            else:
                vc = await voiceState.channel.connect()
                try:
                    def loopAudio(error):
                        if error is None and vc.is_connected():
                            vc.play(discord.FFmpegOpusAudio(AMBIENCE_DIRECTORY + "/" + commandArgs + "." + AMBIENCE_FILE_EXT), after=loopAudio)
                    vc.play(discord.FFmpegOpusAudio(AMBIENCE_DIRECTORY + "/" + commandArgs + "." + AMBIENCE_FILE_EXT), after=loopAudio)
                except:
                    await vc.disconnect()
                    raise
                else:
                    connectionCache[message.guild.id] = vc
                    await message.channel.send("Playing `" + commandArgs + "`")

async def stopAmbience(message):
    if len(ambienceList) > 0:
        if message.guild.id not in connectionCache:
            await message.channel.send("Not connected to a voice channel.")
        else:
            vc = connectionCache[message.guild.id]
            await vc.disconnect()
            del connectionCache[message.guild.id]
            await message.channel.send("Disconnected from Voice Channel.")

async def checkVoiceChannel(server):
    if server.id in connectionCache:
        vc = connectionCache[server.id]
        if len(vc.channel.members) <= 1:
            await vc.disconnect()
            del connectionCache[server.id]
