import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
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

def dataframe_to_image(category, dataframe):
    display_df = dataframe.copy()

    column_names = {
        "amount": "Amount",
        "name": "Item",
        "price": "Price",
        "total_value": "Total Value"
    }
    display_df = display_df.rename(columns=column_names)

    if display_df.empty:
        display_df = display_df.reindex(columns=["Amount", "Item", "Price", "Total Value"])
        display_df.loc[0] = ["-", "No items", "-", "-"]
    else:
        for column in ["Amount", "Price", "Total Value"]:
            if column in display_df.columns:
                display_df[column] = display_df[column].map(lambda value: f"{int(value):,}")

    row_count = max(len(display_df), 1)
    fig_width = 10.5
    fig_height = max(2.4, row_count * 0.46 + 1.4)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    fig.patch.set_facecolor("#111827")
    ax.set_facecolor("#111827")
    ax.axis("off")

    fig.subplots_adjust(left=0.03, right=0.97, top=0.76, bottom=0.10)

    fig.suptitle(
        f"{category} Inventory",
        fontsize=22,
        fontweight="bold",
        color="#f8fafc",
        y=0.94
    )

    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc="center",
        loc="center",
        zorder=2,
        edges="closed"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.45)

    for (row, col), cell in table.get_celld().items():
        cell.set_linewidth(0.6)
        cell.set_edgecolor("#334155")

        if row == 0:
            cell.set_facecolor("#1e293b")
            cell.set_text_props(weight="bold", color="#f8fafc")
        else:
            if row % 2 == 0:
                cell.set_facecolor("#111827")
            else:
                cell.set_facecolor("#172033")

            cell.set_text_props(color="#e5e7eb")

            column_name = display_df.columns[col]
            if column_name == "Total Value":
                cell.set_text_props(weight="bold", color="#34d399")
            elif column_name == "Price":
                cell.set_text_props(color="#93c5fd")

    buffer = BytesIO()
    plt.savefig(
        buffer,
        format="png",
        dpi=170,
        facecolor="#111827",
        edgecolor="none",
        bbox_inches=None,
        pad_inches=0
    )
    plt.close(fig)

    buffer.seek(0)
    return buffer

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

    server_config = config.get(guild_id, {})
    server_config["trader_id"] = trader_id
    config[guild_id] = server_config
    save_config(config)

    await interaction.response.send_message(f"Trader ID set to {trader_id} for this server.", ephemeral=True)

@bot.tree.command(name="setcategories", description="Set the categories for inventory lookup")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(categories="Comma-separated list of categories to check (e.g., Flower,Plushie)")
async def set_categories(interaction: discord.Interaction, categories: str):
    if interaction.guild is None:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    category_list = [cat.strip() for cat in categories.split(",") if cat.strip()]
    
    if not category_list:
        await interaction.response.send_message("No valid categories provided. Please provide at least one category.", ephemeral=True)
        return
    
    config = load_config()
    guild_id = str(interaction.guild.id)

    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id]["categories"] = category_list
    save_config(config)

    await interaction.response.send_message(f"Categories set to {', '.join(category_list)} for this server.", ephemeral=True)

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

    config = load_config()
    guild_id = str(interaction.guild.id)

    server_config = config.get(guild_id, {})
    trader_id = server_config.get("trader_id")
    categories = server_config.get("categories", ["Flower", "Plushie"])

    if user_id not in keys:
        await interaction.followup.send("API key not found for your user. Please provide your API key using the `/setkey` command.", ephemeral=True)
        return
    
    api_key = decrypt_api_key(keys[user_id])

    if trader_id is None:
        await interaction.followup.send("Trader ID not set for this server. Please set it using the `/settrader` command.", ephemeral=True)
        return

    inventories = inventory(api_key, trader_id, categories)

    files = []
    max_sale_price = 0

    for category, dataframe in inventories.items():
        if "total_value" in dataframe.columns:
            max_sale_price += int(dataframe["total_value"].sum())

        image_buffer = dataframe_to_image(category, dataframe)

        files.append(discord.File(fp=image_buffer, filename=f"{category}_inventory.png"))

    response_content = (
        f"**Max sale price:** ${max_sale_price:,}\n"
        f"[Start a trade](https://www.torn.com/trade.php#step=start&userID={trader_id})"
    )
    
    if len(files) <= 10:
        await interaction.followup.send(
            content=response_content,
            files=files
        )
    else:
        await interaction.followup.send(
            content=(
                "Inventory images exceed Discord's limit of 10 files per message. "
                "Please check the images below.\n"
                f"{response_content}"
            ),
            files=files[:10]
        )

if __name__ == "__main__":
    bot.run(os.environ["DISCORD_BOT_TOKEN"])

