# import discord.py libraries to interact with Discord
import discord
from discord.ext import commands, tasks
from discord.utils import get  # just so we don't have to type discord.utils.get a lot
from discord import app_commands  # to enable slash commands

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



## Logging

logger = logging.getLogger('Spreadsheet Utils')  # set up a log called 'TO'
logger.setLevel(logging.INFO)  # set Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL) to only show info level and up

# output log to file
handler = logging.FileHandler(filename='SpreadsheetUtils.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))  # change this if you want log items formatted differently
logger.addHandler(handler)



## Google Sheets setup

# set credentials to use on the google sheet
gc = gspread.service_account(filename='credentials.json')



@lru_cache
def get_values(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up'):
    logger.info(f"get_values fired with spreadsheet={spreadsheet} and sheet={sheet}")
    
    logger.info(f"opening spreadsheet {spreadsheet}")
    try:
        openned_spreadsheet = gc.open(spreadsheet)
    except:
        logger.error(f"get_values failed to open {spreadsheet}")
        return []

    logger.info(f"opening sheet {sheet} in spreadsheet {spreadsheet}")
    try:
        if str(sheet).isdigit():
            logger.info(f"sheet var is digit, so will open as an index")
            openned_sheet = openned_spreadsheet.get_worksheet(int(sheet))
        else:
            logger.info(f"sheet var is not a digit, so will open by name")
            openned_sheet = openned_spreadsheet.worksheet(str(sheet))
    except:
        logger.error(f"get_values failed to open sheet {sheet} in spreadsheet {spreadsheet}")
        return []

    logger.info(f"getting values of sheet {sheet} in spreadsheet {spreadsheet}")
    try:
        openned_values = openned_sheet.get_values()
    except:
        logger.error(f"get_values failed to get values of sheet {sheet} in spreadsheet {spreadsheet}")
        return []    
    
    logger.info(f"get_values finished")
    return openned_values



def set_values(spreadsheet=os.getenv('SHEET_PUZZLES'), sheet=0, values=[]):
    logger.info(f"set_values fired with values={pprint(values)}, spreadsheet={spreadsheet}. and sheet={sheet}")
    
    logger.info(f"opening spreadsheet {spreadsheet}")
    try:
        openned_spreadsheet = gc.open(spreadsheet)
    except:
        logger.error(f"set_values failed to open {spreadsheet}")
        return

    logger.info(f"opening sheet {sheet} in spreadsheet {spreadsheet}")
    try:
        if str(sheet).isdigit():
            logger.info(f"sheet var is digit, so will open as an index")
            openned_sheet = openned_spreadsheet.get_worksheet(int(sheet))
        else:
            logger.info(f"sheet var is not a digit, so will open by name")
            openned_sheet = openned_spreadsheet.worksheet(str(sheet))
    except:
        logger.error(f"set_values failed to open sheet {sheet} in spreadsheet {spreadsheet}")
        return

    logger.info(f"writing values to sheet {sheet} in spreadsheet {spreadsheet}")
    try:
        openned_sheet.update(values, value_input_option='USER_ENTERED')  # need to use the 'USER-ENTERED' option so things like checkboxes don't turn into text
    except:
        logger.error("failed to update values")
        return

    logger.info(f"set_values finished")
    return



def set_value(spreadsheet=os.getenv('SHEET_PUZZLES'), sheet=0, row=1, column=2, value=""):
    logger.info(f"set_values fired with values={pprint(value)}, spreadsheet={spreadsheet}. and sheet={sheet}")
    
    logger.info(f"opening spreadsheet {spreadsheet}")
    try:
        openned_spreadsheet = gc.open(spreadsheet)
    except:
        logger.error(f"set_values failed to open {spreadsheet}")
        return

    logger.info(f"opening sheet {sheet} in spreadsheet {spreadsheet}")
    try:
        if str(sheet).isdigit():
            logger.info(f"sheet var is digit, so will open as an index")
            openned_sheet = openned_spreadsheet.get_worksheet(int(sheet))
        else:
            logger.info(f"sheet var is not a digit, so will open by name")
            openned_sheet = openned_spreadsheet.worksheet(str(sheet))
    except:
        logger.error(f"set_values failed to open sheet {sheet} in spreadsheet {spreadsheet}")
        return

    logger.info(f"writing values to sheet {sheet} in spreadsheet {spreadsheet}")
    try:
        openned_sheet.update_cell(row, column, str(value))  # need to use the 'USER-ENTERED' option so things like checkboxes don't turn into text
    except:
        logger.error("failed to update values")
        return

    logger.info(f"set_values finished")
    return



@lru_cache
def get_cell_indexes(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', value="value"):
    sheet_values = get_values(spreadsheet, sheet)
    return_dict = dict()
    return_dict['row'] = -1
    return_dict['column'] = -1
    return_dict['row_index'] = -1
    return_dict['column_index'] = -1

    logger.info(value)
    logger.info(sheet_values[13][3])
    

    for row_index in range(len(sheet_values)):
        try:
            column_index = sheet_values[row_index].index(str(value))
            
            return_dict['row'] = row_index + 1
            return_dict['column'] = column_index + 1
            return_dict['row_index'] = row_index
            return_dict['column_index'] = column_index

            logger.debug(f"{str(value)} found in [row {row_index}, column {column_index}] of the {sheet} sheet within the {spreadsheet} spreadsheet")
            return return_dict
        except:
            logger.debug(f"{str(value)} not found in row {row_index} of the {sheet} sheet within the {spreadsheet} spreadsheet")
            continue
    
    return return_dict



@lru_cache
def get_time_column(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', day_row=1, day_column=1, start_time="12am"):
    sheet_values = get_values(spreadsheet, sheet)
    
    time_row = int(day_row) + 1

    for column_index in range(int(day_column), len(sheet_values[time_row])):
        logger.debug(sheet_values[time_row][column_index])

        if str(sheet_values[time_row][column_index]).lower() == str(start_time).lower():
            logger.info(f"{start_time} is on column {column_index}")
            return column_index
    
    return -1



@lru_cache
def get_shift_type_row(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', shift_type='Ultimate'):
    sheet_values = get_values(spreadsheet, sheet)
    
    for row_index in range(len(sheet_values)):
        for column_index in range(len(sheet_values[row_index])):
            logger.debug(sheet_values[row_index][column_index])

            if str(shift_type).replace('-','').replace(' ', '').lower() in str(sheet_values[row_index][column_index]).replace('-','').replace(' ', '').lower():
                logger.info(f"{shift_type} is on row {row_index}")
                return row_index
    
    return -1



@lru_cache
def get_requester_row(spreadsheet=os.getenv('SHEET_SHIFT_SIGNUPS'), sheet='Sign Up', requester='nqztv'):
    sheet_values = get_values(spreadsheet, sheet)
    
    for row_index in range(15, len(sheet_values)):
        logger.info(sheet_values[row_index][2])
        if len(sheet_values[row_index][2].lower()) < 1:
            break

        if requester.lower() in sheet_values[row_index][2].lower():
            logger.info(f"{requester} is on row {row_index}")
            return row_index
        
    set_value(spreadsheet, sheet, row_index + 1, 3, requester)
    
    return row_index