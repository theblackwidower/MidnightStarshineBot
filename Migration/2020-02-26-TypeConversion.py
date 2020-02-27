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

# On February 26, 2020. I altered the database schema to use more appropriate data types for dates and times.
# This file is meant to be run only once to convert a pre-existing database from the old system to the new system.
# It also tests for data integrity.
# But if something goes wrong, it will not attempt to undo what has already been done.
# Because of this, it is recommended that you backup the database before running this file.

import os
import datetime
import asyncpg
import asyncio

from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

async def migrate():
    try:
        print("Migrating...")
        conn = await asyncpg.connect(DATABASE_URL)

        old_payday_settings_data = await conn.fetch('SELECT server, amount, cooldown FROM tbl_payday_settings')
        old_transactions_data = await conn.fetch('SELECT server, member, date, amount_in, notes FROM tbl_transactions')
        old_active_role_settings_data = await conn.fetch('SELECT server, role, gap, duration, max FROM tbl_active_role_settings')
        old_activity_record_data = await conn.fetch('SELECT server, member, last_active FROM tbl_activity_record')

        await conn.execute('ALTER TABLE tbl_payday_settings ALTER COLUMN cooldown TYPE INTERVAL USING make_interval(secs => cooldown)')
        await conn.execute('ALTER TABLE tbl_transactions ALTER COLUMN date TYPE TIMESTAMP USING to_timestamp(date)')
        await conn.execute('ALTER TABLE tbl_active_role_settings ALTER COLUMN gap TYPE INTERVAL USING make_interval(secs => gap)')
        await conn.execute('ALTER TABLE tbl_active_role_settings ALTER COLUMN duration TYPE INTERVAL USING make_interval(secs => duration)')
        await conn.execute('ALTER TABLE tbl_active_role_settings ALTER COLUMN max TYPE INTERVAL USING make_interval(secs => max)')
        await conn.execute('ALTER TABLE tbl_activity_record ALTER COLUMN last_active TYPE TIMESTAMP USING to_timestamp(last_active)')

        for payday_settings_row in old_payday_settings_data:
            server = payday_settings_row['server']
            amount = payday_settings_row['amount']
            new_cooldown = await conn.fetchval('SELECT cooldown FROM tbl_payday_settings WHERE server = $1 AND amount = $2', server, amount)
            old_cooldown = payday_settings_row['cooldown']
            if new_cooldown is None:
                message = "Conversion error in tbl_payday_settings.\n"
                message += "server: " + str(server) + "\n"
                message += "amount: " + str(amount) + "\n"
                message += "missing cooldown."
                raise Exception(message)
            elif datetime.timedelta(seconds=old_cooldown) != new_cooldown or old_cooldown != new_cooldown.total_seconds():
                message = "Conversion error in tbl_payday_settings.\n"
                message += "server: " + str(server) + "\n"
                message += "amount: " + str(amount) + "\n"
                message += "cooldown numbers: " + str(old_cooldown) + " AND " + str(new_cooldown.total_seconds()) + "\n"
                message += "cooldown objects: " + str(datetime.timedelta(seconds=old_cooldown)) + " AND " + str(new_cooldown)
                raise Exception(message)

        for transactions_row in old_transactions_data:
            server = transactions_row['server']
            member = transactions_row['member']
            old_date = transactions_row['date']
            amount_in = transactions_row['amount_in']
            notes = transactions_row['notes']
            converted_old_date = datetime.datetime.fromtimestamp(old_date)
            new_date = await conn.fetchval('SELECT date FROM tbl_transactions WHERE server = $1 AND member = $2 AND date = $3 AND amount_in = $4 AND notes = $5', server, member, converted_old_date, amount_in, notes)
            if new_date is None:
                message = "Conversion error in tbl_transactions.\n"
                message += "server: " + str(server) + "\n"
                message += "member: " + str(member) + "\n"
                message += "date: " + str(old_date) + "\n"
                message += "amount_in: " + str(amount_in) + "\n"
                message += "notes: " + str(notes) + "\n"
                message += "Can't find row in new table."
                raise Exception(message)
            elif datetime.datetime.fromtimestamp(old_date) != new_date or old_date != new_date.timestamp():
                message = "Conversion error in tbl_active_role_settings.\n"
                message += "server: " + str(server) + "\n"
                message += "member: " + str(member) + "\n"
                message += "amount_in: " + str(amount_in) + "\n"
                message += "notes: " + str(notes) + "\n"
                message += "date numbers: " + str(old_date) + " AND " + str(new_date.timestamp()) + "\n"
                message += "date objects: " + str(datetime.datetime.fromtimestamp(old_date)) + " AND " + str(new_date) + "\n"
                raise Exception(message)

        for active_role_settings_row in old_active_role_settings_data:
            server = active_role_settings_row['server']
            role = active_role_settings_row['role']
            new_data = await conn.fetchrow('SELECT gap, duration, max FROM tbl_active_role_settings WHERE server = $1 AND role = $2', server, role)
            if new_data is None:
                message = "Conversion error in tbl_active_role_settings.\n"
                message += "server: " + str(server) + "\n"
                message += "role: " + str(role) + "\n"
                message += "missing all further data."
                raise Exception(message)
            else:
                new_gap = new_data['gap']
                new_duration = new_data['duration']
                new_max = new_data['max']
                old_gap = active_role_settings_row['gap']
                old_duration = active_role_settings_row['duration']
                old_max = active_role_settings_row['max']
                if datetime.timedelta(seconds=old_gap) != new_gap or old_gap != new_gap.total_seconds()or datetime.timedelta(seconds=old_duration) != new_duration or old_duration != new_duration.total_seconds() or datetime.timedelta(seconds=old_max) != new_max or old_max != new_max.total_seconds():
                    message = "Conversion error in tbl_active_role_settings.\n"
                    message += "server: " + str(server) + "\n"
                    message += "role: " + str(role) + "\n"
                    message += "gap numbers: " + str(old_gap) + " AND " + str(new_gap.total_seconds()) + "\n"
                    message += "gap objects: " + str(datetime.timedelta(seconds=old_gap)) + " AND " + str(new_gap) + "\n"
                    message += "duration numbers: " + str(old_duration) + " AND " + str(new_duration.total_seconds()) + "\n"
                    message += "duration objects: " + str(datetime.timedelta(seconds=old_duration)) + " AND " + str(new_duration) + "\n"
                    message += "max numbers: " + str(old_max) + " AND " + str(new_max.total_seconds()) + "\n"
                    message += "max objects: " + str(datetime.timedelta(seconds=old_max)) + " AND " + str(new_max) + "\n"
                    raise Exception(message)

        for activity_record_row in old_activity_record_data:
            server = activity_record_row['server']
            member = activity_record_row['member']
            new_last_active = await conn.fetchval('SELECT last_active FROM tbl_activity_record WHERE server = $1 AND member = $2', server, member)
            old_last_active = activity_record_row['last_active']
            if new_last_active is None:
                message = "Conversion error in tbl_payday_settings.\n"
                message += "server: " + str(server) + "\n"
                message += "amount: " + str(amount) + "\n"
                message += "missing last_active."
                raise Exception(message)
            elif datetime.datetime.fromtimestamp(old_last_active) != new_last_active or old_last_active != new_last_active.timestamp():
                message = "Conversion error in tbl_payday_settings.\n"
                message += "server: " + str(server) + "\n"
                message += "amount: " + str(amount) + "\n"
                message += "last_active numbers: " + str(old_last_active) + " AND " + str(new_last_active.timestamp()) + "\n"
                message += "last_active objects: " + str(datetime.datetime.fromtimestamp(old_last_active)) + " AND " + str(new_last_active) + "\n"
                raise Exception(message)

    finally:
        await conn.close()

asyncio.run(migrate())
