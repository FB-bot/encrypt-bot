import os
import time
import base64
import zlib
import random
import string
from threading import Thread
from flask import Flask

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

TOKEN = os.environ.get("BOT_TOKEN")

# ================= KEEP ALIVE =================

web = Flask(__name__)

@web.route("/")
def home():
    return "EncryptXnoob Running 🔐"


# ================= USER SYSTEM =================

user_keys = {}
user_mode = {}
user_time = {}

def get_cipher(uid):
    if uid not in user_keys:
        user_keys[uid] = Fernet.generate_key()
    return Fernet(user_keys[uid])


# ================= ANTI SPAM =================

def anti_spam(uid):
    now = time.time()
    if uid in user_time and now - user_time[uid] < 2:
        return True
    user_time[uid] = now
    return False


# ================= PROTECTORS =================

def protect_python(code):

    compressed = zlib.compress(code)
    encoded = base64.b64encode(compressed).decode()

    fake = "".join(random.choice(string.ascii_letters) for _ in range(18))

    protected = f"""
# EncryptXnoob Protected File

import base64,zlib
{fake}="{encoded}"
exec(zlib.decompress(base64.b64decode({fake})))
"""
    return protected.encode()


def protect_js(code):
    encoded = base64.b64encode(code).decode()
    protected = f'eval(atob("{encoded}"));'
    return protected.encode()


# ================= MENU =================

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 Encrypt", callback_data="encrypt")],
        [InlineKeyboardButton("🔓 Decrypt", callback_data="decrypt")],
        [InlineKeyboardButton("🛡 Protect Code", callback_data="protect")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ])


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.message.from_user.id
    user_mode[uid] = "encrypt"

    await update.message.reply_text(
        "👋 Welcome to EncryptXnoob 🔐\n\n"
        "Send text or file.\nChoose mode below.",
        reply_markup=menu()
    )


# ================= BUTTONS =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data == "encrypt":
        user_mode[uid] = "encrypt"
        await q.edit_message_text("🔐 Encrypt Mode Enabled")

    elif q.data == "decrypt":
        user_mode[uid] = "decrypt"
        await q.edit_message_text("🔓 Decrypt Mode Enabled")

    elif q.data == "protect":
        user_mode[uid] = "protect"
        await q.edit_message_text(
            "🛡 Protection Mode\nSend .py or .js file"
        )

    elif q.data == "about":
        await q.edit_message_text(
            "EncryptXnoob 🔐\nProfessional Code Protector Bot"
        )


# ================= TEXT =================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.message.from_user.id

    if anti_spam(uid):
        await update.message.reply_text("⏳ Slow down...")
        return

    cipher = get_cipher(uid)
    mode = user_mode.get(uid, "encrypt")

    try:
        if mode == "decrypt":
            text = cipher.decrypt(update.message.text.encode()).decode()
            await update.message.reply_text(f"🔓 Decrypted:\n\n{text}")
        else:
            enc = cipher.encrypt(update.message.text.encode()).decode()
            await update.message.reply_text(f"🔐 Encrypted:\n\n{enc}")

    except:
        await update.message.reply_text("❌ Failed")


# ================= FILE =================

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.message.from_user.id

    if anti_spam(uid):
        await update.message.reply_text("⏳ Wait...")
        return

    doc = update.message.document
    file = await doc.get_file()

    path = doc.file_name
    await file.download_to_drive(path)

    with open(path, "rb") as f:
        data = f.read()

    mode = user_mode.get(uid, "encrypt")
    cipher = get_cipher(uid)

    try:

        # ===== PROTECTION MODE =====
        if mode == "protect":

            if path.endswith(".py"):
                result = protect_python(data)
                name = "protected.py"

            elif path.endswith(".js"):
                result = protect_js(data)
                name = "protected.js"

            else:
                await update.message.reply_text("Only .py or .js allowed")
                return

        # ===== DECRYPT =====
        elif mode == "decrypt":
            result = cipher.decrypt(data)
            name = "decrypted.py"

        # ===== ENCRYPT =====
        else:
            result = cipher.encrypt(data)
            name = "encrypted.txt"

        out = f"{uid}_out"

        with open(out, "wb") as f:
            f.write(result)

        await update.message.reply_document(
            document=InputFile(out),
            filename=name,
            caption="✅ Done"
        )

        os.remove(out)

    except:
        await update.message.reply_text("❌ Operation failed")

    os.remove(path)


# ================= TELEGRAM =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))


def run_bot():
    app.run_polling()


# ================= RUN =================

if __name__ == "__main__":
    Thread(target=run_bot).start()
    web.run(host="0.0.0.0", port=10000)
