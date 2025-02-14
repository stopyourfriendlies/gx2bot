from dotenv import load_dotenv
import json
import logging
import os
import queue
import time

import discord
import gspread
import requests
from discord.ext import commands, tasks


import gspread

gc = gspread.service_account(filename='credentials.json')

# Open a sheet from a spreadsheet in one go
subscribersSheet = gc.open("Subscribers to Alerts").sheet1

# load environment variables from .env
load_dotenv()

logging.basicConfig(filename='perspective_check.log',
                    encoding='utf-8', level=logging.INFO)
logger = logging.getLogger('perspective')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename='perspective_check.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


# set credentials to use on the google sheet
gc = gspread.service_account(filename='credentials.json')

# Open a sheet from a spreadsheet in one go
message_check_sheet = gc.open(os.getenv('SHEET_MESSAGE_CHECK')).sheet1

# set perspective api stuff
api_key = str(os.getenv('PERSPECTIVE_API_KEY'))
url = ('https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze' + '?key=' + api_key)

message_queue = queue.Queue()


class Perspective(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.perspective_check.start()
        # self.guild = bot.get_guild(805237132469862000)

    # Events

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info('Perspective ready')
    
    async def cog_load(self):
        print('Puzzle Commands ready')
        logger.info("Puzzle Cog loaded.")
    
    def cog_unload(self):
        self.perspective_check.cancel()

    @commands.Cog.listener("on_message")
    async def queue_message(self, message):
        logging.info(f'Queue message: {message.content}')
        message_queue.put([
            str(message.author),
            str(message.content),
            str(message.created_at),
            str(message.edited_at),
            message.id,
            str(message.guild),
            str(message.channel)
        ])
        logging.info(f'Queue size: {str(message_queue.qsize())}')
        # await self.bot.process_commands(message)

    @tasks.loop(seconds=15.0)
    async def perspective_check(self):
        print('perspective check')
        if message_queue.empty():
            # print("Queue empty")
            return

        message = message_queue.get()

        current_time = time.strftime("%H:%M:%S", time.localtime())

        logging.info(f'{current_time}: Working on the message "{message[1]}"')

        if len(message[1]) <= 0:
            message_queue.task_done()
            return

        data_dict = {
            'comment': {'text': message[1]},
            'languages': ['en'],
            'requestedAttributes': {
                'TOXICITY': {},
                'IDENTITY_ATTACK': {},
                'INSULT': {},
                'PROFANITY': {},
                'THREAT': {},
                'SEXUALLY_EXPLICIT': {},
                'FLIRTATION': {},
                'INFLAMMATORY': {},
                'SPAM': {},
                'UNSUBSTANTIAL': {}
            }
        }

        response = requests.post(url=url, data=json.dumps(data_dict))
        response_dict = json.loads(response.content)

        # print(response_dict)

        perspective_results = [
            response_dict["attributeScores"]["TOXICITY"]["summaryScore"]["value"],
            response_dict["attributeScores"]["IDENTITY_ATTACK"]["summaryScore"]["value"],
            response_dict["attributeScores"]["INSULT"]["summaryScore"]["value"],
            response_dict["attributeScores"]["PROFANITY"]["summaryScore"]["value"],
            response_dict["attributeScores"]["THREAT"]["summaryScore"]["value"],
            response_dict["attributeScores"]["SEXUALLY_EXPLICIT"]["summaryScore"]["value"],
            response_dict["attributeScores"]["FLIRTATION"]["summaryScore"]["value"],
            response_dict["attributeScores"]["INFLAMMATORY"]["summaryScore"]["value"],
            response_dict["attributeScores"]["SPAM"]["summaryScore"]["value"],
            response_dict["attributeScores"]["UNSUBSTANTIAL"]["summaryScore"]["value"]
        ]

        message.extend(perspective_results)

        message_check_sheet.append_row(message)

        message_queue.task_done()

        logging.info(str(message))

    # Commands
    @commands.command()
    async def subscribe(self, ctx):
        id_list = subscribersSheet.col_values(1)
        # username_list = subscribersSheet.col_values(2)

        if str(ctx.message.author.id) not in id_list:
            subscribersSheet.append_row([str(ctx.message.author.id), ctx.message.author.name, str(
                ctx.message.author.discriminator), 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 1.00])

        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Perspective(bot))
