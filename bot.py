import os
import time
import json
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

TOKEN = os.environ.get("BOT_TOKEN")

KEY_FILE = "keys.json"

# ================= LOAD KEYS =================

def load_keys():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            data = json.load(f)
            return {int(k): v.encode() for k, v in data.items()}
    return {}

def save_keys():
    with open(KEY_FILE, "w") as f:
        json.dump({k: v.decode() for k, v in user_keys.items()}, f)

user_keys = load_keys()
user_mode = {}
user_time = {}


# ================= USER CIPHER =================

def get_cipher(uid):
    if uid not in user_keys:
        user_keys[uid] = Fernet.generate_key()
        save_keys()
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

    fake = "".join(random.choice(string.ascii_letters) for _ in range(16))

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


# ================= BUTTON =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    uid = q.from_user.id

    await q.answer()

    if q.data == "about":
        await q.edit_message_text(
            "EncryptXnoob Bot\nEncrypt • Decrypt • Protect Code"
        )
        return

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
        await update.message.reply_text("❌ Operation failed")


# ================= FILE =================

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.message.from_user.id

    doc = update.message.document
    file = await doc.get_file()

    temp_name = f"temp_{uid}_{doc.file_name}"

    await file.download_to_drive(temp_name)

    with open(temp_name, "rb") as f:
        data = f.read()

    mode = user_mode.get(uid, "encrypt")
    cipher = get_cipher(uid)

    try:

        if mode == "protect":
            if temp_name.endswith(".py"):
                result = protect_python(data)
            else:
                result = protect_js(data)
            name = "protected"

        elif mode == "decrypt":
            result = cipher.decrypt(data)
            name = "decrypted"

        else:
            result = cipher.encrypt(data)
            name = "encrypted"

        out_file = f"{name}_{uid}"

        with open(out_file, "wb") as f:
            f.write(result)

        await update.message.reply_document(InputFile(out_file))

    except:
        await update.message.reply_text("❌ File operation failed")

    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)
        if os.path.exists(out_file):
            os.remove(out_file)


# ================= RUN BOT =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))


if __name__ == "__main__":
    print("EncryptXnoob Running on Render 🚀")
    app.run_polling()
