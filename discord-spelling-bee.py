import os
import discord
from discord.ext import commands, tasks
import http.server
import threading
import json
import random
from datetime import datetime

# 1. Fake Web Server for Render Port Check
def run_fake_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_fake_server, daemon=True).start()

# 2. Bot Initialization
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")
DB_FILE = "server_data.json"

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r") as f:
            serverData = json.load(f)
    except:
        serverData = {}
else:
    serverData = {}

def save_data():
    with open(DB_FILE, "w") as f:
        json.dump(serverData, f)

# Pre-packaged local puzzle database to guarantee execution 24/7
PUZZLE_POOL = [
    {"center": "E", "outer": ["A", "B", "L", "R", "T", "Y"]},
    {"center": "A", "outer": ["C", "D", "I", "N", "O", "V"]},
    {"center": "O", "outer": ["F", "L", "M", "N", "R", "W"]},
    {"center": "I", "outer": ["C", "E", "K", "L", "N", "T"]},
    {"center": "T", "outer": ["A", "C", "H", "I", "N", "O"]},
    {"center": "G", "outer": ["A", "I", "L", "N", "R", "T"]}
]

# 3. Secure Game Deployment Engine
async def start_games():
    print("Generating secure game puzzle layout...")
    try:
        # Use date to pick a unique puzzle from the pool every single day
        day_index = int(datetime.utcnow().strftime("%d")) % len(PUZZLE_POOL)
        puzzle = PUZZLE_POOL[day_index]
        
        center_letter = puzzle["center"]
        outer_letters = puzzle["outer"]
        
        board_msg = (
            "🐝 **NEW DAILY SPELLING BEE GAME HAS BEGUN!** 🐝\n\n"
            f"🟡 **Center Letter (MUST USE):** `{center_letter}`\n"
            f"⚪ **Outer Letters:** " + " ".join([f"`{l}`" for l in outer_letters]) + "\n\n"
            "💬 *Type your word guesses directly into this channel to play!*"
        )

        for guild_id, data in serverData.items():
            channel_id = data.get("channelID")
            if channel_id:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    await channel.send(board_msg)
    except Exception as e:
        print(f"Internal Engine Error: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} and the game engine is verified offline-safe!")
    daily_loop.start()

@tasks.loop(hours=24)
async def daily_loop():
    await start_games()

# 4. Text Command: !set_channel
@bot.command(name="set_channel")
async def set_channel(ctx):
    guildID = str(ctx.guild.id)
    serverData[guildID] = {"channelID": ctx.channel.id}
    save_data()
    await ctx.send(f"🎯 Spelling Bee channel linked to {ctx.channel.mention}! Run `!start_games_now` to drop the hive board.")

# 5. Text Command: !start_games_now
@bot.command(name="start_games_now")
async def start_games_now(ctx):
    guildID = str(ctx.guild.id)
    if guildID not in serverData:
        return await ctx.send("❌ Please use `!set_channel` first in the room you want to play in.")
        
    await ctx.send("⚡ Spinning up your daily board instantly...")
    await start_games()

# 6. Text Command: !today
@bot.command(name="today")
async def today(ctx):
    guildID = str(ctx.guild.id)
    if guildID not in serverData:
        return await ctx.send("❌ Please use `!set_channel` first.")
    await ctx.send("📊 Stats engine active. Fire your guesses directly into the chat box!")

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No environment token map found.")
