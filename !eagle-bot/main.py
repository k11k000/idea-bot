import disnake
from disnake.ext import commands
import os
import sys
import methods
import datetime
import sqlite3
from dotenv import load_dotenv

activity = disnake.Activity(
    name="/info",
    type=disnake.ActivityType.watching,
)

bot = commands.Bot(
    intents=disnake.Intents.all(),
    activity=activity,
    default_contexts=disnake.InteractionContextTypes(guild=True)
)

os.system('cls' if sys.platform == 'win32' else 'clear')
print("-------------------------------------------")

@bot.event
async def on_ready():
    with sqlite3.connect("ideas.db") as db:
        cursor = db.cursor()
        methods.startprint("BOT")

        cursor.execute("""CREATE TABLE IF NOT EXISTS ideas (
            id int,
            author_id int,
            name text,
            description text,
            likes int,
            dislikes int,
            voted text,
            answer text
        )""")

        db.commit()

try:
    load_dotenv("config.env")
except:
    raise ValueError("Не найден файл config.env")

token = os.getenv("TOKEN")
if token:
    bot.load_extensions('cogs')
    bot.run(token)
else:
    raise ValueError("Не найден TOKEN в config.env")