import json
import random
import string
import os
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
)

TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
ADMIN_IDS = [1476858288, 6998318486]
CHANNELS = ["@zappasmagz", "@magzsukhte"]
VIDEO_FILE = "videos.json"
USERS_FILE = "users.json"
BOT_USERNAME = "maguz_sukhteabot"

videos = {}
users = set()
bot_enabled = True

# Load videos
if os.path.exists(VIDEO_FILE):
    with open(VIDEO_FILE, "r") as f:
        videos = json.load(f)

# Load users
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = set(json.load(f))

def save_videos():
    with open(VIDEO_FILE, "w") as f:
        json.dump(videos, f)

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    users.add(user_id)
    save_users()

    keyboard = [[KeyboardButton("ارسال ویدیو 📤")]]
    if is_admin(user_id):
        keyboard[0].append(KeyboardButton("پنل ادمین 🛠"))
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("سلام حاجی", reply_markup=reply_markup)

async def handle_text(update: Update, context: CallbackContext):
    global bot_enabled
    text = update.message.text
    user_id = update.effective_user.id

    if not bot_enabled and not is_admin(user_id):
        await update.message.reply_text("⛔ ربات فعلاً غیرفعال است.")
        return

    if text == "ارسال ویدیو 📤":
        if is_admin(user_id):
            await update.message.reply_text("لطفاً ویدیوت رو بفرست.")
            context.user_data["awaiting_video"] = True
        else:
            await update.message.reply_text("فقط مدیران می‌تونن ویدیو ارسال کنن.")

    elif text == "پنل ادمین 🛠":
        if is_admin(user_id):
            status = "روشن ✅" if bot_enabled else "خاموش ❌"
            await update.message.reply_text(
                f"🔧 پنل ادمین:\n\n📊 کاربران: {len(users)}\n🎞 ویدیوها: {len(videos)}\n⚙ وضعیت ربات: {status}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("روشن / خاموش کردن ربات 🔁", callback_data="toggle_bot")]
                ])
            )
        else:
            await update.message.reply_text("شما دسترسی ندارید.")

async def handle_video(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if not is_admin(user_id) or not context.user_data.get("awaiting_video"):
        return

    context.user_data["awaiting_video"] = False

    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("ویدیو معتبر نیست.")
        return

    file_id = video.file_id
    token = generate_token()
    videos[token] = file_id
    save_videos()

    link = f"https://t.me/{BOT_USERNAME}?start={token}"
    await update.message.reply_text(f"✅ ویدیو ذخیره شد.\n\n🎯 لینک: {link}")

async def start_token(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    users.add(user_id)
    save_users()

    args = context.args
    if not args:
        await start(update, context)
        return

    token = args[0]
    if token not in videos:
        await update.message.reply_text("❌ ویدیو یافت نشد.")
        return

    # Check subscription
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                raise Exception("Not a member")
        except:
            join_buttons = [
                [InlineKeyboardButton("عضویت در کانال اول 📢", url=f"https://t.me/{CHANNELS[0][1:]}")],
                [InlineKeyboardButton("عضویت در کانال دوم 📢", url=f"https://t.me/{CHANNELS[1][1:]}")],
                [InlineKeyboardButton("بررسی عضویت ✅", callback_data=f"check:{token}")]
            ]
            await update.message.reply_text(
                "🚫 برای دریافت ویدیو ابتدا در دو کانال زیر عضو شوید:",
                reply_markup=InlineKeyboardMarkup(join_buttons)
            )
            return

    await send_timed_video(update, context, user_id, videos[token])

async def check_subscription(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    token = query.data.split(":")[1]

    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                raise Exception("Not a member")
        except:
            await query.edit_message_text("❌ هنوز عضو هر دو کانال نشدید.")
            return

    await context.bot.send_video(chat_id=user_id, video=videos[token])
    await query.edit_message_text("✅ ویدیو برات ارسال شد!")

    await asyncio.sleep(30)
    try:
        await context.bot.delete_message(chat_id=user_id, message_id=query.message.message_id + 1)
        await context.bot.send_message(chat_id=user_id, text="⏱ فیلم‌های ارسالی بعد از 30 ثانیه پاک می‌شن. لطفاً ذخیره کن.")
    except:
        pass

async def send_timed_video(update: Update, context: CallbackContext, chat_id, file_id):
    message = await context.bot.send_video(chat_id=chat_id, video=file_id)
    await asyncio.sleep(30)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        await context.bot.send_message(chat_id=chat_id, text="⏱ فیلم‌های ارسالی بعد از 30 ثانیه پاک می‌شن. لطفاً ذخیره کن.")
    except:
        pass

async def toggle_bot(update: Update, context: CallbackContext):
    global bot_enabled
    query = update.callback_query
    await query.answer()
    bot_enabled = not bot_enabled
    status = "روشن ✅" if bot_enabled else "خاموش ❌"
    await query.edit_message_text(f"⚙ وضعیت ربات: {status}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_token))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern=r"check:"))
    app.add_handler(CallbackQueryHandler(toggle_bot, pattern="toggle_bot"))

    print("🤖 ربات با موفقیت راه‌اندازی شد.")
    app.run_polling()

if __name__ == "__main__":
    main()
