import os
from pathlib import Path

DISCORD_TOKEN = os.getenv("TOKEN", "")
assert DISCORD_TOKEN != "", "MISSING DISCORD_TOKEN"

CREDENTIALS_FILENAME = "credentials.json"
assert Path.exists(CREDENTIALS_FILENAME), "MISSING CREDENTIALS FILE"

SHEET_SHIFT_SIGNUPS = os.getenv("SHEET_SHIFT_SIGNUPS")
SHEET_SHIFT_SIGNUPS_SIGNUPS_TAB = "Sign Up"


# Function, not a constant. Needs to evaluate at run-time.
def get_cog_files():
    return os.listdir("./cogs")
