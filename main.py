import json
import os
import asyncio
from uuid import uuid4
from datetime import datetime

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# تنظیمات ادمین و توکن
ADMINS = [1476858288, 6998318486]
TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
CHANNELS = ["@zappasmagz", "@magzsukhte"]
BOT_USERNAME = "maguz_sukhteabot"

# فایل ذخیره اطلاعات
VIDEO_FILE = "videos.json"
USER_FILE = "users.json"


# ایجاد فایل‌ها در صورت عدم وجود
for file in [VIDEO_FILE, USER_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)


def load_json(file):
    with open(file, "r") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)


async def is_subscribed(user_id, context):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = load_json(USER_FILE)

    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "first_name": update.effective_user.first_name,
            "username": update.effective_user.username,
            "joined": str(datetime.now())
        }
        save_json(USER_FILE, user_data)

    args = context.args
    if args:
        video_id = args[0]
        return await send_video_to_user(update, context, video_id)

    if not await is_subscribed(user_id, context):
        btn = [[InlineKeyboardButton("عضویت در کانال‌ها 📢", url=CHANNELS[0])],
               [InlineKeyboardButton("عضویت در کانال دوم 📢", url=CHANNELS[1])],
               [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_sub")]]
        await update.message.reply_text("👋 برای استفاده از ربات ابتدا در کانال‌های زیر عضو شوید:", reply_markup=InlineKeyboardMarkup(btn))
        return

    btn = [[InlineKeyboardButton("ارسال ویدیو 📤", callback_data="send_video")]] if user_id in ADMINS else []
    if user_id in ADMINS:
        btn.append([InlineKeyboardButton("پنل ادمین 🛠", callback_data="admin_panel")])
    await update.message.reply_text("سلام حاجی 😎", reply_markup=InlineKeyboardMarkup(btn))


async def send_video_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id in ADMINS:
        await query.message.reply_text("ویدیوی خود را ارسال کنید:")
        context.user_data["awaiting_video"] = True


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS or not context.user_data.get("awaiting_video"):
        return

    context.user_data["awaiting_video"] = False
    file_id = update.message.video.file_id
    video_id = str(uuid4())
    videos = load_json(VIDEO_FILE)
    videos[video_id] = {"file_id": file_id, "uploader": user_id, "time": str(datetime.now())}
    save_json(VIDEO_FILE, videos)

    link = f"https://t.me/{BOT_USERNAME}?start={video_id}"
    await update.message.reply_text(f"🎥 ویدیو ذخیره شد!\n🔗 لینک: {link}")
    await update.message.reply_text("⏱ فیلم‌های ارسالی بعد از 30 ثانیه پاک می‌شوند.\n✅ در پیام‌های ذخیره‌شده یا پی‌وی دوستان بفرستید و دانلود کنید.")


async def send_video_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, video_id):
    if not await is_subscribed(update.effective_user.id, context):
        await update.message.reply_text("برای دریافت ویدیو ابتدا عضو کانال‌ها شوید.")
        return

    videos = load_json(VIDEO_FILE)
    video = videos.get(video_id)
    if video:
        msg = await context.bot.send_video(chat_id=update.effective_chat.id, video=video["file_id"])
        await asyncio.sleep(30)
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        except:
            pass


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_subscribed(query.from_user.id, context):
        await query.message.delete()
        await query.message.reply_text("✅ عضویت شما تأیید شد.")
    else:
        await query.message.reply_text("❌ هنوز عضو کانال نیستی. لطفاً عضو شو و دوباره امتحان کن.")


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id not in ADMINS:
        return
    videos = load_json(VIDEO_FILE)
    users = load_json(USER_FILE)
    msg = f"""🛠 پنل ادمین:

👥 تعداد کاربران: {len(users)}
📼 تعداد ویدیوها: {len(videos)}
"""
    await query.message.reply_text(msg)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(CallbackQueryHandler(send_video_button, pattern="^send_video$"))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))

    app.run_polling()


if __name__ == "__main__":
    main()
