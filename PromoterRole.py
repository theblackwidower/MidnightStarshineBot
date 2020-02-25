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

import asyncpg

from Constants import *
from Utilities import *

SETUP_PROMOTER_ROLE_COMMAND = "setuppromoterrole"
CLEAR_PROMOTER_ROLE_COMMAND = "clearpromoterrole"

invitesCache = dict()
invitesCacheTime = dict()

async def setupInviteDataCache(server):
    if server.id not in invitesCache:
        conn = await getConnection()
        serverData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_promoter_role_settings WHERE server = $1', server.id)
        await returnConnection(conn)
        if serverData[0] > 0:
            invitesCache[server.id] = dict()
            invitesCacheTime[server.id] = datetime.datetime.utcnow()
            allInvites = await server.invites()
            for invite in allInvites:
                cacheInvite(invite, invite.created_at, server.id)

def cacheInvite(invite, creationTime, serverId):
    if invite.max_age > 0:
        expiry = creationTime + datetime.timedelta(seconds=invite.max_age)
    else:
        expiry = None

    if invite.max_uses > 0:
        maxUses = invite.max_uses
    else:
        maxUses = None
    invitesCache[serverId][invite.code] = (expiry, invite.uses, maxUses, invite.inviter.id)

async def setupPromoterRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + SETUP_PROMOTER_ROLE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        parsing = parsing[2].rpartition(" ")
        recruitCountString = parsing[2]
        roleString = parsing[0]

        if roleString == "" or recruitCountString == "":
            await message.channel.send("I'm missing some information, I'm sure of it. You need to provide me with a role, and a number of recruits needed to qualify for the role.")
        else:
            role = parseRole(message.guild, roleString)
            if role is None:
                await message.channel.send("Cannot find the role entered.")
            elif not recruitCountString.isdigit():
                await message.channel.send("What you provided for number of recruits is not a number.")
            else:
                recruitCount = int(recruitCountString)
                conn = await getConnection()
                serverCountData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_promoter_role_settings WHERE server = $1 AND recruit_count = $2', message.guild.id, recruitCount)
                serverRoleData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_promoter_role_settings WHERE server = $1 AND role = $2', message.guild.id, role.id)
                if serverCountData[0] > 0 and serverRoleData[0] > 0:
                    output = "Promoter role has already been setup with those parameters.\n"
                else:
                    if serverCountData[0] > 0:
                        await conn.execute('UPDATE tbl_promoter_role_settings SET role = $1 WHERE server = $2 AND recruit_count = $3', role.id, message.guild.id, recruitCount)
                        output = "Promoter role successfully updated with the following parameters:\n"
                    elif serverRoleData[0] > 0:
                        await conn.execute('UPDATE tbl_promoter_role_settings SET recruit_count = $1 WHERE server = $2 AND role = $3', recruitCount, message.guild.id, role.id)
                        output = "Promoter role successfully updated with the following parameters:\n"
                    else:
                        await conn.execute('INSERT INTO tbl_promoter_role_settings (server, role, recruit_count) VALUES ($1, $2, $3)', message.guild.id, role.id, recruitCount)
                        await setupInviteDataCache(message.guild)
                        output = "New promoter role successfully set up with the following parameters:\n"
                    output += "We'll be assigning the \"__" + role.name + "__\" role...\n"
                    output += "... to any user whose invites bring in __" + str(recruitCount) + "__ members.\n"
                await message.channel.send(output)
                await returnConnection(conn)

async def clearPromoterRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + CLEAR_PROMOTER_ROLE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        conn = await getConnection()
        serverData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_promoter_role_settings WHERE server = $1', message.guild.id)
        if serverData[0] > 0:
            await conn.execute('DELETE FROM tbl_promoter_role_settings WHERE server = $1', message.guild.id)
            del invitesCache[message.guild.id]
            await message.channel.send("Promoter role feature completely cleared out. If you want to reenable it, please run `" + COMMAND_PREFIX + SETUP_PROMOTER_ROLE_COMMAND + "` again.")
        else:
            await message.channel.send("Promoter role feature has not even been set up, so there's no reason to clear it.")
        await returnConnection(conn)

async def recordRecruit(recruit):
    if not recruit.bot:
        conn = await getConnection()
        serverData = await conn.fetch('SELECT role, recruit_count FROM tbl_promoter_role_settings WHERE server = $1', recruit.guild.id)
        if len(serverData) > 0:
            if recruit.guild.id not in invitesCache:
                await setupInviteDataCache(recruit.guild)
            else:
                currentTime = datetime.datetime.utcnow()
                async for item in recruit.guild.audit_logs(limit=100000, after=invitesCacheTime[recruit.guild.id], action=discord.AuditLogAction.invite_create):
                    if item.created_at > invitesCacheTime[recruit.guild.id]:
                        cacheInvite(item.after, item.created_at, recruit.guild.id)
                async for item in recruit.guild.audit_logs(limit=100000, after=invitesCacheTime[recruit.guild.id], action=discord.AuditLogAction.invite_delete):
                    if item.created_at > invitesCacheTime[recruit.guild.id]:
                        del invitesCache[recruit.guild.id][item.before.code]
                invitesCacheTime[recruit.guild.id] = currentTime

                foundInviter = None
                allInvites = await recruit.guild.invites()
                inviteCodeList = list(invitesCache[recruit.guild.id])
                for inviteCode in inviteCodeList:
                    expiry, uses, maxUses, inviterId = invitesCache[recruit.guild.id][inviteCode]
                    if expiry is not None and expiry < currentTime:
                        del invitesCache[recruit.guild.id][inviteCode]
                    else:
                        updatedInvite = discord.utils.get(allInvites, code=inviteCode)
                        if updatedInvite is None and maxUses is not None and maxUses == uses + 1:
                            foundInviter = inviterId
                            del invitesCache[recruit.guild.id][inviteCode]
                            break
                        elif updatedInvite is not None and uses < updatedInvite.uses:
                            foundInviter = inviterId
                            del invitesCache[recruit.guild.id][inviteCode]
                            invitesCache[recruit.guild.id][inviteCode] = expiry, uses + 1, maxUses, inviterId
                            break

                if foundInviter is None:
                    raise Exception("Can't find invite of new user.")
                else:
                    recruiterId = foundInviter
                    if recruiterId != recruit.id:
                        repetitionData = await conn.fetchrow('SELECT COUNT(recruiter) FROM tbl_recruitment_record WHERE server = $1 AND recruited_member = $2', recruit.guild.id, recruit.id)
                        if repetitionData[0] == 0:
                            await conn.execute('INSERT INTO tbl_recruitment_record (server, recruiter, recruited_member) VALUES ($1, $2, $3)', recruit.guild.id, recruiterId, recruit.id)
                            recruiter = recruit.guild.get_member(recruiterId)
                            if recruiter is not None and not recruiter.bot:
                                for row in serverData:
                                    role = recruit.guild.get_role(row[0])
                                    recruitCount = row[1]
                                    if recruiter.roles.count(role) == 0:
                                        countData = await conn.fetchrow('SELECT COUNT(recruited_member) FROM tbl_recruitment_record WHERE server = $1 AND recruiter = $2', recruit.guild.id, recruiter.id)
                                        if countData[0] >= recruitCount:
                                            await recruiter.add_roles(role, reason="Recruited a total of " + str(countData[0]) + " members.")
                                        else:
                                            break
        await returnConnection(conn)

async def persistPromoterRole(member):
    if isinstance(member, discord.Member) and not member.bot:
        conn = await getConnection()
        serverData = await conn.fetch('SELECT role, recruit_count FROM tbl_promoter_role_settings WHERE server = $1', member.guild.id)
        if len(serverData) > 0:
            recordData = await conn.fetchrow('SELECT COUNT(recruited_member) FROM tbl_recruitment_record WHERE server = $1 AND recruiter = $2', member.guild.id, member.id)
            recruitCount = recordData[0]
            for row in serverData:
                role = member.guild.get_role(row[0])
                minRecruitCount = row[1]
                if member.roles.count(role) > 0:
                    if recruitCount < minRecruitCount:
                        await member.remove_roles(role, reason="This user does not qualify for the promoter role, as they have only recruited " + str(recruitCount) + " members out of the " + str(minRecruitCount) + " they need.")
                else:
                    if recruitCount >= minRecruitCount:
                        await member.add_roles(role, reason="This user had their promoter role returned, since records show they recruited " + str(recruitCount) + " members, and they only need " + str(minRecruitCount) + " to qualify.")
        await returnConnection(conn)

async def deleteInvites(server, user):
    conn = await getConnection()
    serverData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_promoter_role_settings WHERE server = $1', server.id)
    await returnConnection(conn)
    if serverData[0] > 0:
        allInvites = await server.invites()
        for invite in allInvites:
            if invite.inviter.id == user.id:
                await invite.delete(reason="Member " + str(user) + " was banned. Their invites have been deleted to prevent further issues.")
