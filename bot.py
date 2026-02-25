import os
import time
import base64
import zlib
import random
import string
from flask import Flask, request

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from cryptography.fernet import Fernet

# ================= CONFIG =================

TOKEN = os.environ.get("8710925616:AAG2DYwGuusWMrfQDgcNdwGbKc73SK4DPUk")
APP_URL = os.environ.get("https://encrypt-bot-1.onrender.com")

# ================= USER SYSTEM =================

user_keys = {}
user_mode = {}
user_time = {}

def get_cipher(uid):
    if uid not in user_keys:
        user_keys[uid] = Fernet.generate_key()
    return Fernet(user_keys[uid])

def anti_spam(uid):
    now = time.time()
    if uid in user_time and now - user_time[uid] < 2:
        return True
    user_time[uid] = now
    return False

# ================= PROTECT =================

def protect_python(code):
    compressed = zlib.compress(code)
    encoded = base64.b64encode(compressed).decode()
    fake = "".join(random.choice(string.ascii_letters) for _ in range(18))

    protected = f"""
import base64,zlib
{fake}="{encoded}"
exec(zlib.decompress(base64.b64decode({fake})))
"""
    return protected.encode()

def protect_js(code):
    encoded = base64.b64encode(code).decode()
    return f'eval(atob("{encoded}"));'.encode()

# ================= MENU =================

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 Encrypt", callback_data="encrypt")],
        [InlineKeyboardButton("🔓 Decrypt", callback_data="decrypt")],
        [InlineKeyboardButton("🛡 Protect Code", callback_data="protect")],
    ])

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    user_mode[uid] = "encrypt"
    await update.message.reply_text(
        "👋 EncryptXnoob Ready 🔐",
        reply_markup=menu()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()
    user_mode[uid] = q.data
    await q.edit_message_text(f"{q.data.upper()} MODE ENABLED")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.message.from_user.id

    if anti_spam(uid):
        return

    cipher = get_cipher(uid)
    mode = user_mode.get(uid, "encrypt")

    if mode == "decrypt":
        try:
            text = cipher.decrypt(update.message.text.encode()).decode()
            await update.message.reply_text(text)
        except:
            await update.message.reply_text("Decrypt failed")
    else:
        enc = cipher.encrypt(update.message.text.encode()).decode()
        await update.message.reply_text(enc)

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.message.from_user.id
    doc = update.message.document
    file = await doc.get_file()

    path = doc.file_name
    await file.download_to_drive(path)

    with open(path, "rb") as f:
        data = f.read()

    mode = user_mode.get(uid, "encrypt")
    cipher = get_cipher(uid)

    if mode == "protect":
        result = protect_python(data) if path.endswith(".py") else protect_js(data)
        name = "protected"
    elif mode == "decrypt":
        result = cipher.decrypt(data)
        name = "decrypted"
    else:
        result = cipher.encrypt(data)
        name = "encrypted"

    with open(name, "wb") as f:
        f.write(result)

    await update.message.reply_document(InputFile(name))
    os.remove(path)
    os.remove(name)

# ================= TELEGRAM APP =================

telegram_app = ApplicationBuilder().token(TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(buttons))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
telegram_app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

# ================= FLASK WEBHOOK =================

web = Flask(__name__)

@web.route("/")
def home():
    return "EncryptXnoob Alive"

@web.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK"

# ================= START =================

if __name__ == "__main__":
    telegram_app.bot.set_webhook(f"{APP_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)
