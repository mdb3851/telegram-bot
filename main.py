import os
import json
import asyncio
from uuid import uuid4
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    CallbackContext, CallbackQueryHandler
)

# اطلاعات ثابت
TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
ADMIN_IDS = [1476858288, 6998318486]
CHANNELS = ["@zappasmagz", "@magzsukhte"]
BOT_USERNAME = "maguz_sukhteabot"

VIDEOS_FILE = "videos.json"
USERS_FILE = "users.json"

# ایجاد فایل ویدیوها اگر وجود نداشت
if not os.path.exists(VIDEOS_FILE):
    with open(VIDEOS_FILE, "w") as f:
        json.dump({}, f)

# ذخیره اطلاعات ویدیو
def save_video(video_id, file_id):
    with open(VIDEOS_FILE, "r") as f:
        data = json.load(f)
    data[video_id] = file_id
    with open(VIDEOS_FILE, "w") as f:
        json.dump(data, f)

# دریافت اطلاعات ویدیو
def get_video(video_id):
    with open(VIDEOS_FILE, "r") as f:
        data = json.load(f)
    return data.get(video_id)

# بررسی عضویت در کانال‌ها
async def is_member(user_id, context: CallbackContext):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

# منوی اصلی
def get_main_menu(is_admin=False):
    buttons = [[KeyboardButton("ارسال ویدیو 📤")]] if is_admin else []
    buttons.append([KeyboardButton("پنل ادمین 🛠")] if is_admin else [])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# استارت ربات
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    is_admin = user.id in ADMIN_IDS
    await update.message.reply_text(
        "سلام حاجی",
        reply_markup=get_main_menu(is_admin)
    )

# بررسی عضویت اجباری
async def check_subscription(update: Update, context: CallbackContext):
    user = update.effective_user
    if await is_member(user.id, context):
        return True
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("عضویت در کانال ۱", url="https://t.me/zappasmagz")],
        [InlineKeyboardButton("عضویت در کانال ۲", url="https://t.me/magzsukhte")],
        [InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_sub")]
    ])
    await update.message.reply_text("🔒 برای دریافت ویدیو، اول عضو هر دو کانال شو:", reply_markup=keyboard)
    return False

# دریافت کال‌بک بررسی عضویت
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "check_sub":
        if await is_member(query.from_user.id, context):
            await query.message.delete()
            await query.message.reply_text("✅ عضویت تأیید شد.")
        else:
            await query.message.reply_text("❌ هنوز عضو نیستی. لطفا عضو هر دو کانال شو.")

# مدیریت دکمه‌ها
async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    user = update.effective_user
    is_admin = user.id in ADMIN_IDS

    if text == "ارسال ویدیو 📤" and is_admin:
        await update.message.reply_text("لطفاً ویدیوی خود را ارسال کنید.")
        return

    if text == "پنل ادمین 🛠" and is_admin:
        await update.message.reply_text("🔧 پنل ادمین (در دست ساخت!)")
        return

# دریافت ویدیو از ادمین
async def receive_video(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    video = update.message.video
    if not video:
        return

    file_id = video.file_id
    video_id = str(uuid4())

    save_video(video_id, file_id)
    bot_username = BOT_USERNAME.replace("@", "")
    video_link = f"https://t.me/{bot_username}?start=vid_{video_id}"

    await update.message.reply_text(
        f"✅ ویدیو ذخیره شد. لینک:\n{video_link}\n\n⏱ فیلم‌های ارسالی بعد از ۳۰ ثانیه حذف می‌شن.\n✅ حتماً در پیام‌های ذخیره‌شده یا پی‌وی دوستانت بفرست و دانلود کن."
    )

# مدیریت لینک ویدیو
async def handle_start_video(update: Update, context: CallbackContext):
    user = update.effective_user
    args = context.args
    if not args:
        return await start(update, context)

    if args[0].startswith("vid_"):
        video_id = args[0][4:]
        if not await is_member(user.id, context):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("عضویت در کانال ۱", url="https://t.me/zappasmagz")],
                [InlineKeyboardButton("عضویت در کانال ۲", url="https://t.me/magzsukhte")],
                [InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_sub")]
            ])
            await update.message.reply_text("🔒 برای دریافت ویدیو اول عضو شو:", reply_markup=keyboard)
            return

        file_id = get_video(video_id)
        if file_id:
            sent = await update.message.reply_video(file_id)
            await asyncio.sleep(30)
            try:
                await sent.delete()
            except:
                pass
        else:
            await update.message.reply_text("❌ ویدیو پیدا نشد.")

# اجرای اصلی
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start_video))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VIDEO, receive_video))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
