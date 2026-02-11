from config import (
    SHEET_DISCORD_MEMBERS,
    SHEET_DISCORD_MEMBERS_ID_COL,
    SHEET_DISCORD_MEMBERS_NAME_COL,
    SHEET_DISCORD_MEMBERS_NICKNAME_COL,
    SHEET_DISCORD_MEMBERS_VOLUNTEERS_TAB,
    SHIFT_VALIDATION_WEBHOOK_ID,
)
from discord.ext import commands
import logging  # to log obviously
from pprint import pprint  # to pretty print lists and dictionaries
from functools import lru_cache

from utils.spreadsheet import *
from utils.logging_setup import new_logger

logger = new_logger("ShiftValidation", logging.INFO)


class ShiftValidationCommands(commands.Cog):

    ## Events

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("Shift Validation Commands ready")
        logger.info("ShiftValidationCommands Cog loaded.")

    @commands.Cog.listener("on_message")
    async def notify_rewards_from_webhook(self, msg):
        # TODO: Change hardcoded webhook id
        if msg.webhook_id != SHIFT_VALIDATION_WEBHOOK_ID:
            return

        content = msg.content
        command = content.split()[0]
        if command != "!notify_rewards":
            return  # something else, not handling here

        username = content.split()[1]
        message = " ".join(content.split()[2:])

        volunteer_data = get_values(
            spreadsheet=SHEET_DISCORD_MEMBERS,
            sheet=SHEET_DISCORD_MEMBERS_VOLUNTEERS_TAB,
        )

        user_data = get_user_data(username, volunteer_data)

        if user_data is None:
            print(f"User {username} not found")
            await msg.delete()
            return

        user = self.bot.get_user(int(user_data[SHEET_DISCORD_MEMBERS_ID_COL]))
        await user.send(message)
        await msg.delete()


def get_user_data(username, volunteer_data: list) -> dict:
    # TODO Change to get_requester_row
    # ignore the header line, cause im not dealing with pandas at the moment
    for user_details in volunteer_data[1:]:
        if username.lower() in [
            user_details[SHEET_DISCORD_MEMBERS_NAME_COL].lower(),
            user_details[SHEET_DISCORD_MEMBERS_NICKNAME_COL].lower(),
        ]:
            return user_details
    return None


async def setup(bot):
    await bot.add_cog(ShiftValidationCommands(bot))
