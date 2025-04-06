import telebot
import os
import subprocess
import glob
import requests

BOT_TOKEN = '8004343174:AAFoe0VCqBuR1WrTrcYDM4_UE76LRZ5im1c'  # 🔁 Replace with your Telegram bot token
bot = telebot.TeleBot(BOT_TOKEN)

MAX_SIZE_MB = 50  # Telegram upload limit for bots

def upload_to_pixeldrain(file_path):
    with open(file_path, 'rb') as f:
        r = requests.post('https://pixeldrain.com/api/file', files={'file': f})
        if r.status_code == 200:
            return "https://pixeldrain.com/u/" + r.json()['id']
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 Send me a YouTube link to download as MP3.")

@bot.message_handler(func=lambda msg: 'youtu' in msg.text)
def handle_youtube_link(message):
    url = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "🎧 Downloading MP3, please wait...")

    try:
        output_template = "%(title).100s.%(ext)s"
        cmd = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "-o", output_template,
            url
        ]
        subprocess.run(cmd, check=True)

        files = sorted(glob.glob("*.mp3"), key=os.path.getmtime, reverse=True)
        if not files:
            bot.send_message(chat_id, "❌ Download failed. No MP3 found.")
            return

        filename = files[0]
        size_mb = os.path.getsize(filename) / (1024 * 1024)

        if size_mb > MAX_SIZE_MB:
            bot.send_message(chat_id, "📤 File too large, uploading to cloud...")
            link = upload_to_pixeldrain(filename)
            if link:
                bot.send_message(chat_id, f"✅ MP3 uploaded: [Click to Download]({link})", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, "❌ Upload failed.")
        else:
            with open(filename, 'rb') as f:
                bot.send_audio(chat_id, f, caption="✅ Here is your MP3!")

    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Error: {str(e)}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

bot.polling()
