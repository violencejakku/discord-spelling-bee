import os
import discord
from discord.ext import commands, tasks
import http.server
import threading
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 1. RENDER PORT CHECK BYPASS (Keeps free server online)
def run_fake_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_fake_server, daemon=True).start()

# 2. BOT INITIALIZATION
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")
DB_FILE = "server_data.json"

if os.path.exists(DB_FILE):
    try:
         with open(DB_FILE, "r") as f: serverData = json.load(f)
    except: serverData = {}
else: serverData = {}

def save_data():
    with open(DB_FILE, "w") as f: json.dump(serverData, f)

# Global Live Game States
nyt_center = "G"
nyt_outer = ["A", "I", "L", "N", "R", "T"]
nyt_answers = []
found_words = []

# 3. LIVE NEW YORK TIMES SCRAPER ENGINE
async def fetch_live_nyt_puzzle():
    global nyt_center, nyt_outer, nyt_answers, found_words
    print("Connecting directly to New York Times...")
    try:
        url = "https://nytimes.com"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look into NYT's secret game script container tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'window.gameData' in script.string:
                    # Clean out the javascript wrapper boundaries to capture pure data
                    raw_js = script.string
                    json_str = raw_js.split('window.gameData =', 1)[1].strip().rstrip(';')
                    game_data = json.loads(json_str)
                    
                    today = game_data.get("today", {})
                    nyt_center = today.get("centerLetter", "G").upper()
                    nyt_outer = [l.upper() for l in today.get("outerLetters", ["A", "I", "L", "N", "R", "T"])]
                    nyt_answers = [w.upper() for w in today.get("answers", [])]
                    found_words = [] # Clear daily word cache tracking
                    print("Successfully extracted active NYT puzzle database!")
                    return True
    except Exception as e:
        print(f"Scraper error encountered: {e}")
    return False

# 4. GAME DESIGN PRINT ENGINE
async def display_game_board():
    board_msg = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🐝  **LIVE NYT SPELLING BEE GAME HAS BEGUN!**  🐝\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ **TODAY'S OFFICIAL NYT LETTERS:**\n"
        "┌───────────────────────────────┐\n"
        "│                               │\n"
        "│       🟡  **CENTER:** `{}` (Must Use)  │\n"
        "│                               │\n"
        "│       ⚪  **OUTER:**  {}  │\n"
        "│                               │\n"
        "└───────────────────────────────┘\n\n"
        "📝 **HOW TO EARN POINTS:**\n"
        "• Words must match NYT's official solution database.\n"
        "• Words must be **4+ letters** and use **{}**.\n\n"
        "💬 *Simply type your word guesses directly into this channel chat!*"
    ).format(nyt_center, " ".join([f"`{l}`" for l in nyt_outer]), nyt_center)

    for guild_id, data in serverData.items():
        channel = bot.get_channel(int(data.get("channelID", 0)))
        if channel: await channel.send(board_msg)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - NYT Scraper System Live!")
    await fetch_live_nyt_puzzle()
    daily_sync.start()

# Automatic puzzle updates at midnight UTC
@tasks.loop(hours=24)
async def daily_sync():
    if await fetch_live_nyt_puzzle():
        await display_game_board()

# 5. GUESS INTERCEPT ENGINE (Listens to text words in chat)
@bot.event
async def on_message(message):
    if message.author == bot.user: return

    guildID = str(message.guild.id)
    if guildID in serverData and message.channel.id == serverData[guildID]['channelID']:
        guess = message.content.strip().upper()
        
        if guess.startswith("!"):
            await bot.process_commands(message)
            return

        if nyt_center not in guess:
            await message.add_reaction("❌")
            return
        if len(guess) < 4:
            await message.add_reaction("⚠️")
            return

        # Score words against the scraped NYT answer key
        if guess in nyt_answers:
            if guess in found_words:
                await message.add_reaction("🔄") # Already found
            else:
                found_words.append(guess)
                await message.add_reaction("✅")
                points = 1 if len(guess) == 4 else len(guess)
                
                # Check for Pangram (uses all unique letters)
                if len(set(guess)) >= 7:
                    await message.channel.send(f"🎉 **PANGRAM!** {message.author.mention} discovered `{guess}` for **{points + 7} points**! 💥")
                else:
                    await message.channel.send(f"👍 Awesome! {message.author.mention} guessed `{guess}` for **{points} points**.")
        else:
            await message.add_reaction("❌") # Invalid NYT word

    await bot.process_commands(message)

# 6. CONFIGURATION MANAGEMENT COMMANDS
@bot.command(name="set_channel")
async def set_channel(ctx):
    guildID = str(ctx.guild.id)
    serverData[guildID] = {"channelID": ctx.channel.id}
    save_data()
    await ctx.send(f"🎯 Channel linked! Type `!start_games_now` to retrieve the current puzzle from NYT.")

@bot.command(name="start_games_now")
async def start_games_now(ctx):
    guildID = str(ctx.guild.id)
    if guildID not in serverData: return await ctx.send("❌ Use `!set_channel` first.")
    await ctx.send("⚡ Scraping live puzzle variables directly from NYT databases... please hold.")
    await fetch_live_nyt_puzzle()
    await display_game_board()

if TOKEN: bot.run(TOKEN)
