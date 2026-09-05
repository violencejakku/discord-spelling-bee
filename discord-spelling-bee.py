import os
import discord
from discord.ext import commands
import http.server
import threading

# 1. Fake Web Server for Render
def run_fake_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_fake_server, daemon=True).start()

# 2. Bot Initialization (Using standard intents)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")
serverData = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} and ready to play!")

# 3. Today Command (Rewritten to old text style to prevent crashes)
@bot.command(description="Check today's Stats")
async def today(ctx):
    await ctx.defer()
    guildID = str(ctx.guild.id)
    
    if guildID not in serverData:
        return await ctx.send("Please use !set_channel first to initialize the bot.")
        
    await ctx.send("Fetching your daily spelling bee stats...")

# 4. Set Channel Command
@bot.command(description="Set the spelling bee channel")
async def set_channel(ctx):
    await ctx.defer()
    guildID = str(ctx.guild.id)
    serverData[guildID] = {"channelID": ctx.channel.id}
    await ctx.send(f"Spelling Bee channel set to this room!")

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No DISCORD_TOKEN found in environment variables.")
