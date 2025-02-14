### SETUP



## Imports

# import discord.py libraries to interact with Discord
import discord
from discord.ext import commands, tasks
from discord.utils import get  # just so we don't have to type discord.utils.get a lot
from discord import app_commands  # to enable slash commands
from discord.ui import Button, View, Select

# import gspread libraries to interact with Google Sheets
import gspread

# import stuff to download images so we can post them to Discord
import aiohttp
import io

# import time stuff
from datetime import datetime
import pytz

# import helper stuff
import logging  # to log obviously
import os  # to get local files like credentials and such
import re  # regular expressions to parse certain strings
from pprint import pprint  # to pretty print lists and dictionaries
from functools import lru_cache  # Least Recently Used Cache so we don't have to pound the APIs
#from emoji import UNICODE_EMOJI

#import queue stuff
import queue


from utils.spreadsheet import *


## Logging

logger = logging.getLogger('Volunteer')  # set up a log called 'TO'
logger.setLevel(logging.DEBUG)  # set Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL) to only show info level and up

# output log to file
handler = logging.FileHandler(filename='VolunteerCommands.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))  # change this if you want log items formatted differently
logger.addHandler(handler)


## Google Sheets setup

# set credentials to use on the google sheet
gc = gspread.service_account(filename='credentials.json')



### FUNCTIONS



## Queue stuff
requests_queue = queue.Queue()

def queue_request(self, request):
    requests_queue.put(request)
    logging.info(f"Request added to Queue: {request.requester} is requesting {request.shift_type} at {request.shift_day} {request.shift_time}")
    logging.info(f"Queue size is now {str(requests_queue.qsize())}")
    # await self.bot.process_commands(message)





## Classes
class ShiftRequest:
    def __init__(self, timestamp, requester, shift_type, shift_day, shift_time, interaction) -> None:
        self.timestamp = timestamp
        self.requester = requester
        self.shift_type = shift_type
        self.shift_day = shift_day
        self.shift_time = shift_time
        self.interaction = interaction

    def is_available(self):
        # try:

            logger.info(f"is_available fired with self.shift_day={str(self.shift_day)}, self.shift_time={str(self.shift_time)}, and self.shift_type={str(self.shift_type)}")
    
            day_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value=str(self.shift_day))

            day_column = day_cell['column_index']
            day_row = day_cell['row_index']

            logger.info(f"day_column={str(day_column)}, day_row={str(day_row)}")
    
            time_column = get_time_column(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', day_row, day_column, self.shift_time)

            logger.info(f"time_column={str(time_column)}")
    
            shift_type_row = get_shift_type_row(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', self.shift_type)

            get_values.cache_clear()
            latest_values = get_values(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up')

            logger.info(latest_values[shift_type_row][time_column])
            logger.info(latest_values[shift_type_row][time_column].split('​')[1])
            
            shifts_left = int(latest_values[shift_type_row][time_column].split('​')[1])

            if shifts_left > 0:
                logger.info(f"{self.shift_type} at {self.shift_day} {self.shift_time} has {str(shifts_left)} shifts left and is available.")
                return True
            else:
                logger.info(f"{self.shift_type} at {self.shift_day} {self.shift_time} has {str(shifts_left)} shifts left and is not available.")
                return False
        # except:
            # return False
    
    def assign(self):
        day_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value=str(self.shift_day))

        day_column = day_cell['column_index']
        day_row = day_cell['row_index']

        time_column = get_time_column(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', day_row, day_column, self.shift_time)

        shift_type_row = get_shift_type_row(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', self.shift_type)

        requester_row = get_requester_row(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', self.requester)

        # gx_shift_signups_sheet.update_cell(requester_row + 1, time_column + 1, self.shift_type)
        set_value(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', requester_row + 1, time_column + 1, self.shift_type.title())
    
        # gx_shift_signups_values[requester_row][time_column] = self.shift_type


    def unschedule(self):
        day_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value=str(self.shift_day))

        day_column = day_cell['column_index']
        day_row = day_cell['row_index']

        time_column = get_time_column(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', day_row, day_column, self.shift_time)

        shift_type_row = get_shift_type_row(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', self.shift_type)

        requester_row = get_requester_row(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', self.requester)

        # gx_shift_signups_sheet.update_cell(requester_row + 1, time_column + 1, self.shift_type)
        set_value(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', requester_row + 1, time_column + 1, "")
    
        # gx_shift_signups_values[requester_row][time_column] = self.shift_type






































class UnscheduleShiftButton(Button):
    def __init__(self, label, style, shift):
        self.shift = shift
        super().__init__(label=label, style=style)

    async def callback(self, interaction):
        self.shift.unschedule()
        await interaction.response.send_message(f'{self.label} has been removed from your schedule.')











































class UserShiftButtons(discord.ui.View):
    def __init__(self, *, timeout=600, username="", shifts=[]):
        self.username = username
        self.shifts = shifts
        super().__init__(timeout=timeout)

        for shift in self.shifts:
            self.add_item(UnscheduleShiftButton(label=f"{shift.shift_day.title()}, {shift.shift_time}: {shift.shift_type.upper()}", style=discord.ButtonStyle.blurple, shift=shift))






















































































### CLASS

class VolunteerCommands(commands.Cog):

    ## Events

    def __init__(self, bot):
        self.bot = bot
        # await bot.tree.sync()
        self.process_requests.start()

    async def cog_load(self):
        print('Volunteer Commands ready')
        logger.info("VolunteerCommands Cog loaded.")



    ## Commands

    @commands.Cog.listener("on_message")
    async def sheet_responses(self, message):
        # Get current datetime in PST
        tz = pytz.timezone('America/Los_Angeles')
        now = datetime.now(tz)
        msgDateTimeFormat = '%m/%d/%Y %I:%M %p'
        msgDateTime = datetime.strftime(now, msgDateTimeFormat)

        sorry_msg = "Unfortunately, the bot is no longer accepting shift signups. If you would like to sign-up for a shift, please visit the TO desk."
        signup_msgs = [
            "i would like to help with checkin",
            "i would like to help with ultimate",
            "i would like to help with melee",
            "i would like to help with rivals",
            "i would like to help with street fighter",
            "i would like to help with tekken",
            "i would like to help with guilty gear",
            "i would like to help with degenesis",
            "i would like to help with data entry",
            "i would like to help with brackets on demand",
            "i would like to help with info desk",
            "i would like to help with floater"
        ]
        # Respond to request to help
        if message.content.lower() in signup_msgs:
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(sorry_msg)

            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")

        if message.content.lower() == "what are my shifts?":
            await message.add_reaction("✅")
        
            get_values.cache_clear()
            latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')
            day_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/13")

            day_column = day_cell['column_index']
            day_row = day_cell['row_index']
            day_text = "Thursday"

            time_row = day_row + 1

            # print(f"{message.author.display_name}")
            # print(dir(message))
            # print("asdfasdfasdfadsfsafdsaf")
            # print(dir(message.author))

            requester_row = get_requester_row(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', message.author.display_name)

            shifts = []

            
            
            for column in range(day_column, len(latest_data[0]), 1):
                if day_text != latest_data[day_row][column] and len(latest_data[day_row][column]) > 1:
                    day_text = latest_data[day_row][column]
                if (len(latest_data[requester_row][column]) > 1):
                    shifts.append(ShiftRequest(msgDateTime, message.author.display_name, str(latest_data[requester_row][column]), day_text, str(latest_data[time_row][column]), ""))
                    # view.add_item(discord.ui.Button(label=f"{str(latest_data[requester_row][column])}, {day_text}, {str(latest_data[time_row][column])}"))

            if (len(shifts) < 1):
                await message.author.send(f"We don't currently have you signed up for any shifts right as of {msgDateTime} PST")
                return
            
            
            view=UserShiftButtons(username=str(message.author), shifts = shifts)
            
            await message.author.send(f"As of {msgDateTime} PST, we have you signed up for the following shifts. If you would like to remove a shift from your schedule, please click on the corresponding button.", view=view)

        

        return
    


    ## Loops
    # loop every 60 seconds to prevent going over rate limit
    @tasks.loop(seconds=15.0)
    async def process_requests(self):
        logger.info(f'Processing next request. There are {requests_queue.qsize()} requests left in the request queue.')
        
        # Sanity Check: Make sure queue is not empty before continuing.
        if requests_queue.empty():
            logger.info(f'The request queue is empty. Skipping processing.')
            return

        # Get the next request.
        request = requests_queue.get()

        logger.info(f"Processing {request.requester}'s request to help with {request.shift_type} on {request.shift_day}, starting at {request.shift_time}")
        
        if (request.is_available()):
            logger.info(f"{request.requester}'s request to help with {request.shift_type} on {request.shift_day}, starting at {request.shift_time} is available.")
        
            request.assign()
            await request.interaction.followup.send(content=f"```diff\n+ Your ({request.requester}) request to help with {request.shift_type} on {request.shift_day}, starting at {request.shift_time}, has been successfully assigned!```")
            logger.info(f"{request.requester}'s has been assigned to help with {request.shift_type} on {request.shift_day}, starting at {request.shift_time}")
        else:
            logger.info(f"{request.requester}'s request to help with {request.shift_type} on {request.shift_day}, starting at {request.shift_time} is NOT available.")
        
            await request.interaction.followup.send(content=f"```diff\n- Your ({request.requester}) request to help with {request.shift_type} on {request.shift_day}, starting at {request.shift_time}, is unavailable```")
            logger.info(f"Request is unavailable.")

    @process_requests.before_loop
    async def before_processing(self):
        logger.info('Waiting for bot to be ready before we start to process requests.')
        await self.bot.wait_until_ready()



async def setup(bot):
    await bot.add_cog(VolunteerCommands(bot))