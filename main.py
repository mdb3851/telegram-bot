import asyncio
import logging
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler, CallbackQueryHandler,
                          filters, ContextTypes)
import os

# فعال‌سازی nest_asyncio برای جلوگیری از خطای event loop
nest_asyncio.apply()

# اطلاعات ادمین و کانال‌ها
ADMINS = [1476858288, 6998318486]
CHANNELS = ['@zappasmagz', '@magzsukhte']
BOT_USERNAME = 'maguz_sukhteabot'
VIDEO_DIR = 'videos'
DB_FILE = 'db.txt'

# ساخت دایرکتوری ویدیوی ذخیره‌شده اگر وجود ندارد
os.makedirs(VIDEO_DIR, exist_ok=True)

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# متغیرهای سراسری
bot_enabled = True
users = set()
video_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)

    buttons = []
    if user_id in ADMINS:
        buttons.append([InlineKeyboardButton("ارسال ویدیو 📤", callback_data='send_video')])
        buttons.append([InlineKeyboardButton("پنل ادمین 🛠", callback_data='admin_panel')])

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("سلام حاجی 👋", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'send_video':
        await query.edit_message_text("لطفا ویدیوی خود را ارسال کنید 🎥")
    elif query.data == 'admin_panel':
        text = f"🛠 پنل ادمین:\n\n👥 کاربران: {len(users)}\n🎞 ویدیوها: {len(video_links)}\n📡 وضعیت ربات: {'روشن ✅' if bot_enabled else 'خاموش ❌'}"
        buttons = [
            [InlineKeyboardButton("روشن کردن ✅", callback_data='enable_bot'),
             InlineKeyboardButton("خاموش کردن ❌", callback_data='disable_bot')],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    elif query.data == 'enable_bot':
        global bot_enabled
        bot_enabled = True
        await query.edit_message_text("✅ ربات با موفقیت روشن شد.")
    elif query.data == 'disable_bot':
        bot_enabled = False
        await query.edit_message_text("❌ ربات خاموش شد.")

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    video = update.message.video
    if not video:
        await update.message.reply_text("لطفاً فقط فایل ویدیویی ارسال کنید.")
        return

    video_id = str(video.file_unique_id)
    file_path = os.path.join(VIDEO_DIR, f"{video_id}.mp4")
    new_file = await context.bot.get_file(video.file_id)
    await new_file.download_to_drive(file_path)

    video_links[video_id] = file_path
    link = f"https://t.me/{BOT_USERNAME}?start={video_id}"
    await update.message.reply_text(f"✅ ویدیو ذخیره شد.\nلینک: {link}")

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status not in ('member', 'administrator', 'creator'):
                return False
        except:
            return False
    return True

async def handle_start_param(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)

    if not bot_enabled:
        await update.message.reply_text("⛔️ ربات فعلاً غیرفعال است.")
        return

    if not await check_membership(user_id, context):
        buttons = [
            [InlineKeyboardButton("عضویت در کانال ۱", url='https://t.me/zappasmagz')],
            [InlineKeyboardButton("عضویت در کانال ۲", url='https://t.me/magzsukhte')],
            [InlineKeyboardButton("بررسی عضویت ✅", callback_data='check_membership')]
        ]
        await update.message.reply_text("📛 لطفاً ابتدا در کانال‌های زیر عضو شوید:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    video_id = context.args[0] if context.args else None
    if video_id in video_links:
        with open(video_links[video_id], 'rb') as f:
            msg = await update.message.reply_video(f)

        # حذف ویدیو بعد از 30 ثانیه
        await asyncio.sleep(30)
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        except:
            pass

        await update.message.reply_text("⏱ فیلم‌های ارسالی ربات بعد از 30 ثانیه از ربات پاک می‌شوند.\n\n✅ فیلم را در پی‌وی دوستان خود یا در پیام‌های ذخیره‌شده ارسال و بعد دانلود کنید.")

async def check_membership_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_membership(query.from_user.id, context):
        await query.edit_message_text("✅ عضویت تأیید شد. دوباره روی لینک بزنید.")
    else:
        await query.edit_message_text("❌ هنوز عضو نیستید. لطفاً هر دو کانال را عضو شوید و دوباره امتحان کنید.")

async def main():
    app = Application.builder().token("7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI").build()

    app.add_handler(CommandHandler("start", handle_start_param))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(check_membership_button, pattern='check_membership'))
    app.add_handler(MessageHandler(filters.VIDEO, video_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    await app.run_polling()

# اجرای امن در محیط Railway
if __name__ == "__main__":
    def run():
        import nest_asyncio
        nest_asyncio.apply()
        import asyncio
        asyncio.get_event_loop().run_until_complete(main())
    run()
