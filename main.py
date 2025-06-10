import logging
import os
import json
import random
import string
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, filters, ContextTypes, CallbackContext)

# اطلاعات اولیه
BOT_TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
BOT_USERNAME = "maguz_sukhteabot"
ADMINS = [1476858288, 6998318486]
CHANNELS = ["@zappasmagz", "@magzsukhte"]

# فایل ذخیره‌سازی ویدیوها و کاربران
VIDEOS_FILE = "videos.json"
USERS_FILE = "users.json"
STATE_FILE = "state.json"

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ذخیره در فایل

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

# بررسی عضویت در کانال‌ها
async def is_user_member(user_id, context):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# دکمه عضویت

def get_join_keyboard():
    buttons = [[InlineKeyboardButton("📢 عضویت در کانال ۱", url=f"https://t.me/{CHANNELS[0][1:]}")],
               [InlineKeyboardButton("📢 عضویت در کانال ۲", url=f"https://t.me/{CHANNELS[1][1:]}")],
               [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_membership")]]
    return InlineKeyboardMarkup(buttons)

# دکمه‌های اصلی

def get_main_keyboard(is_admin=False):
    buttons = [[InlineKeyboardButton("ارسال ویدیو 📤", callback_data="upload")]]
    if is_admin:
        buttons.append([InlineKeyboardButton("پنل ادمین 🛠", callback_data="admin")])
    return InlineKeyboardMarkup(buttons)

# شروع بات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USERS = load_json(USERS_FILE)
    USERS[str(user_id)] = True
    save_json(USERS_FILE, USERS)

    if update.message.text.startswith("/start "):
        video_id = update.message.text.split()[1]
        if not await is_user_member(user_id, context):
            await update.message.reply_text("⛔️ لطفاً ابتدا در هر دو کانال عضو شوید:", reply_markup=get_join_keyboard())
            return

        VIDEOS = load_json(VIDEOS_FILE)
        if video_id in VIDEOS:
            file_id = VIDEOS[video_id]
            sent = await context.bot.send_video(chat_id=user_id, video=file_id)

            await asyncio.sleep(30)
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=sent.message_id)
            except:
                pass

            await context.bot.send_message(chat_id=user_id,
                text="⏱ فیلم های ارسالی ربات بعد از 30ثانیه از ربات پاک میشوند.\n\n✅ فیلم را در پی وی دوستان خود یا در پیام های ذخیره شده ارسال و بعد دانلود کنید.")
        else:
            await update.message.reply_text("ویدیو پیدا نشد یا منقضی شده است.")
        return

    await update.message.reply_text("سلام حاجی 👋", reply_markup=get_main_keyboard(user_id in ADMINS))

# آپلود ویدیو
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return

    file_id = update.message.video.file_id
    video_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    VIDEOS = load_json(VIDEOS_FILE)
    VIDEOS[video_id] = file_id
    save_json(VIDEOS_FILE, VIDEOS)

    link = f"https://t.me/{BOT_USERNAME}?start={video_id}"
    await update.message.reply_text(
        f"✅ ویدیو ذخیره شد.\n\n📥 لینک: {link}"
    )

# دکمه‌ها
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "upload":
        if user_id in ADMINS:
            await query.message.reply_text("ویدیوی خود را ارسال کنید:")
    elif query.data == "admin":
        await show_admin_panel(update, context)
    elif query.data == "check_membership":
        if await is_user_member(user_id, context):
            await query.message.reply_text("✅ شما عضو شدید! روی لینک کلیک کنید یا دوباره استارت بزنید.")
        else:
            await query.message.reply_text("❌ هنوز عضو هر دو کانال نیستید.")

# پنل ادمین
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in ADMINS:
        return

    STATE = load_json(STATE_FILE)
    state = STATE.get("enabled", True)

    USERS = load_json(USERS_FILE)
    VIDEOS = load_json(VIDEOS_FILE)

    msg = f"🛠 پنل مدیریت ربات:\n\n"
    msg += f"👥 تعداد کاربران: {len(USERS)}\n"
    msg += f"🎬 ویدیوهای ذخیره شده: {len(VIDEOS)}\n"
    msg += f"🚦 وضعیت ربات: {'فعال ✅' if state else 'غیرفعال ❌'}"

    buttons = [
        [InlineKeyboardButton("🔴 خاموش کردن ربات" if state else "🟢 روشن کردن ربات", callback_data="toggle_bot")]
    ]
    await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons))

async def toggle_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in ADMINS:
        return

    STATE = load_json(STATE_FILE)
    current = STATE.get("enabled", True)
    STATE["enabled"] = not current
    save_json(STATE_FILE, STATE)

    status = "✅ روشن شد" if not current else "❌ خاموش شد"
    await query.message.reply_text(f"وضعیت ربات: {status}")

# راه‌اندازی برنامه
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(CallbackQueryHandler(toggle_bot, pattern="^toggle_bot$"))

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
