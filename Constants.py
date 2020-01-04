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

import os

from dotenv import load_dotenv

COMMAND_PREFIX = "ms!"

MIDNIGHTS_TRUE_MASTER = 204818040628576256

MAX_CHARS = 2000

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ERROR_LOG = os.getenv('ERROR_LOG')
DATABASE_URL = os.getenv('DATABASE_URL')
