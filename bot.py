import os
import time
import base64
import zlib
import random
import string

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
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ])


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    user_mode[uid] = "encrypt"

    await update.message.reply_text(
        "👋 Welcome to EncryptXnoob 🔐",
        reply_markup=menu()
    )


# ================= BUTTONS =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    user_mode[uid] = q.data
    await q.edit_message_text(f"{q.data.upper()} MODE ENABLED")


# ================= TEXT =================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.message.from_user.id

    if anti_spam(uid):
        return

    cipher = get_cipher(uid)
    mode = user_mode.get(uid, "encrypt")

    try:
        if mode == "decrypt":
            text = cipher.decrypt(update.message.text.encode()).decode()
            await update.message.reply_text(text)
        else:
            enc = cipher.encrypt(update.message.text.encode()).decode()
            await update.message.reply_text(enc)
    except:
        await update.message.reply_text("Operation failed")


# ================= FILE =================

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


# ================= TELEGRAM =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))


# ================= RUN =================

if __name__ == "__main__":
    print("EncryptXnoob Running on Railway 🚀")
    app.run_polling()
