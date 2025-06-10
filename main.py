import json
import os
import asyncio
from uuid import uuid4
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler, ContextTypes
)
from config import ADMINS, CHANNELS, BOT_USERNAME

VIDEO_STORAGE = "videos.json"

def load_videos():
    if os.path.exists(VIDEO_STORAGE):
        with open(VIDEO_STORAGE, "r") as f:
            return json.load(f)
    return {}

def save_videos(data):
    with open(VIDEO_STORAGE, "w") as f:
        json.dump(data, f)

videos = load_videos()

def get_start_keyboard(is_admin=False):
    buttons = [[KeyboardButton("ارسال ویدیو 📤")]] if is_admin else []
    if is_admin:
        buttons.append([KeyboardButton("پنل ادمین 🛠")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def check_membership(user_id, context: ContextTypes.DEFAULT_TYPE):
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if not await check_membership(user_id, context):
        buttons = [[InlineKeyboardButton("📢 عضویت در کانال 1", url="https://t.me/zappasmagz")],
                   [InlineKeyboardButton("📢 عضویت در کانال 2", url="https://t.me/magzsukhte")],
                   [InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_membership")]]
        await update.message.reply_text("برای استفاده از ربات ابتدا در کانال‌های زیر عضو شوید 👇", reply_markup=InlineKeyboardMarkup(buttons))
        return

    is_admin = user_id in ADMINS
    await update.message.reply_text("سلام حاجی", reply_markup=get_start_keyboard(is_admin))

async def check_membership_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if await check_membership(user_id, context):
        await query.edit_message_text("✅ عضویت شما تایید شد. دوباره /start بزنید.")
    else:
        await query.edit_message_text("❌ هنوز عضو نشدی! لطفاً عضو شو و بعد دوباره بررسی بزن.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return

    file = update.message.video or update.message.document
    if not file:
        await update.message.reply_text("لطفاً فقط ویدیو ارسال کنید.")
        return

    file_id = file.file_id
    video_id = str(uuid4())
    videos[video_id] = file_id
    save_videos(videos)

    link = f"https://t.me/{BOT_USERNAME}?start={video_id}"
    await update.message.reply_text(f"✅ لینک ویدیو:\n{link}\n\n⏱ فیلم‌های ربات بعد از ۳۰ ثانیه حذف می‌شن.\n✅ حتماً ذخیره‌اش کن.")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "check_membership":
        await check_membership_button(update, context)

async def handle_start_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        return await start(update, context)

    video_id = args[0]
    if video_id not in videos:
        await update.message.reply_text("❌ این ویدیو موجود نیست یا حذف شده.")
        return

    if not await check_membership(user_id, context):
        buttons = [[InlineKeyboardButton("📢 عضویت در کانال 1", url="https://t.me/zappasmagz")],
                   [InlineKeyboardButton("📢 عضویت در کانال 2", url="https://t.me/magzsukhte")],
                   [InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_membership")]]
        await update.message.reply_text("برای دیدن ویدیو باید در کانال‌ها عضو باشید 👇", reply_markup=InlineKeyboardMarkup(buttons))
        return

    msg = await update.message.reply_video(videos[video_id])
    await asyncio.sleep(30)
    await msg.delete()

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستور نامعتبر است.")

# === راه‌اندازی برنامه اصلی ===

import logging
logging.basicConfig(level=logging.INFO)

from telegram.ext import Application

async def main():
    TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start_video))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
