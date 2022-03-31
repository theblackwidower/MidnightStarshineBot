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

from Constants import *
from Utilities import *

MIN_GROUP_NAME_LENGTH = 4

CREATE_ROLE_GROUP_COMMAND = "createrolegroup"
DELETE_ROLE_GROUP_COMMAND = "deleterolegroup"
ADD_TO_ROLE_GROUP_COMMAND = "addtogroup"
REMOVE_FROM_ROLE_GROUP_COMMAND = "removefromgroup"

async def createRoleGroup(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        name = commandArgs
        if len(name) < MIN_GROUP_NAME_LENGTH:
            await message.channel.send("Group name must be at least " + str(MIN_GROUP_NAME_LENGTH) + " characters long.")
        elif name.count(" "):
            await message.channel.send("Name cannot contain spaces. Sorry.")
        else:
            conn = await getConnection()
            try:
                nameData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_role_groups WHERE server = $1 AND group_name = $2', message.guild.id, name)
                if nameData[0] > 0:
                    await message.channel.send("That name is already in use.")
                else:
                    await conn.execute('INSERT INTO tbl_role_groups (server, group_name) VALUES ($1, $2)', message.guild.id, name)
                    await message.channel.send("The " + name + " group has been created. You can add roles to it by entering `" + getPrefix(message.guild) + ADD_TO_ROLE_GROUP_COMMAND + " " + name + "` followed by the role you want to add.")
            finally:
                await returnConnection(conn)

async def deleteRoleGroup(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        name = commandArgs
        conn = await getConnection()
        try:
            serverData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_role_groups WHERE server = $1 AND group_name = $2', message.guild.id, name)
            if serverData[0] > 0:
                await conn.execute('DELETE FROM tbl_role_groups WHERE server = $1 AND group_name = $2', message.guild.id, name)
                await message.channel.send("The " + name + " group has been deleted.")
            else:
                await message.channel.send("No group found by that name.")
        finally:
            await returnConnection(conn)

async def addToRoleGroup(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        parsing = commandArgs.partition(" ")
        groupName = parsing[0]
        roleString = parsing[2]
        if roleString == "" or groupName == "":
            await message.channel.send("I'm missing some information, I'm sure of it. You need to provide me with the name of a role group, and a role.")
        else:
            role = parseRole(message.guild, roleString)
            if role is None:
                await message.channel.send("Cannot find the role entered.")
            else:
                conn = await getConnection()
                try:
                    groupData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_role_groups WHERE server = $1 AND group_name = $2', message.guild.id, groupName)
                    roleData = await conn.fetchrow('SELECT group_name FROM tbl_controlled_roles WHERE server = $1 AND role = $2', message.guild.id, role.id)
                    if groupData[0] == 0:
                        await message.channel.send("Cannot find a role group called \"" + groupName + "\".")
                    elif roleData is not None:
                        await message.channel.send("Role is already assigned to the " + roleData[0] + " group.")
                    else:
                        await conn.execute('INSERT INTO tbl_controlled_roles (server, group_name, role) VALUES ($1, $2, $3)', message.guild.id, groupName, role.id)
                        await message.channel.send("The " + role.name + " role has been successfully added to the " + groupName + " group.")
                finally:
                    await returnConnection(conn)

async def removeFromRoleGroup(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        parsing = commandArgs.partition(" ")
        groupName = parsing[0]
        roleString = parsing[2]
        if roleString == "" or groupName == "":
            await message.channel.send("I'm missing some information, I'm sure of it. You need to provide me with the name of a role group, and a role.")
        else:
            role = parseRole(message.guild, roleString)
            if role is None:
                await message.channel.send("Cannot find the role entered.")
            else:
                conn = await getConnection()
                try:
                    groupData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_role_groups WHERE server = $1 AND group_name = $2', message.guild.id, groupName)
                    removalData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_controlled_roles WHERE server = $1 AND groupName = $2 AND role = $3', message.guild.id, groupName, role.id)
                    if groupData[0] == 0:
                        await message.channel.send("Cannot find a role group called \"" + groupName + "\".")
                    elif removalData[0] == 0:
                        await message.channel.send("Role is not currently assigned to the " + roleData[0] + " group.")
                    else:
                        await conn.execute('DELETE FROM tbl_controlled_roles WHERE server = $1 AND group_name = $2 AND role = $3', message.guild.id, groupName, role.id)
                        await message.channel.send("The " + role.name + " role has been removed from the " + groupName + " group.")
                finally:
                    await returnConnection(conn)

async def checkRoleControl(before, after):
    roleListBefore = before.roles
    roleListAfter = after.roles

    if len(roleListAfter) > len(roleListBefore):
        newRole = None
        for role in roleListAfter:
            if role not in roleListBefore:
                newRole = role
                break
        if newRole is not None:
            conn = await getConnection()
            try:
                roleData = await conn.fetchrow('SELECT group_name FROM tbl_controlled_roles WHERE server = $1 AND role = $2', after.guild.id, newRole.id)
                if roleData is not None:
                    groupName = roleData[0]
                    restrictionData = await conn.fetch('SELECT role FROM tbl_controlled_roles WHERE server = $1 AND group_name = $2', after.guild.id, groupName)
                    await returnConnection(conn)
                    for row in restrictionData:
                        thisRole = after.guild.get_role(row[0])
                        if thisRole is None:
                            await conn.execute('DELETE FROM tbl_controlled_roles WHERE server = $1 AND role = $2', after.guild.id, row[0])
                        elif thisRole is not newRole and thisRole in roleListAfter:
                            await after.remove_roles(thisRole, reason="Member can only have one role from the " + groupName + " group.")
            finally:
                await returnConnection(conn)
