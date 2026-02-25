import os
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler
)
from cryptography.fernet import Fernet

# ========= Flask Server =========
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running!"

# ========= Encryption =========
key = b'YOUR_SAVED_KEY'
cipher = Fernet(key)

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send Python code, I will encrypt it 🔐"
    )

async def encrypt_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    encrypted = cipher.encrypt(code.encode()).decode()

    await update.message.reply_text(
        f"🔐 Encrypted Code:\n\n{encrypted}"
    )

telegram_app = ApplicationBuilder().token(TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, encrypt_code)
)

def run_bot():
    telegram_app.run_polling()

if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_bot).start()
    app_web.run(host="0.0.0.0", port=10000)
