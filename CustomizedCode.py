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

import re

from Constants import *
from Utilities import *

ELEMENT_FINDER = re.compile("^element of .*", flags=re.IGNORECASE)

async def ponyVersePersistElementRole(member):
    if member.guild.id == 682755852238848037:
        isMatch = ELEMENT_FINDER.fullmatch(member.display_name) is not None
        role = member.guild.get_role(683401036974915645)
        if role is not None:
            if member.roles.count(role) > 0:
                if not isMatch:
                    await member.remove_roles(role, reason="They're not an element.")
            else:
                if isMatch:
                    await member.add_roles(role, reason="They're now an element.")
