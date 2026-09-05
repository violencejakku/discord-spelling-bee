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

# 2. Bot Initialization
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")
serverData = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="today", description="Check today's Stats")
async def today(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guildID = str(interaction.guild.id)
    
    if guildID not in serverData:
        return await interaction.followup.send("Please use /set_channel first to initialize the bot.", ephemeral=True)
        
    await interaction.followup.send("Fetching your daily spelling bee stats...", ephemeral=True)

@bot.tree.command(name="set_channel", description="Set the spelling bee channel")
async def set_channel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guildID = str(interaction.guild.id)
    serverData[guildID] = {"channelID": interaction.channel.id}
    await interaction.followup.send(f"Spelling Bee channel set to {interaction.channel.mention}!", ephemeral=True)

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No DISCORD_TOKEN found in environment variables.")

bot.run(DISCORD_TOKEN)
