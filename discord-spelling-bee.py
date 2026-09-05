import os
import discord
from discord.ext import commands
from discord.commands import bridge
import http.server
import threading

# 1. Fake Web Server for Render Port Check
def run_fake_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_fake_server, daemon=True).start()

# 2. Bot Initialization using Pycord's Command Bridge
intents = discord.Intents.default()
intents.message_content = True
bot = bridge.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")
serverData = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} and synced with Discord!")

# 3. Modern Today Command
@bot.bridge_command(description="Check today's Stats")
async def today(ctx):
    await ctx.defer(ephemeral=True)
    guildID = str(ctx.guild.id)
    
    if guildID not in serverData or 'channelID' not in serverData[guildID]:
        return await ctx.respond("Please use /set_channel first to initialize the bot.", ephemeral=True)
        
    await ctx.respond("Fetching your daily spelling bee stats...", ephemeral=True)

# 4. Modern Set Channel Command
@bot.bridge_command(description="Set the spelling bee channel")
async def set_channel(ctx):
    await ctx.defer(ephemeral=True)
    guildID = str(ctx.guild.id)
    serverData[guildID] = {"channelID": ctx.channel.id}
    await ctx.respond(f"Spelling Bee channel set to {ctx.channel.mention}!", ephemeral=True)

# 5. Global Start Switch
@bot.bridge_command(description="Start games manually")
async def start_games_now(ctx):
    await ctx.defer(ephemeral=True)
    await ctx.respond("Spun up game loops globally across channels!", ephemeral=True)

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No DISCORD_TOKEN found in environment variables.")
