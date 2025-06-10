import asyncio
import logging
import os
import json
from uuid import uuid4
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    InputFile
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# اطلاعات ثابت
TOKEN = '7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI'
ADMINS = [1476858288, 6998318486]
CHANNELS = ['@zappasmagz', '@magzsukhte']
BOT_USERNAME = 'maguz_sukhteabot'

# فایل‌های ذخیره‌سازی
USERS_FILE = 'users.json'
VIDEOS_FILE = 'videos.json'

# وضعیت ربات
bot_enabled = True

# لاگ
logging.basicConfig(level=logging.INFO)

# کمک‌کننده‌ها
def load_json(file):
    return json.load(open(file, 'r')) if os.path.exists(file) else {}

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f)

# رویداد شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_json(USERS_FILE)
    users[str(user.id)] = {"username": user.username}
    save_json(USERS_FILE, users)

    keyboard = []
    if user.id in ADMINS:
        keyboard = [
            [InlineKeyboardButton("ارسال ویدیو 📤", callback_data='send_video')],
            [InlineKeyboardButton("پنل ادمین 🛠", callback_data='admin_panel')]
        ]

    await update.message.reply_text(
        "سلام حاجی 👋",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# دکمه‌ها
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "send_video":
        await query.message.reply_text("🎥 لطفاً ویدیو را ارسال کن.")
    elif query.data == "admin_panel":
        if user_id not in ADMINS:
            await query.message.reply_text("⛔ دسترسی غیرمجاز.")
            return
        users = load_json(USERS_FILE)
        videos = load_json(VIDEOS_FILE)
        status = "روشن ✅" if bot_enabled else "خاموش ❌"
        await query.message.reply_text(
            f"🛠 پنل مدیریت\n\n📊 کاربران: {len(users)}\n🎬 ویدیوها: {len(videos)}\n🔌 وضعیت ربات: {status}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("روشن/خاموش ربات", callback_data="toggle_bot")],
                [InlineKeyboardButton("لیست کاربران 👥", callback_data="list_users")]
            ])
        )
    elif query.data == "toggle_bot":
        if user_id in ADMINS:
            bot_enabled = not bot_enabled
            status = "روشن ✅" if bot_enabled else "خاموش ❌"
            await query.message.reply_text(f"وضعیت ربات تغییر کرد: {status}")
    elif query.data == "list_users":
        users = load_json(USERS_FILE)
        text = "\n".join([f"{uid} - @{info['username']}" for uid, info in users.items()])
        await query.message.reply_text(f"👥 کاربران:\n{text or 'کاربری وجود ندارد.'}")
    elif query.data.startswith("check_"):
        _, video_id = query.data.split("_", 1)
        user = query.from_user
        member = await check_membership(user.id, context)
        if not member:
            await query.message.reply_text("❌ لطفاً در هر دو کانال عضو شوید.")
            return
        videos = load_json(VIDEOS_FILE)
        if video_id in videos:
            file_id = videos[video_id]
            msg = await query.message.reply_video(file_id)
            await asyncio.sleep(30)
            try:
                await msg.delete()
            except:
                pass
            await query.message.reply_text(
                "⏱ فیلم‌های ارسالی ربات بعد از 30 ثانیه از ربات پاک می‌شوند.\n\n✅ فیلم را در پی‌وی دوستان خود یا در پیام‌های ذخیره شده ارسال و بعد دانلود کنید."
            )
        else:
            await query.message.reply_text("❌ این ویدیو یافت نشد.")

# بررسی عضویت
async def check_membership(user_id, context):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

# دریافت ویدیو از ادمین
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    if not bot_enabled:
        await update.message.reply_text("⛔ ربات در حال حاضر خاموش است.")
        return

    user = update.effective_user
    if user.id not in ADMINS:
        return

    file_id = update.message.video.file_id
    video_id = str(uuid4())
    videos = load_json(VIDEOS_FILE)
    videos[video_id] = file_id
    save_json(VIDEOS_FILE, videos)

    link = f"https://t.me/{BOT_USERNAME}?start={video_id}"
    await update.message.reply_text(f"✅ ویدیو ذخیره شد. لینک:\n{link}")

# پردازش لینک‌های start
async def handle_start_with_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        video_id = context.args[0]
        user = update.effective_user
        member = await check_membership(user.id, context)

        if not member:
            await update.message.reply_text(
                "⛔ برای دریافت ویدیو ابتدا باید در کانال‌های زیر عضو شوید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("عضویت در کانال 1", url="https://t.me/zappasmagz")],
                    [InlineKeyboardButton("عضویت در کانال 2", url="https://t.me/magzsukhte")],
                    [InlineKeyboardButton("بررسی عضویت ✅", callback_data=f"check_{video_id}")]
                ])
            )
            return

        videos = load_json(VIDEOS_FILE)
        if video_id in videos:
            file_id = videos[video_id]
            msg = await update.message.reply_video(file_id)
            await asyncio.sleep(30)
            try:
                await msg.delete()
            except:
                pass
            await update.message.reply_text(
                "⏱ فیلم‌های ارسالی ربات بعد از 30 ثانیه از ربات پاک می‌شوند.\n\n✅ فیلم را در پی‌وی دوستان خود یا در پیام‌های ذخیره شده ارسال و بعد دانلود کنید."
            )
        else:
            await update.message.reply_text("❌ ویدیو یافت نشد.")
    else:
        await start(update, context)

# اجرای اصلی
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start_with_video))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
