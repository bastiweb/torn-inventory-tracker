import discord
from discord.ext import commands
from discord import app_commands
import tabulate
import json
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from inventory_checker import inventory

load_dotenv()
KEY_FILE = "api_keys.json"
CONFIG_FILE = "server_config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    
    if os.path.getsize(CONFIG_FILE) == 0:
        return {}
    
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)
    
def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

def get_cipher():
    secret = os.environ["INVENTORY_BOT_SECRET"]
    return Fernet(secret.encode())

def encrypt_api_key(api_key):
    cipher = get_cipher()
    encrypted_key = cipher.encrypt(api_key.encode())
    return encrypted_key.decode()

def decrypt_api_key(encrypted_key):
    cipher = get_cipher()
    api_key = cipher.decrypt(encrypted_key.encode())
    return api_key.decode()

def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    
    if os.path.getsize(KEY_FILE) == 0:
        return {}
    
    with open(KEY_FILE, "r") as file:
        return json.load(file)
    
def save_keys(keys):
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file, indent=4)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

class ApiKeyModal(discord.ui.Modal, title="Enter your API Key"):
    api_key = discord.ui.TextInput(label="API Key", placeholder="Enter your Torn API Key here")

    async def on_submit(self, interaction: discord.Interaction):
        keys = load_keys()
        keys[str(interaction.user.id)] = encrypt_api_key(
            str(self.api_key.value).strip()
        )
        save_keys(keys)
        await interaction.response.send_message("API key saved successfully!", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'We have logged in as {bot.user}')

@bot.tree.command(name="settrader", description="Set the trader ID for price lookup")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(trader_id="The Torn trader ID to use for price lookup")
async def set_trader(interaction: discord.Interaction, trader_id: str):
    if interaction.guild is None:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    if not trader_id.isdigit():
        await interaction.response.send_message("Invalid trader ID. Please provide a numeric trader ID.", ephemeral=True)
        return
    
    config = load_config()
    guild_id = str(interaction.guild.id)

    config[guild_id] = {"trader_id": trader_id}
    save_config(config)

    await interaction.response.send_message(f"Trader ID set to {trader_id} for this server.", ephemeral=True)

@bot.tree.command(name="setkey", description="Set your Torn API key")
async def setkey(interaction: discord.Interaction):
    await interaction.response.send_modal(ApiKeyModal())


@bot.tree.command(name="inventory", description="Check your Torn inventory")
async def inventory_command(interaction: discord.Interaction):
    await interaction.response.defer()

    if interaction.guild is None:
            await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
            return
    
    keys = load_keys()
    user_id = str(interaction.user.id)

    if user_id not in keys:
        await interaction.followup.send("API key not found for your user. Please provide your API key using the `/setkey` command.", ephemeral=True)
        return
    
    api_key = decrypt_api_key(keys[user_id])

    config = load_config()
    
    guild_id = str(interaction.guild.id)
    

    trader_id = config.get(guild_id, {}).get("trader_id")
    if trader_id is None:
        await interaction.followup.send("Trader ID not set for this server. Please set it using the `/settrader` command.", ephemeral=True)
        return

    inventories = inventory(api_key, trader_id)
    messages = []

    for categorie, dataframe in inventories.items():
        table = tabulate.tabulate(
            dataframe, 
            headers='keys', 
            tablefmt='grid', 
            showindex=False, 
            intfmt=',',
            floatfmt=',.0f'
        )
        messages.append(f"```{categorie} Inventory:\n{table}```")
        
    await interaction.followup.send("\n".join(messages)+f"\n [Start a trade](https://www.torn.com/trade.php#step=start&userID={trader_id})")

bot.run(os.environ["DISCORD_BOT_TOKEN"])

