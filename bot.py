#!/usr/bin/env python3
"""
Twitter/X Video Downloader Telegram Bot
Скачивает видео из Twitter/X и отправляет в Telegram.
Доступ только для подписчиков @prouxui.
"""

import asyncio
import os
import re
import subprocess
import tempfile
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL = os.environ.get("CHANNEL", "@prouxui")
TWITTER_RE = re.compile(r'https?://(?:twitter\.com|x\.com|vxtwitter\.com|fxtwitter\.com)/\S+')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)


async def check_subscription(bot, user_id: int) -> bool:
    """Check if user is subscribed to the channel."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return member.status in ('member', 'administrator', 'creator')
    except Exception as e:
        log.warning(f"Subscription check failed for {user_id}: {e}")
        return False


def download_video(url: str, output_dir: str) -> str | None:
    """Download video using yt-dlp, return file path or None."""
    # Normalize URL
    url = re.sub(r'vxtwitter\.com|fxtwitter\.com|twitter\.com', 'x.com', url)
    
    output_template = os.path.join(output_dir, 'video.%(ext)s')
    cmd = [
        'yt-dlp',
        '-f', 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b',
        '--merge-output-format', 'mp4',
        '--no-playlist',
        '--max-filesize', '50m',
        '-o', output_template,
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            log.error(f"yt-dlp error: {result.stderr}")
            return None
        
        # Find the output file
        for f in os.listdir(output_dir):
            if f.startswith('video.'):
                return os.path.join(output_dir, f)
        return None
    except subprocess.TimeoutExpired:
        log.error("yt-dlp timed out")
        return None
    except Exception as e:
        log.error(f"Download error: {e}")
        return None


async def handle_message(update: Update, context):
    """Handle incoming messages with Twitter/X links."""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    match = TWITTER_RE.search(text)
    
    if not match:
        await update.message.reply_text("Отправь ссылку на видео из Twitter/X 🐦")
        return
    
    user_id = update.message.from_user.id
    
    # Check subscription
    if not await check_subscription(context.bot, user_id):
        await update.message.reply_text("🔒 Подпишись на @prouxui чтобы использовать бота")
        return
    
    url = match.group(0)
    wait_msg = await update.message.reply_text("⏳ Скачиваю видео...")
    
    # Download in thread pool
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = await asyncio.get_event_loop().run_in_executor(
            None, download_video, url, tmpdir
        )
        
        if not file_path:
            await wait_msg.edit_text("❌ Не удалось скачать видео. Возможно, в твите нет видео или оно слишком большое (>50 МБ)")
            return
        
        # Check file size (Telegram limit 50MB for bots)
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > 50:
            await wait_msg.edit_text(f"❌ Видео слишком большое ({size_mb:.0f} МБ). Лимит Telegram — 50 МБ")
            return
        
        try:
            with open(file_path, 'rb') as f:
                await update.message.reply_video(
                    video=f,
                    supports_streaming=True,
                    read_timeout=120,
                    write_timeout=120,
                )
            await wait_msg.delete()
        except Exception as e:
            log.error(f"Send error: {e}")
            await wait_msg.edit_text("❌ Ошибка при отправке видео")


async def start(update: Update, context):
    await update.message.reply_text(
        "👋 Отправь ссылку на твит с видео — я скачаю и пришлю!\n\n"
        "Поддерживаются: twitter.com, x.com, vxtwitter.com, fxtwitter.com\n\n"
        "🔒 Доступно только подписчикам @prouxui"
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    log.info("Bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
