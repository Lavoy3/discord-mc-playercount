import os
import discord
import requests
from discord.ext import tasks, commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
SERVER_IP = os.getenv("SERVER_IP")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)

# Cache
last_display_text = None
status_message = None

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    update_status.start()

@tasks.loop(seconds=30)
async def update_status():
    global last_display_text, status_message
    try:
        # Fetch Minecraft server status
        url = f"https://api.mcstatus.io/v2/status/java/{SERVER_IP}"
        response = requests.get(url, timeout=5)
        data = response.json()

        # Determine what to display
        if not data.get("online"):
            display_text = "🔴 Server Offline"
        else:
            players_online = data["players"]["online"]
            players_max = data["players"]["max"]
            display_text = f"🟢 {players_online}/{players_max} players online"

        # Skip if nothing changed
        if display_text == last_display_text:
            print("⏳ No change in player count, skipping update")
            return

        # Update bot presence
        await client.change_presence(activity=discord.Game(name=display_text))

        # Update channel message
        channel = await client.fetch_channel(CHANNEL_ID)

        if status_message is None:
            # Try to find previous bot message
            async for msg in channel.history(limit=10):
                if msg.author == client.user:
                    status_message = msg
                    break
            if status_message is None:
                status_message = await channel.send("🔄 Loading status...")

        await status_message.edit(content=f"📊 **Server Status:**\n{display_text}")
        print(f"✅ Updated display: {display_text}")
        last_display_text = display_text

    except Exception as e:
        print(f"❌ Error updating status: {e}")

client.run(TOKEN)
