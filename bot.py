import os
import logging
import time
from uuid import uuid4
from functools import wraps
from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# تنظیمات اولیه
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [1476858288, 6998318486]
CHANNELS = ["@zappasmagz", "@magzsukhte"]
VIDEOS_DIR = "videos"

# لاگ
logging.basicConfig(level=logging.INFO)

# ساخت پوشه ویدیوها اگه وجود نداشت
if not os.path.exists(VIDEOS_DIR):
    os.makedirs(VIDEOS_DIR)

# دکوراتور برای چک ادمین بودن
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id in ADMINS:
            return await func(update, context)
        else:
            await update.message.reply_text("فقط ادمین می‌تونه این دکمه رو ببینه!")
    return wrapper

# چک عضویت
async def check_membership(user_id, context):
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

# استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام حاجی {user.first_name}!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎥 ارسال ویدیو (ادمین)", callback_data="send_video")]
        ])
    )

# دکمه ارسال ویدیو (فقط ادمین می‌تونه استفاده کنه)
@admin_only
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "send_video":
        await query.message.reply_text("ویدیو مورد نظر رو ارسال کن.")

# ذخیره ویدیو
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return

    file = await update.message.video.get_file()
    unique_id = str(uuid4())
    path = os.path.join(VIDEOS_DIR, f"{unique_id}.mp4")
    await file.download_to_drive(path)

    link = f"https://t.me/{context.bot.username}?start=vid_{unique_id}"
    await update.message.reply_text(
        f"✅ ویدیو ذخیره شد!\n📎 لینکش:\n{link}"
    )

# دریافت با لینک اختصاصی
async def start_with_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    if not args or not args[0].startswith("vid_"):
        return await start(update, context)

    if not await check_membership(user.id, context):
        join_buttons = [[InlineKeyboardButton("عضو شو", url=link)] for link in [
            "https://t.me/zappasmagz", "https://t.me/magzsukhte"
        ]]
        await update.message.reply_text(
            "برای دریافت ویدیو باید عضو کانال‌ها بشی👇",
            reply_markup=InlineKeyboardMarkup(join_buttons)
        )
        return

    video_id = args[0].replace("vid_", "")
    video_path = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")

    if not os.path.exists(video_path):
        return await update.message.reply_text("ویدیو پیدا نشد!")

    msg = await update.message.reply_video(
        video=open(video_path, "rb"),
        caption="🎬 فیلم در پیام‌های ذخیره‌شده هم ارسال شد، بعد از ۳۰ ثانیه پاک میشه!"
    )
    await context.bot.copy_message(
        chat_id=user.id,
        from_chat_id=update.effective_chat.id,
        message_id=msg.message_id
    )
    await context.bot.send_message(
        chat_id=user.id,
        text="این پیام بعد از ۳۰ ثانیه پاک می‌شود..."
    )
    await asyncio.sleep(30)
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
    except:
        pass

# راه‌اندازی
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_with_video))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.COMMAND, start))

    print("ربات روشن شد!")
    app.run_polling()

if __name__ == "__main__":
    import asyncio
    main()
