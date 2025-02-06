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
from functools import lru_cache  # Least Recently Used Cache so we don't have to pound the APIs
#from emoji import UNICODE_EMOJI
from utils.spreadsheet import *



## Logging

logger = logging.getLogger('ShiftValidation')  # set up a log
logger.setLevel(logging.INFO)  # set Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL) to only show info level and up

# output log to file
handler = logging.FileHandler(filename='ShiftValidationCommands.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))  # change this if you want log items formatted differently
logger.addHandler(handler)



## Google Sheets setup

# set credentials to use on the google sheet
gc = gspread.service_account(filename='credentials.json')

# Open a sheet from a spreadsheet in one go
# gx2_discord_members_spreadsheet = gc.open(os.getenv('SHEET_DISCORD_MEMBERS'))





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

    if (guild is None):
        logger.error(f"guild object is None")
        return

    logger.info(f"grabbing channel object")
    try:
        channel = get(self.bot.get_all_channels(), name=channel_name)
    except:
        logger.error(f"failed to grab channel object")
        return

    if (channel is None):
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

class ShiftValidationCommands(commands.Cog):

    ## Events

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print('Shift Validation Commands ready')
        logger.info("ShiftValidationCommands Cog loaded.")

    ## Commands

    # Type "!ping" to check if bot is online.
    @commands.command()
    async def ping(self, ctx):
        await ctx.message.author.send("pong")
        await ctx.message.delete()
        return

    @commands.command()
    # Type "!notifyRewards <user> <message>" to notify <user> of their rewards (<message>).
    async def notify_rewards(self, ctx, user_name, *, msg):
        # user = None

        volunteer_data = get_values(spreadsheet=os.getenv('SHEET_DISCORD_MEMBERS'), sheet='SYF')
        #print(volunteer_data)
        user_data = None
        # Currently hardcoded, would want to update to be dynamic
        id_col = 0
        name_col = 1
        nick_col = 3
        for user_details in volunteer_data[1:]:  # ignore the header line, cause im not dealing with pandas at the moment
            if user_name.lower() in [user_details[name_col].lower(), user_details[nick_col].lower()]:
                user_data = user_details
                print(f"user is {user_data}")
                break
        if user_data is None:
            print(f"User {user_name} not found")
            await ctx.message.delete()
            return

        user = self.bot.get_user(int(user_data[id_col]))
        await user.send(msg)
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(ShiftValidationCommands(bot))
