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
            day_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value=str(self.shift_day))

            day_column = day_cell['column_index']
            day_row = day_cell['row_index']

            time_column = get_time_column(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up', day_row, day_column, self.shift_time)

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
    
        




        

































class CheckInSelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift
                if (row_index == thursday_row):
                    if str(latest_data[row_index][column_index]) != "":
                        shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("check-in" not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Check In"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the Check-In Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day.title()}, {shift_time}, {shift_type.upper()}",emoji="🚶",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no Check In shifts available right now."))

        # Set up the select menu
        super().__init__(placeholder="Check-In Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        if "sorry" in str(self.values[0]).lower():
            await interaction.response.defer()
        
        # Send the user a message that you are processing their requests
        await interaction.response.send_message(content="Your Check In shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class CheckInSelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(CheckInSelect())




























class MeleeSelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift
                if (row_index == thursday_row):
                    if str(latest_data[row_index][column_index]) != "":
                        shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("melee" not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Melee"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the Melee Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day.title()}, {shift_time}, {shift_type.upper()}",emoji="🚶",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no Melee shifts available right now."))

        # Set up the select menu
        super().__init__(placeholder="Melee Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        if "sorry" in str(self.values[0]).lower():
            await interaction.response.defer()
        
        # Send the user a message that you are processing their requests
        await interaction.response.send_message(content="Your Melee shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class MeleeSelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(MeleeSelect())



























class UltimateSelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift
                if (row_index == thursday_row):
                    if str(latest_data[row_index][column_index]) != "":
                        shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("ultimate" not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Ultimate"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the Ultimate Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day.title()}, {shift_time}, {shift_type.upper()}",emoji="📋",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no Ultimate shifts available right now."))
        super().__init__(placeholder="Ultimate Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        if "Sorry".lower() in str(self.values[0]).lower():
            await interaction.response.defer()
        # Send the user a message that you are processing their requests
        
        await interaction.response.send_message(content="Your Ultimate shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class UltimateSelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(UltimateSelect())



































class FloaterSelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift
                if (row_index == thursday_row):
                    if str(latest_data[row_index][column_index]) != "":
                        shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("FLOATER".lower() not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Floater"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the Floater Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day}, {shift_time}, {shift_type.upper()}",emoji="🚶",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no Floater shifts available right now."))
        super().__init__(placeholder="Floater Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        if "Sorry".lower() in str(self.values[0]).lower():
            await interaction.response.defer()
        # Send the user a message that you are processing their requests
        
        await interaction.response.send_message(content="Your Floater shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class FloaterSelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(FloaterSelect())



































class GuiltyGearSelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift if cell is not blank
                if (row_index == thursday_row) and str(latest_data[row_index][column_index]) != "":
                    shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("guilty gear" not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Guilty Gear"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the Guilty Gear Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day.title()}, {shift_time}, {shift_type.upper().title()}",emoji="📋",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no Guilty Gear shifts available right now."))

        # Set up the select menu
        super().__init__(placeholder="Guilty Gear Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        # if no shifts, make no response
        if "sorry" in str(self.values[0]).lower():
            await interaction.response.defer()

        # Send the user a message that you are processing their requests
        await interaction.response.send_message(content="Your Guilty Gear shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class GuiltyGearSelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(GuiltyGearSelect())




























class SF6Select(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift if cell is not blank
                if (row_index == thursday_row) and str(latest_data[row_index][column_index]) != "":
                    shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("sf6" not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Sf6"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the SF6 Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day.title()}, {shift_time}, {shift_type.upper()}",emoji="📋",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no SF6 shifts available right now."))

        # Set up the select menu
        super().__init__(placeholder="SF6 Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        # if no shifts, make no response
        if "sorry" in str(self.values[0]).lower():
            await interaction.response.defer()

        # Send the user a message that you are processing their requests
        await interaction.response.send_message(content="Your SF6 shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class SF6SelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(SF6Select())

























class TekkenSelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift if cell is not blank
                if (row_index == thursday_row) and str(latest_data[row_index][column_index]) != "":
                    shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("tekken" not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Tekken"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the Tekken Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day.title()}, {shift_time}, {shift_type.upper()}",emoji="📋",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no Tekken shifts available right now."))

        # Set up the select menu
        super().__init__(placeholder="Tekken Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        # if no shifts, make no response
        if "sorry" in str(self.values[0]).lower():
            await interaction.response.defer()

        # Send the user a message that you are processing their requests
        await interaction.response.send_message(content="Your Tekken shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class TekkenSelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(TekkenSelect())

























class RushdownSelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift if cell is not blank
                if (row_index == thursday_row) and str(latest_data[row_index][column_index]) != "":
                    shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("rushdown" not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Rushdown"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the Rushdown Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day.title()}, {shift_time}, {shift_type.upper()}",emoji="📋",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no Rushdown shifts available right now."))

        # Set up the select menu
        super().__init__(placeholder="Rushdown Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        # if no shifts, make no response
        if "sorry" in str(self.values[0]).lower():
            await interaction.response.defer()

        # Send the user a message that you are processing their requests
        await interaction.response.send_message(content="Your Rushdown shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class RushdownSelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(RushdownSelect())




























class BracketsOnDemandSelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift if cell is not blank
                if (row_index == thursday_row) and str(latest_data[row_index][column_index]) != "":
                    shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("brackets" not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Brackets On Demand"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the Brackets On Demand Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day.title()}, {shift_time}, {shift_type.upper()}",emoji="📋",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no Brackets On Demand shifts available right now."))

        # Set up the select menu
        super().__init__(placeholder="Brackets On Demand Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        # if no shifts, make no response
        if "sorry" in str(self.values[0]).lower():
            await interaction.response.defer()

        # Send the user a message that you are processing their requests
        await interaction.response.send_message(content="Your Brackets On Demand shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class BracketsOnDemandSelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(BracketsOnDemandSelect())


























class DataEntrySelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift if cell is not blank
                if (row_index == thursday_row) and str(latest_data[row_index][column_index]) != "":
                    shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("data entry" not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Data Entry"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the Data Entry Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day.title()}, {shift_time}, {shift_type.upper()}",emoji="📋",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no Data Entry shifts available right now."))

        # Set up the select menu
        super().__init__(placeholder="Data Entry Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        # if no shifts, make no response
        if "sorry" in str(self.values[0]).lower():
            await interaction.response.defer()

        # Send the user a message that you are processing their requests
        await interaction.response.send_message(content="Your Data Entry shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class DataEntrySelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(DataEntrySelect())

























class MerchSelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")
        thursday_column = thursday_cell['column_index']
        thursday_row = thursday_cell['row_index']

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):
                
                logger.debug(str(latest_data[row_index][column_index]))
                
                # Set day of week for shift if cell is not blank
                if (row_index == thursday_row) and str(latest_data[row_index][column_index]) != "":
                    shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if ("merch" not in str(latest_data[row_index][column_index]).lower()):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if ("​0​/" in str(latest_data[row_index][column_index])):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if (len(options) >= 25):
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Merch"

                # Add shift into the Select Menu dropdown
                logger.info(f"adding {shift_day.title()}, {shift_time}, {shift_type.upper()} to the Merch Select Menu")
                options.append(discord.SelectOption(label=f"{shift_day.title()}, {shift_time}, {shift_type.upper()}",emoji="📋",description=""))

        # Set the Select Menu options
        if len(options) < 1:
            options.append(discord.SelectOption(label=f"Sorry",emoji="❌",description="There are no Merch shifts available right now."))

        # Set up the select menu
        super().__init__(placeholder="Merch Shifts (Select Multiple)", max_values=len(options), min_values=0, options = options)
    
    async def callback(self, interaction: discord.Interaction):
        # if no shifts, make no response
        if "sorry" in str(self.values[0]).lower():
            await interaction.response.defer()

        # Send the user a message that you are processing their requests
        await interaction.response.send_message(content="Your Merch shift request(s) have been added to the queue. You will receive a response whether or not your shift was successfully added once your request is processed. Please be patient!", ephemeral=True)

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:
            
            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.display_name
            shift_type = response.split(',')[2].strip()
            shift_day = response.split(',')[0].strip()
            shift_time = response.split(',')[1].strip()
            
            request = ShiftRequest(timestamp, requester, shift_type, shift_day, shift_time, interaction)

            logging.info(f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}")
            
            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))

class MerchSelectView(discord.ui.View):
    def __init__(self, *, timeout = 600):
        super().__init__(timeout=timeout)
        self.add_item(MerchSelect())

























































































































































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

        # Respond to request to help with Check-In
        if message.content.lower() == "i would like to help with checkin":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**CHECK-IN SHIFT SIGNUPS**\n\nThanks for offering to help with the **Check-In** team.\n\nThe Check-In team leads are **<@214515494554697738>** and **<@237313363556696065>**.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n​",view=CheckInSelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")
        

        if message.content.lower() == "i would like to help with melee":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**MELEE SHIFT SIGNUPS**\n\nThanks for offering to help with the **Melee** team.\n\nThe Melee team leads are **<@327166415713075212>** and **<@150905096413118465>**.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n​",view=MeleeSelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")
        

        if message.content.lower() == "i would like to help with ultimate":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**ULTIMATE SHIFT SIGNUPS**\n\nThanks for offering to help with the **Ultimate** team.\n\nThe Ultimate team leads are **<@179308376650416128>**, **<@97043736063668224>**, and **<@231911162902478849>**.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n​",view=UltimateSelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")
        


        if message.content.lower() == "i would like to help with guilty gear":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**GUILTY GEAR SHIFT SIGNUPS**\n\nThanks for offering to help with the **Guilty Gear** team.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n​",view=GuiltyGearSelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")
        


        if message.content.lower() == "i would like to help with sf6":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**SF6 SHIFT SIGNUPS**\n\nThanks for offering to help with the **SF6** team.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n​",view=SF6SelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")
        

        if message.content.lower() == "i would like to help with tekken":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**TEKKEN SHIFT SIGNUPS**\n\nThanks for offering to help with the **Tekken** team.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n​",view=TekkenSelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")

        
        if message.content.lower() == "i would like to help with rushdown":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**RUSHDOWN SHIFT SIGNUPS**\n\nThanks for offering to help with the **Rushdown** team.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n​",view=RushdownSelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")
        
        

        if message.content.lower() == "i would like to help with brackets on demand":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**BRACKETS ON DEMAND SHIFT SIGNUPS**\n\nThanks for offering to help with the **Brackets On Demand** team.\n\nThe Brackets On Demand team leads are **<@154768322787934208>** and **<@167122411802591232>**.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n​",view=BracketsOnDemandSelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")
        
        

        if message.content.lower() == "i would like to help with data entry":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**DATA ENTRY SHIFT SIGNUPS**\n\nThanks for offering to help with the **Data Entry** team.\n\nThe Data Entry team leads are **<@92840691301900288>** and **<@133765875907035138>**.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n​",view=DataEntrySelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")
        


        if message.content.lower() == "i would like to help with merch":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**MERCH SHIFT SIGNUPS**\n\nThanks for offering to help with the **Merch** team.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n​",view=MerchSelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")
        



        if message.content.lower() == "i would like to help with floater":
            # Send a DM to the user with the Shift Signup dropdown
            await message.author.send(f"**FLOATER SHIFT SIGNUPS**\n\nThanks for offering to help with the **Floater** team.\n\nAs of *{msgDateTime} PST*, the following shifts in the dropdown are available. Please select when you would like to help out! Note that these are **2 hour shifts** that *start* at the listed time.\n\nThis drop-down will only work for the next 3 minutes. If you try to add a shift after then, you may get an Interaction Failed message. If that happens, please reprompt for a new dropdown.\n\n​",view=FloaterSelectView())
            
            # Acknowledge the user's message with an emote react.
            await message.add_reaction("✅")
        

        if message.content.lower() == "what are my shifts?":
            await message.add_reaction("✅")
        
            get_values.cache_clear()
            latest_data = get_values(os.getenv('SHEET_SHIFT_SIGNUPS'), 'Sign Up')
            day_cell = get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="Thursday 2/15")

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

            
            
            for column in range(day_column, len(latest_data[0]), 2):
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

    @tasks.loop(seconds=60.0)
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
            request.assign()
            await request.interaction.followup.send(content=f"```diff\n+ Your ({request.requester}) request to help with {request.shift_type} on {request.shift_day}, starting at {request.shift_time}, has been successfully assigned!```")
            logger.info(f"{request.requester}'s has been assigned to help with {request.shift_type} on {request.shift_day}, starting at {request.shift_time}")
        else:
            await request.interaction.followup.send(content=f"```diff\n- Your ({request.requester}) request to help with {request.shift_type} on {request.shift_day}, starting at {request.shift_time}, is unavailable```")
            logger.info(f"Request is unavailable.")

    @process_requests.before_loop
    async def before_processing(self):
        logger.info('Waiting for bot to be ready before we start to process requests.')
        await self.bot.wait_until_ready()



async def setup(bot):
    await bot.add_cog(VolunteerCommands(bot))