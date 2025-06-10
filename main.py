import os
import json
import asyncio
import logging
import random
from uuid import uuid4
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler

# پیکربندی لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# توکن و تنظیمات
TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
ADMIN_IDS = [1476858288, 6998318486]
CHANNEL_IDS = ['@zappasmagz', '@magzsukhte']
BOT_USERNAME = "@maguz_sukhteabot"

# فایل‌های دیتابیس ساده
VIDEO_DB_FILE = "videos.json"
USER_DB_FILE = "users.json"

# حالت فعال یا غیرفعال بودن ربات
bot_enabled = True

# بررسی وجود فایل دیتابیس
if not os.path.exists(VIDEO_DB_FILE):
    with open(VIDEO_DB_FILE, "w") as f:
        json.dump({}, f)
if not os.path.exists(USER_DB_FILE):
    with open(USER_DB_FILE, "w") as f:
        json.dump({}, f)

# ذخیره و بارگذاری ویدیوها

def save_video(video_id, file_id):
    with open(VIDEO_DB_FILE, "r") as f:
        data = json.load(f)
    data[video_id] = file_id
    with open(VIDEO_DB_FILE, "w") as f:
        json.dump(data, f)

def get_video_file(video_id):
    with open(VIDEO_DB_FILE, "r") as f:
        data = json.load(f)
    return data.get(video_id)

# ذخیره کاربران

def save_user(user_id):
    with open(USER_DB_FILE, "r") as f:
        users = json.load(f)
    users[str(user_id)] = str(datetime.now())
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)

def get_user_count():
    with open(USER_DB_FILE, "r") as f:
        users = json.load(f)
    return len(users)

# بررسی عضویت در کانال‌ها
async def check_membership(user_id, context):
    for channel in CHANNEL_IDS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# پیام خوش‌آمد و دکمه‌ها
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    save_user(user_id)
    if not await check_membership(user_id, context):
        keyboard = [[InlineKeyboardButton("عضویت در کانال 1", url=f"https://t.me/{CHANNEL_IDS[0][1:]}"),
                     InlineKeyboardButton("عضویت در کانال 2", url=f"https://t.me/{CHANNEL_IDS[1][1:]}")]]
        await update.message.reply_text("برای دریافت ویدیو ابتدا در کانال‌ها عضو شوید.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await update.message.reply_text("به ربات خوش آمدید.")

# دریافت و ارسال ویدیو از لینک خاص
async def handle_video_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    save_user(user_id)

    if not bot_enabled:
        await update.message.reply_text("ربات غیرفعال است.")
        return

    parts = update.message.text.split(" ")
    if len(parts) != 2:
        await update.message.reply_text("لینک نامعتبر است.")
        return

    video_id = parts[1]
    file_id = get_video_file(video_id)

    if not file_id:
        await update.message.reply_text("ویدیو یافت نشد.")
        return

    if not await check_membership(user_id, context):
        keyboard = [[InlineKeyboardButton("عضویت در کانال 1", url=f"https://t.me/{CHANNEL_IDS[0][1:]}"),
                     InlineKeyboardButton("عضویت در کانال 2", url=f"https://t.me/{CHANNEL_IDS[1][1:]}")]]
        await update.message.reply_text("برای دریافت ویدیو ابتدا در کانال‌ها عضو شوید.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    sent = await update.message.reply_video(file_id)
    await asyncio.sleep(30)
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent.message_id)

    await update.message.reply_text("⏱ فیلم های ارسالی ربات بعد از 30ثانیه از ربات پاک میشوند.\n\n✅ فیلم را در پی وی دوستان خود یا در پیام های ذخیره شده ارسال و بعد دانلود کنید.️")

# ادمین ارسال ویدیو
async def receive_video(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    video = update.message.video
    if not video:
        await update.message.reply_text("لطفاً یک ویدیو ارسال کنید.")
        return
    video_id = str(uuid4())[:8]
    save_video(video_id, video.file_id)
    await update.message.reply_text(f"✅ ویدیو ذخیره شد. لینک:\n\nhttps://t.me/{BOT_USERNAME}?start={video_id}")

# پنل ادمین
async def admin_panel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    keyboard = [
        [InlineKeyboardButton("📊 آمار کاربران", callback_data="stats")],
        [InlineKeyboardButton("🔴 خاموش کردن ربات" if bot_enabled else "🟢 روشن کردن ربات", callback_data="toggle")]
    ]
    await update.message.reply_text("🎛 پنل مدیریت:", reply_markup=InlineKeyboardMarkup(keyboard))

# کنترل پنل ادمین
async def admin_callback(update: Update, context: CallbackContext):
    global bot_enabled
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in ADMIN_IDS:
        return
    await query.answer()
    if query.data == "toggle":
        bot_enabled = not bot_enabled
        await query.edit_message_text("✅ ربات اکنون {} است.".format("فعال" if bot_enabled else "غیرفعال"))
    elif query.data == "stats":
        count = get_user_count()
        await query.edit_message_text(f"👤 تعداد کاربران: {count}")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.Regex(r"^/start "), handle_video_request))
    app.add_handler(MessageHandler(filters.VIDEO, receive_video))

    print("ربات آماده اجرا است.")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
