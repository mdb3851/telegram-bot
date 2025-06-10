import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import TOKEN, ADMINS, CHANNELS
from utils.database import save_user, get_video
from utils.video_handler import store_video
from utils.admin_panel import admin_menu

async def check_membership(user_id, context):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)

    args = context.args
    if args:
        video_id = args[0]
        if not await check_membership(user_id, context):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("عضویت در کانال ۱", url="https://t.me/zappasmagz")],
                [InlineKeyboardButton("عضویت در کانال ۲", url="https://t.me/magzsukhte")],
                [InlineKeyboardButton("بررسی عضویت ✅", callback_data=f"check_membership_{video_id}")]
            ])
            await update.message.reply_text("👋 برای دریافت ویدیو باید عضو کانال‌ها باشید:", reply_markup=keyboard)
            return

        file_id = get_video(video_id)
        if file_id:
            msg = await update.message.reply_video(file_id)
            await asyncio.sleep(30)
            await context.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)
        return

    await update.message.reply_text("سلام حاجی 😎", reply_markup=admin_menu() if user_id in ADMINS else None)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("check_membership_"):
        video_id = query.data.split("_")[2]
        is_member = await check_membership(query.from_user.id, context)
        if is_member:
            file_id = get_video(video_id)
            if file_id:
                msg = await context.bot.send_video(chat_id=query.from_user.id, video=file_id)
                await asyncio.sleep(30)
                await context.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)
            await query.message.delete()
        else:
            await query.message.reply_text("❌ هنوز عضو نیستی!")
        return

    if query.data == "send_video":
        await query.message.reply_text("لطفاً یک ویدیو ارسال کن.")
        context.user_data["awaiting_video"] = True

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_video"):
        file_id = update.message.video.file_id
        video_id = store_video(file_id)
        link = f"https://t.me/{context.bot.username}?start={video_id}"
        await update.message.reply_text(f"✅ ویدیو ذخیره شد\n🔗 لینک: {link}\n\n⏱ فیلم‌ها بعد از 30 ثانیه حذف می‌شوند.\n✅ برای دانلود، آن را برای خود ذخیره یا فورواد کن.")
        context.user_data["awaiting_video"] = False

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.VIDEO & filters.User(ADMINS), handle_video))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
