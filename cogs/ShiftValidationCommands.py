from discord.ext import commands
from discord.utils import get
import logging  # to log obviously
import os  # to get local files like credentials and such
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
        if msg.webhook_id == 1337111947551703142:
            # parse the msg
            content = msg.content
            command = content.split()[0]
            if command != "!notify_rewards":
                return  # something else, not handling here

            user_name = content.split()[1]
            message = " ".join(content.split()[2:])

            volunteer_data = get_values(
                spreadsheet=os.getenv("SHEET_DISCORD_MEMBERS"), sheet="SYF"
            )
            # print(volunteer_data)
            user_data = None
            # Currently hardcoded, would want to update to be dynamic
            id_col = 0
            name_col = 1
            nick_col = 3
            # TODO Change to get_requester_row
            for user_details in volunteer_data[
                1:
            ]:  # ignore the header line, cause im not dealing with pandas at the moment
                if user_name.lower() in [
                    user_details[name_col].lower(),
                    user_details[nick_col].lower(),
                ]:
                    user_data = user_details
                    break
            if user_data is None:
                print(f"User {user_name} not found")
                await msg.delete()
                return

            user = self.bot.get_user(int(user_data[id_col]))
            await user.send(message)
            await msg.delete()


async def setup(bot):
    await bot.add_cog(ShiftValidationCommands(bot))
