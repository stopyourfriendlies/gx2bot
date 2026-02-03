# import discord.py libraries to interact with Discord
import discord
from discord.ext import commands, tasks
from discord.utils import get  # just so we don't have to type discord.utils.get a lot
from discord import app_commands  # to enable slash commands

# import gspread libraries to interact with Google Sheets
import gspread

# import time stuff
from datetime import datetime

# import helper stuff
import os  # to get local files like credentials and such
from pprint import pprint  # to pretty print lists and dictionaries
from functools import (
    lru_cache,
)  # Least Recently Used Cache so we don't have to pound the APIs

# from emoji import UNICODE_EMOJI

from utils.spreadsheet import *


class CheckInSelect(discord.ui.Select):
    def __init__(self):
        # Clear cache and then pull the latest values from the sheet
        get_values.cache_clear()
        latest_data = get_values(os.getenv("SHEET_SHIFT_SIGNUPS"), "Sign Up")

        # Get the row and column of the Days of Week by finding where Thursday is
        thursday_cell = get_cell_indexes(
            spreadsheet=os.getenv("SHEET_SHIFT_SIGNUPS"),
            sheet="Sign Up",
            value="Thursday",
        )
        thursday_column = thursday_cell["column_index"]
        thursday_row = thursday_cell["row_index"]

        # Initialize some vars
        shift_day = "Thursday"
        options = []

        # Go bottom-up, left-right to find shifts
        for column_index in range(thursday_column, len(latest_data[0]), 2):
            for row_index in range(thursday_row, -1, -1):

                logger.debug(str(latest_data[row_index][column_index]))

                # Set day of week for shift
                if row_index == thursday_row:
                    if str(latest_data[row_index][column_index]) != "":
                        shift_day = str(latest_data[row_index][column_index])
                    continue

                # Sanity Check: skip if not the right shift type
                if "CHECK-IN" not in str(latest_data[row_index][column_index]):
                    continue

                # Sanity Check: skip if their are 0 shifts left
                if "​0​/" in str(latest_data[row_index][column_index]):
                    continue

                # Sanity Check: skip if there are more options then the max of 25 allowed within a Select Menu dropdown
                if len(options) >= 25:
                    break

                # If sanity checks pass, set the variables needed to add a select menu option
                shift_time = latest_data[int(thursday_row) + 1][column_index]
                shift_type = "Check In"

                # Add shift into the Select Menu dropdown
                logger.info(
                    f"adding {shift_day}, {shift_time}, {shift_type} to the CheckIn Select Menu"
                )
                options.append(
                    discord.SelectOption(
                        label=f"{shift_day}, {shift_time}, {shift_type}",
                        emoji="🚶",
                        description="",
                    )
                )

        # Set the Select Menu options
        super().__init__(
            placeholder="Check-In Shifts (Select Multiple)",
            max_values=len(options),
            min_values=0,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        # Send the user a message that you are processing their requests
        await interaction.response.send_message(
            content="Processing your Check-In shift requests...", ephemeral=True
        )

        # Go through each request if the user selected multiple options in the dropdown
        for response in self.values:

            # Form the shift request
            timestamp = datetime.now()
            requester = interaction.user.global_name
            shift_type = response.split(",")[2].replace(" ", "")
            shift_day = response.split(",")[0].replace(" ", "")
            shift_time = response.split(",")[1].replace(" ", "")

            request = ShiftRequest(
                timestamp, requester, shift_type, shift_day, shift_time, interaction
            )

            logging.info(
                f"Queue request: {requester} is requesting {shift_type} at {shift_day} {shift_time}"
            )

            # Add the shift request to the queue
            requests_queue.put(request)
            logging.info("Queue size: " + str(requests_queue.qsize()))


class CheckInSelectView(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
        self.add_item(CheckInSelect())
