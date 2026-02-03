### SETUP


## Imports

# import discord.py libraries to interact with Discord
import discord
from discord.ext import commands, tasks
from discord.utils import get  # just so we don't have to type discord.utils.get a lot

# import gspread libraries to interact with Google Sheets
import gspread

# import stuff to download images so we can post them to Discord
import aiohttp
import io

# import time stuff
from datetime import datetime

# import helper stuff
import logging  # to log obviously
import os  # to get local files like credentials and such
import re  # regular expressions to parse certain strings
from pprint import pprint  # to pretty print lists and dictionaries
from functools import (
    lru_cache,
)  # Least Recently Used Cache so we don't have to pound the APIs

# from emoji import UNICODE_EMOJI


## Logging

logger = logging.getLogger("TO")  # set up a log called 'TO'
logger.setLevel(
    logging.INFO
)  # set Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL) to only show info level and up

# output log to file
handler = logging.FileHandler(filename="TOCommands.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)  # change this if you want log items formatted differently
logger.addHandler(handler)


## Google Sheets setup

# set credentials to use on the google sheet
gc = gspread.service_account(filename="credentials.json")

# Open a sheet from a spreadsheet in one go
gx2_discord_members_spreadsheet = gc.open(os.getenv("SHEET_DISCORD_MEMBERS"))


### FUNCTIONS


# Type "!purge_role [role_name]" in a channel to remove all users from that role.
async def purge_role(self, role_name):
    logger.info(f"purge_role fired for {role_name} Role.")

    logger.info(f"grabbing guild object")
    try:
        guild = get(self.bot.guilds, name="Stop Your Friendlies")
    except:
        logger.error(f"failed to grab guild object")
        return

    logger.info(f"grabbing role object")
    try:
        role = get(guild.roles, name=role_name)
    except:
        logger.error(f"failed to grab role object")
        return

    if role is None:
        logger.warning(f"{role_name} Role cannot be purged since it cannot be found.")
        return

    # Cycle through each member that has the Role and remove the Role.
    for member in role.members:
        logger.info(f"{role_name} Role removed from {member}.")
        await member.remove_roles(role)

    logger.info(f"purge_role finished. {role_name} purged of members.")
    return


# Type "!purge_channel [channel_name]" in a channel to remove all messages from that channel.
async def purge_channel(self, channel_name):
    logger.info(f"purge_channel fired for #{channel_name}.")

    logger.info(f"grabbing guild object")
    try:
        guild = get(self.bot.guilds, name="Stop Your Friendlies")
    except:
        logger.error(f"failed to grab guild object")
        return

    if guild is None:
        logger.error(f"guild object is None")
        return

    logger.info(f"grabbing channel object")
    try:
        channel = get(self.bot.get_all_channels(), name=channel_name)
    except:
        logger.error(f"failed to grab channel object")
        return

    if channel is None:
        logger.error(f"channel object is None")
        return

    # Purge messages from the Channel.
    logger.info(f"purging channel of messages")
    try:
        await channel.purge()
    except:
        logger.error(f"purging messages failed")
        return

    logger.info(f"#{channel_name} purged of messages.")
    return


### CLASS


class TOCommands(commands.Cog):

    ## Events

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("TO Commands ready")
        logger.info("TOCommands Cog loaded.")

    ## Commands

    # Type "!getMembersInRole [role_name]" to populate the specified Google Sheet with Members of that Role.
    @commands.command()
    async def getMembersInRole(self, ctx, role_name):
        output = []

        for role in ctx.guild.roles:
            if role.name == role_name:
                # print(role.members)
                for member in role.members:
                    output.append(
                        [
                            str(member.id),
                            str(member.name),
                            str(member.discriminator),
                            str(member.nick),
                            member.bot,
                            str(member.guild.name),
                            str(member.guild.id),
                        ]
                    )

        # Sanity Check to make sure there are actually members that have the role before continuing.
        if len(output) <= 0:
            await ctx.message.delete()
            return

        try:
            # Grab the Google Sheet
            sheet = gx2_discord_members_spreadsheet.worksheet(role_name)
        except:
            # If the sheet doesn't exist for that role, create it
            sheet = gx2_discord_members_spreadsheet.add_worksheet(
                title=role_name, rows=100, cols=20
            )

            # Create header for the new sheet
            output.insert(
                0,
                [
                    "ID",
                    "Name",
                    "Discriminator",
                    "Nick",
                    "Bot?",
                    "Guild Name",
                    "Guild ID",
                    "Joined Names",
                ],
            )

        # Insert the Members into the Sheet
        sheet.append_rows(output)

        # Delete the message that was used to fire this command.
        await ctx.message.delete()

    # Type "!purge_role [role_name]" to delete all Members that have the specified Role.
    @commands.command()
    @commands.has_role("Admin")
    async def cmd_purge_role(self, ctx, role_name):
        await purge_role(self, role_name)
        await ctx.message.delete()

    # Type "!clear_channel [channel_name]" to delete all Messages within the specified channel.
    @commands.command()
    @commands.has_role("Admin")
    async def cmd_clear_channel(self, ctx, channel_name):
        await purge_channel(self, channel_name)
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(TOCommands(bot))
