import os
import discord
from discord.ext import commands
import http.server
import threading

# 1. Fake Web Server for Render Port Check
def run_fake_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_fake_server, daemon=True).start()

# 2. Bot Initialization using standard discord.py
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")
serverData = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} and ready for text commands!")

# 3. Text Command: !set_channel
@bot.command(name="set_channel", description="Set the spelling bee channel")
async def set_channel(ctx):
    guildID = str(ctx.guild.id)
    serverData[guildID] = {"channelID": ctx.channel.id}
    await ctx.send(f"Spelling Bee channel set to this room! Now use !start_games_now to begin.")

# 4. Text Command: !start_games_now
@bot.command(name="start_games_now", description="Start games manually")
async def start_games_now(ctx):
    guildID = str(ctx.guild.id)
    if guildID not in serverData:
        return await ctx.send("Please use !set_channel first to initialize this room.")
        
    await ctx.send("Spinning up daily spelling bee game data loops...")

# 5. Text Command: !today
@bot.command(name="today", description="Check today's Stats")
async def today(ctx):
    guildID = str(ctx.guild.id)
    if guildID not in serverData:
        return await ctx.send("Please use !set_channel first to initialize this room.")
        
    await ctx.send("Fetching your live daily spelling bee stats...")

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No DISCORD_TOKEN found in environment variables.")
