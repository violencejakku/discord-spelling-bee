import os
import discord
from discord.ext import commands, tasks
import http.server
import threading
import json
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

# 3. ROTATING PUZZLE DATABASE
# Each index maps to a different calendar day rotation slot
PUZZLE_LIBRARY = [
    {
        "center": "G", "outer": ["A", "I", "L", "N", "R", "T"],
        "answers": ["ALIGN", "ALIGNING", "ANGLING", "GAIN", "GAINING", "GAIT", "GALA", "GALL", "GALLING", "GANG", "GANGING", "GIANT", "GILL", "GILT", "GINNING", "GLAD", "GLINT", "GLINTING", "GNARL", "GNARLING", "GNAT", "GRAIL", "GRAIN", "GRAINING", "GRANT", "GRANTING", "GRATING", "GRIN", "GRINING", "GRIT", "TAILGATING", "TRAILING", "TRAINING"]
    },
    {
        "center": "E", "outer": ["A", "B", "L", "R", "T", "Y"],
        "answers": ["ABLE", "ALERT", "ALTER", "BARE", "BARLEY", "BARTENDER", "BEAR", "BEARD", "BEAT", "BEET", "BEER", "BETRAY", "BLEAT", "EARL", "EARLY", "EARN", "LATE", "LATER", "LAYER", "LEATHER", "TEAL", "TEAR", "TREE", "YEAR", "YEARTY"]
    },
    {
        "center": "O", "outer": ["C", "D", "I", "N", "R", "W"],
        "answers": ["CROW", "CROWD", "CROWDING", "CORN", "COWBIRE", "COWARD", "DOOR", "DOWN", "DOWNWARD", "ICON", "INDOOR", "IRON", "NORDIC", "WINDROW", "WORD", "WORM", "WORN"]
    },
    {
        "center": "I", "outer": ["C", "E", "K", "L", "N", "T"],
        "answers": ["CEILING", "CLICK", "CLIENT", "CLINIC", "CLINK", "ELITE", "ICECLINK", "ICICLE", "INKLING", "KICK", "KICKING", "KILT", "KINETIC", "KNIT", "KNITTING", "LICE", "LICK", "LICKING", "LINE", "LINEN", "LINING", "LINK", "LINKING", "LINT", "LITTLE", "NICK", "NICKEL", "TICK", "TICKET", "TICKING", "TILT", "TILTING", "TINGLE", "TINGLING"]
    }
]

found_words = []
current_puzzle = PUZZLE_LIBRARY[0]

# 4. Clean Formatting Board Layout
async def start_games():
    global found_words, current_puzzle
    found_words = [] # Reset found pool for the day
    
    # Calculate a unique index based on the day of the month to pick a puzzle
    day_of_month = int(datetime.utcnow().strftime("%d"))
    puzzle_index = day_of_month % len(PUZZLE_LIBRARY)
    current_puzzle = PUZZLE_LIBRARY[puzzle_index]
    
    c = current_puzzle["center"]
    o = current_puzzle["outer"]
    
    board_msg = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🐝  **NEW DAILY SPELLING BEE GAME HAS BEGUN!**  🐝\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ **THE LETTERS TODAY ARE:**\n"
        "┌───────────────────────────────┐\n"
        "│                               │\n"
        "│       🟡  **CENTER:** `{}` (Must Use)  │\n"
        "│                               │\n"
        "│       ⚪  **OUTER:**  {}  │\n"
        "│                               │\n"
        "└───────────────────────────────┘\n\n"
        "📝 **HOW TO PLAY:**\n"
        "• Words must contain at least **4 letters**.\n"
        "• Words **MUST** use the center letter **{}**.\n"
        "• Letters can be used more than once.\n\n"
        "💬 *Simply type your word guesses directly into this channel chat!*"
    ).format(c, " ".join([f"`{l}`" for l in o]), c)

    for guild_id, data in serverData.items():
        channel_id = data.get("channelID")
        if channel_id:
            channel = bot.get_channel(int(channel_id))
            if channel:
                await channel.send(board_msg)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} and system engine is online!")
    
    # This guarantees the bot picks the correct daily puzzle the exact second it boots up!
    day_of_month = int(datetime.utcnow().strftime("%d"))
    puzzle_index = day_of_month % len(PUZZLE_LIBRARY)
    global current_puzzle
    current_puzzle = PUZZLE_LIBRARY[puzzle_index]
    
    daily_scheduler.start()

# 5. Background Task: Automatically runs midnight check
@tasks.loop(minutes=30)
async def daily_scheduler():
    now = datetime.utcnow()
    # If it is between 12:00 AM and 12:30 AM UTC, rotate the letters automatically
    if now.hour == 0 and now.minute < 30:
        print("Midnight UTC reached! Rotating letters...")
        await start_games()

# 6. WATCHER ENGINE: Listens to text guesses in chat
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    guildID = str(message.guild.id)
    if guildID in serverData and message.channel.id == serverData[guildID]['channelID']:
        guess = message.content.strip().upper()
        
        if guess.startswith("!"):
            await bot.process_commands(message)
            return

        c_letter = current_puzzle["center"]
        if c_letter not in guess:
            await message.add_reaction("❌")
            return

        if len(guess) < 4:
            await message.add_reaction("⚠️")
            return

        if guess in current_puzzle["answers"]:
            if guess in found_words:
                await message.add_reaction("🔄")
            else:
                found_words.append(guess)
                await message.add_reaction("✅")
                points = 1 if len(guess) == 4 else len(guess)
                
                unique_letters = set(guess)
                if len(unique_letters) >= 7:
                    await message.channel.send(f"🎉 **PANGRAM!** {message.author.mention} found `{guess}` for **{points + 7} points**! 💥")
                else:
                    await message.channel.send(f"👍 Perfect! {message.author.mention} found `{guess}` for **{points} points**.")
        else:
            await message.add_reaction("❌")

    await bot.process_commands(message)

# 7. Setup Commands Layout
@bot.command(name="set_channel")
async def set_channel(ctx):
    guildID = str(ctx.guild.id)
    serverData[guildID] = {"channelID": ctx.channel.id}
    save_data()
    await ctx.send(f"🎯 Channel linked successfully! Type `!start_games_now` to build the game frame.")

@bot.command(name="start_games_now")
async def start_games_now(ctx):
    guildID = str(ctx.guild.id)
    if guildID not in serverData:
        return await ctx.send("❌ Use `!set_channel` first.")
    await start_games()

@bot.command(name="today")
async def today(ctx):
    guildID = str(ctx.guild.id)
    if guildID not in serverData:
        return await ctx.send("❌ Use `!set_channel` first.")
    await ctx.send(f"📊 Words found so far today: `{len(found_words)}` total words.")

if TOKEN:
    bot.run(TOKEN)
