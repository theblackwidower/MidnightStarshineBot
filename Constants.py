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

from Utilities import *

from os import getenv

from dotenv import load_dotenv

DEFAULT_PREFIX = "ms!"

MIDNIGHTS_TRUE_MASTER = 204818040628576256

MAX_CHARS = 2000

load_dotenv()
DISCORD_TOKEN = getenv('DISCORD_TOKEN')
ERROR_LOG = getenv('ERROR_LOG')
DATABASE_URL = getenv('DATABASE_URL')

CHANGE_PREFIX_COMMAND = "prefix"

prefixCache = dict()

async def buildPrefixCache(serverId):
    conn = await getConnection()
    try:
        serverData = await conn.fetchrow('SELECT prefix FROM tbl_prefix WHERE server = $1', serverId)
        if serverData is not None:
            prefixCache[serverId] = serverData[0]
    finally:
        await returnConnection(conn)

async def changePrefix(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        if commandArgs == "":
            await message.channel.send("You haven't provided a new prefix")
        elif " " in commandArgs:
            await message.channel.send("Prefix cannot contain any spaces.")
        else:
            newPrefix = commandArgs.casefold()
            conn = await getConnection()
            try:
                serverData = await conn.fetchrow('SELECT prefix FROM tbl_prefix WHERE server = $1', message.guild.id)
                if serverData is None:
                    await conn.execute('INSERT INTO tbl_prefix (server, prefix) VALUES ($1, $2)', message.guild.id, newPrefix)
                else:
                    await conn.execute('UPDATE tbl_prefix SET prefix = $1 WHERE server = $2', newPrefix, message.guild.id)
                prefixCache[message.guild.id] = newPrefix
                await message.channel.send("Prefix changed to `" + newPrefix + "`.")
            finally:
                await returnConnection(conn)

def getPrefix(server):
    if server is not None and server.id in prefixCache:
        return prefixCache[server.id]
    else:
        return DEFAULT_PREFIX
