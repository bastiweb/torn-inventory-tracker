# Torn Inventory Discord Bot

A small Python Discord bot for checking Torn inventory values for flowers and plushies. Users can save their Torn API key through Discord, then request a formatted inventory value table.

## Features

- `/setkey` opens a private modal for storing a Torn API key.
- `/inventory` fetches the user's Torn flower and plushie inventory.
- Item prices are loaded from the Weav3r price list API.
- API keys are encrypted locally in `api_keys.json`.

## Setup

1. Create and activate a virtual environment.
2. Install the required packages:

```bash
pip install discord.py requests pandas tabulate python-dotenv cryptography
```

3. Copy `.env.example` to `.env`.
4. Add your Discord bot token and an encryption secret:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
INVENTORY_BOT_SECRET=your_fernet_secret
```

Generate a Fernet secret with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Running

```bash
python sneaky_steve.py
```

When the bot is online, use `/setkey` in Discord first, then `/inventory` to check inventory values.

## Notes

- `.env` and `api_keys.json` are local secret files and should not be committed.
- The inventory checker currently focuses on `Flower` and `Plushie` categories.
