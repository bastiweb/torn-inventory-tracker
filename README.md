# Torn Inventory Discord Bot

A Python Discord bot for checking Torn inventory values with trader-specific prices from the Weav3r price list API.

Users store their own Torn API key privately through Discord. Server admins configure which trader price list and inventory categories the server should use. Inventory results are sent back as dark-mode table images, one image per category.

## Features

- `/setkey` opens a private modal for saving or updating a user's Torn API key.
- `/settrader` lets a server admin configure the Weav3r trader ID.
- `/setcategories` lets a server admin configure which Torn inventory categories to check.
- `/inventory` fetches the user's configured inventory categories and returns image tables.
- `/inventory` also shows the max sale price across all returned categories.
- Item prices are loaded from `https://weav3r.dev/api/pricelist/{trader_id}`.
- User API keys are encrypted locally in `api_keys.json`.
- Server settings are stored locally in `server_config.json`.

## Project Files

- `sneaky_steve.py` - Discord bot, slash commands, config handling, encryption, and image rendering.
- `inventory_checker.py` - Torn and Weav3r API calls plus inventory value calculation.
- `requirements.txt` - Python dependencies.
- `.env.example` - Example environment variables.
- `api_keys.json` - Local encrypted user API key storage. Do not commit.
- `server_config.json` - Local server configuration. Do not commit.

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux / Raspberry Pi:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in the values:

```env
INVENTORY_BOT_SECRET=your_fernet_secret
DISCORD_BOT_TOKEN=your_discord_bot_token
```

Generate a Fernet encryption secret with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Keep this secret safe. If it changes, previously saved user API keys cannot be decrypted anymore and users will need to run `/setkey` again.

## Discord Bot Setup

When inviting the bot to a server, include these OAuth scopes:

```text
bot
applications.commands
```

The bot uses Discord slash commands. Global slash command updates can take a while to appear in Discord after restarting the bot.

## Running

```bash
python sneaky_steve.py
```

After the bot is online:

1. A server admin runs `/settrader` with the desired trader ID.
2. A server admin runs `/setcategories` with categories such as `Flower,Plushie`.
3. Each user runs `/setkey` to save their own Torn API key.
4. Users run `/inventory` to receive inventory value images.

## Category Configuration

Categories are configured per Discord server with `/setcategories`.

Example:

```text
Flower,Plushie,Drug,Other
```

The category names must match values accepted by the Torn inventory API.

## Local Data And Secrets

These files are intentionally ignored by Git:

```text
.env
api_keys.json
server_config.json
```

Do not publish your Discord bot token, Torn API keys, or `INVENTORY_BOT_SECRET`.

If a token or key was exposed, rotate it immediately.

## Raspberry Pi Notes

The bot can run on a Raspberry Pi without keeping VS Code open. Install Python, copy the project, create a virtual environment, install `requirements.txt`, create the `.env`, and run:

```bash
python sneaky_steve.py
```

For long-running use, run it with `tmux`, `screen`, or a `systemd` service.
