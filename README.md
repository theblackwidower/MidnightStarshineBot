# Midnight Starshine

This is Midnight Starshine, the Discord bot I built for Ponyworld.

This bot is planned to have many functions, all coded directly in the bot.

## Install

First of all, you'll need a Discord Bot Token. This is how the bot logs into Discord.

If you don't have a bot token, you can get one here: [Discord Developers Portal](https://discordapp.com/developers/applications)

With that, add a new file in the bot's root folder named `.env`. (The dot at the beginning is very important.)

This file should contain the following code:
```
DISCORD_TOKEN=[Insert Bot Token here]
ERROR_LOG=[Full path to where you want the error log to be]
DATABASE_URL=postgresql://localhost/Midnight?user=[username]&password=[password]
```
Insert the token in the appropriate location. (Don't include the brackets.)

Also, select a location for the error log to be written to, and enter the full path in the file as well.

You'll need to install Python 3.7+.

You'll also need to install a few Python modules. They're defined in the requirements file, so it's all done with a single command.
```
$ pip install -r requirements.txt
```

Finally, you'll need to set up an PostgreSQL database. Name it Midnight and initialize it with the schema in `Midnight.sql`.

Enter the login information in the `.env` file.

From here, running the bot is simple:
```
$ python Midnight.py
```

## Working Features

  * Stopping Emoji Spam
  * Echo feature (limited to access by a single user, me... can be customized)
  * Rolecall, lists all users (can be filtered by role) sorted by whatever their top role is.
  * YAG Snipe, automatically kicks or bans a specified user, designed to deal with problems related to the bot YAGPDB.xyz.
  * Active user feature assigns custom roles based on user activity rates
  * On-the-fly rule management and lookup through bot commands.

## Upcoming Features

  * Currency system ('payday' command)
  * Time-delayed echo
  * Moderation features (mute, warn, kick, and ban commands)
  * Automated welcome
