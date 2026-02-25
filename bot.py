import os
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)
from cryptography.fernet import Fernet
from threading import Thread

# ========= Auto Key =========
cipher = Fernet(Fernet.generate_key())

# ========= Flask =========
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot Running!"

# ========= Telegram =========
TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send Python code. I will encrypt it 🔐"
    )

async def encrypt_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    encrypted = cipher.encrypt(text.encode()).decode()

    await update.message.reply_text(
        f"🔐 Encrypted Code:\n\n{encrypted}"
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, encrypt_code))

def run_bot():
    app.run_polling()

if __name__ == "__main__":
    Thread(target=run_bot).start()
    app_web.run(host="0.0.0.0", port=10000)
