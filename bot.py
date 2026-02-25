import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)
from cryptography.fernet import Fernet
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("BOT_TOKEN")

# ===== keep alive (Render) =====
web = Flask(__name__)

@web.route("/")
def home():
    return "EncryptXnoob Running"

# ===== User Private Keys =====
user_keys = {}

def get_cipher(user_id):
    if user_id not in user_keys:
        user_keys[user_id] = Fernet.generate_key()
    return Fernet(user_keys[user_id])

# ===== Spam Protection =====
user_time = {}

def anti_spam(user_id):
    now = time.time()
    if user_id in user_time and now - user_time[user_id] < 3:
        return True
    user_time[user_id] = now
    return False

# ===== Buttons =====
def menu_buttons():
    keyboard = [
        [InlineKeyboardButton("🔐 Encrypt Text", callback_data="encrypt")],
        [InlineKeyboardButton("📂 Encrypt .py File", callback_data="file")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== Start Command =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to EncryptXnoob\n\n"
        "Send Python code or .py file to encrypt 🔐",
        reply_markup=menu_buttons(),
    )

# ===== Button Actions =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "about":
        await query.edit_message_text(
            "EncryptXnoob 🔐\nPrivate Python Encryption Bot"
        )

    elif query.data == "encrypt":
        await query.edit_message_text(
            "Send any Python text now."
        )

    elif query.data == "file":
        await query.edit_message_text(
            "Send .py file to encrypt."
        )

# ===== Text Encryption =====
async def encrypt_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if anti_spam(user_id):
        await update.message.reply_text("⏳ Slow down bro...")
        return

    cipher = get_cipher(user_id)

    encrypted = cipher.encrypt(update.message.text.encode()).decode()

    await update.message.reply_text(
        f"🔐 Encrypted:\n\n{encrypted}"
    )

# ===== File Encryption =====
async def encrypt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if anti_spam(user_id):
        await update.message.reply_text("⏳ Wait a moment...")
        return

    document = update.message.document

    if not document.file_name.endswith(".py"):
        await update.message.reply_text("❌ Send only .py file")
        return

    file = await document.get_file()
    path = f"{user_id}.py"

    await file.download_to_drive(path)

    cipher = get_cipher(user_id)

    with open(path, "rb") as f:
        data = f.read()

    encrypted = cipher.encrypt(data)

    enc_path = f"{user_id}_encrypted.txt"

    with open(enc_path, "wb") as f:
        f.write(encrypted)

    await update.message.reply_document(
        document=InputFile(enc_path),
        filename="encrypted_code.txt",
        caption="✅ File Encrypted 🔐",
    )

    os.remove(path)
    os.remove(enc_path)

# ===== Telegram Setup =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, encrypt_text))
app.add_handler(MessageHandler(filters.Document.ALL, encrypt_file))

def run_bot():
    app.run_polling()

if __name__ == "__main__":
    Thread(target=run_bot).start()
    web.run(host="0.0.0.0", port=10000)
