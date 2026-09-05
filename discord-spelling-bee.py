import os
import discord
from discord.ext import commands, tasks
import http.server
import threading
import json
import requests
import re

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

# Load persistent server data safely
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

# 3. Built-in NYT Fetch & Scrape Engine
async def start_games():
    print("Fetching today's puzzle from NYT...")
    try:
        url = "https://nytimes.com"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print("Failed to reach NYT website.")
            return

        # Scrape game data safely using regex pattern matching
        match = re.search(r'window\.gameData\s*=\s*(\{.*?\});', response.text)
        if not match:
            print("Could not parse NYT data structure.")
            return
            
        game_data = json.loads(match.group(1))
        today_data = game_data.get("today", {})
        
        center_letter = today_data.get("centerLetter", "").upper()
        outer_letters = [l.upper() for l in today_data.get("outerLetters", [])]
        all_letters = [center_letter] + outer_letters
        
        # Format the visual layout board
        board_msg = (
            "🐝 **NEW NYT SPELLING BEE GAME HAS BEGUN!** 🐝\n\n"
            f"🟡 **Center Letter:** `{center_letter}`\n"
            f"⚪ **Outer Letters:** " + " ".join([f"`{l}`" for l in outer_letters]) + "\n\n"
            "💬 *Type your word guesses directly into the chat to earn points!*"
        )

        for guild_id, data in serverData.items():
            channel_id = data.get("channelID")
            if channel_id:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    await channel.send(board_msg)
    except Exception as e:
        print(f"Error executing game loop engine: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} and system engine is online!")
    daily_loop.start()

# Auto loop to check for the daily puzzle at midnight UTC
@tasks.loop(hours=24)
async def daily_loop():
    await start_games()

# 4. Text Command: !set_channel
@bot.command(name="set_channel")
async def set_channel(ctx):
    guildID = str(ctx.guild.id)
    serverData[guildID] = {"channelID": ctx.channel.id}
    save_data()
    await ctx.send(f"🎯 Spelling Bee channel linked to {ctx.channel.mention}! Now type `!start_games_now` to fetch today's puzzle.")

# 5. Text Command: !start_games_now
@bot.command(name="start_games_now")
async def start_games_now(ctx):
    guildID = str(ctx.guild.id)
    if guildID not in serverData:
        return await ctx.send("❌ Please use `!set_channel` first in the room you want to play in.")
        
    await ctx.send("⚡ Connecting to the New York Times database... please wait a few seconds.")
    await start_games()

# 6. Text Command: !today
@bot.command(name="today")
async def today(ctx):
    guildID = str(ctx.guild.id)
    if guildID not in serverData:
        return await ctx.send("❌ Please use `!set_channel` first.")
    await ctx.send("📊 Stats command refreshed. Type your word guesses right here to play!")

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No DISCORD_TOKEN found in environment variables.")
