import discord
from discord.ext import commands
import tabulate
import json
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from inventory_checker import inventory

load_dotenv()
KEY_FILE = "api_keys.json"

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

@bot.tree.command(name="setkey", description="Set your Torn API key")
async def setkey(interaction: discord.Interaction):
    await interaction.response.send_modal(ApiKeyModal())


@bot.tree.command(name="inventory", description="Check your Torn inventory")
async def inventory_command(interaction: discord.Interaction):
    await interaction.response.defer()

    keys = load_keys()
    user_id = str(interaction.user.id)

    if user_id not in keys:
        await interaction.followup.send("API key not found for your user. Please provide your API key using the `/setkey` command.", ephemeral=True)
        return
    
    api_key = decrypt_api_key(keys[user_id])

    inventories = inventory(api_key)
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
        
    await interaction.followup.send("\n".join(messages)+"\n [Start a trade](https://www.torn.com/trade.php#step=start&userID=4253363)")

bot.run(os.environ["DISCORD_BOT_TOKEN"])

