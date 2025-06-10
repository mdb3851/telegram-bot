import os
import json
from uuid import uuid4
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# -------------------
# اطلاعات ادمین و تنظیمات ربات
ADMINS = [1476858288, 6998318486]
BOT_TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
CHANNELS = ["@zappasmagz", "@magzsukhte"]
VIDEO_DB_FILE = "videos.json"
# -------------------

# اگر فایل وجود نداشت بساز
if not os.path.exists(VIDEO_DB_FILE):
    with open(VIDEO_DB_FILE, "w") as f:
        json.dump({}, f)

def load_videos():
    with open(VIDEO_DB_FILE) as f:
        return json.load(f)

def save_videos(data):
    with open(VIDEO_DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_admin(user_id):
    return user_id in ADMINS

def get_main_menu(user_id):
    buttons = [[KeyboardButton("ارسال ویدیو 📤")]] if is_admin(user_id) else []
    buttons.append([KeyboardButton("پنل ادمین 🛠")]) if is_admin(user_id) else None
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def check_membership(user_id, context):
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

async def handle_start_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    if args:
        # لینک ویدیو
        video_id = args[0]
        if not await check_membership(user.id, context):
            buttons = [[InlineKeyboardButton("عضویت در کانال 1", url="https://t.me/zappasmagz")],
                       [InlineKeyboardButton("عضویت در کانال 2", url="https://t.me/magzsukhte")],
                       [InlineKeyboardButton("بررسی عضویت ✅", callback_data=f"check_{video_id}")]]
            await update.message.reply_text("📛 برای دریافت ویدیو ابتدا در کانال‌ها عضو شوید:",
                                            reply_markup=InlineKeyboardMarkup(buttons))
            return

        videos = load_videos()
        if video_id in videos:
            file_id = videos[video_id]["file_id"]
            msg = await context.bot.send_video(chat_id=user.id, video=file_id)
            await update.message.reply_text(
                "⏱ فیلم‌های ارسالی ربات بعد از 30 ثانیه از ربات پاک می‌شوند.\n✅ فیلم را در پی‌وی دوستان یا پیام‌های ذخیره‌شده ارسال و بعد دانلود کنید."
            )
            await context.job_queue.run_once(lambda ctx: ctx.bot.delete_message(chat_id=user.id, message_id=msg.message_id), 30)

    else:
        await update.message.reply_text("سلام حاجی 👋", reply_markup=get_main_menu(user.id))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("check_"):
        video_id = data.split("_")[1]
        if await check_membership(query.from_user.id, context):
            videos = load_videos()
            if video_id in videos:
                file_id = videos[video_id]["file_id"]
                msg = await context.bot.send_video(chat_id=query.from_user.id, video=file_id)
                await context.bot.send_message(chat_id=query.from_user.id,
                    text="⏱ فیلم‌های ارسالی ربات بعد از 30 ثانیه از ربات پاک می‌شوند.\n✅ فیلم را در پی‌وی دوستان یا پیام‌های ذخیره‌شده ارسال و بعد دانلود کنید.")
                await context.job_queue.run_once(lambda ctx: ctx.bot.delete_message(chat_id=query.from_user.id, message_id=msg.message_id), 30)
            await query.message.delete()
        else:
            await query.answer("هنوز عضو نیستی 😐", show_alert=True)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return

    file = update.message.video or update.message.document
    file_id = file.file_id
    video_id = str(uuid4())[:8]

    videos = load_videos()
    videos[video_id] = {
        "file_id": file_id,
        "by": user.id,
        "time": str(datetime.utcnow())
    }
    save_videos(videos)

    await update.message.reply_text(f"✅ ویدیو ذخیره شد. لینک:
https://t.me/maguz_sukhteabot?start={video_id}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستور نامعتبر است ⛔")

if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start_video))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    app.run_polling()
