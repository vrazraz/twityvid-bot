# twityvid-bot

Telegram bot that downloads videos from Twitter/X and sends them back in chat. Access restricted to subscribers of a channel you specify via `CHANNEL` env variable.

## Features
- Downloads videos from twitter.com, x.com, vxtwitter.com, fxtwitter.com
- Checks channel subscription before processing
- 50 MB file size limit (Telegram Bot API restriction)
- Auto-cleanup of temporary files

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:
```
BOT_TOKEN=your_bot_token
CHANNEL=@yourchannel
```

The bot must be added as an admin (no special permissions needed) to the channel for subscription checks to work.

## Run

```bash
source venv/bin/activate
python3 bot.py
```

## Requirements
- Python 3.10+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed and available in PATH
