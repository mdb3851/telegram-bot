import asyncio
import json
import logging
import os
import random
import string
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters, ConversationHandler)

TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
ADMIN_IDS = [1476858288, 6998318486]
CHANNELS = ["@zappasmagz", "@magzsukhte"]

DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"videos": {}, "users": [], "stats": {"views": 0}}, f)

with open(DATA_FILE) as f:
    data = json.load(f)

bot_enabled = True
logging.basicConfig(level=logging.INFO)


def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data()

    keyboard = [[InlineKeyboardButton("ارسال ویدیو 📤", callback_data="send_video")]]
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("پنل ادمین 🛠", callback_data="admin")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("سلام حاجی", reply_markup=reply_markup)


async def check_membership(user_id, context):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "creator", "administrator"]:
                return False
        except:
            return False
    return True


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "send_video":
        if user_id in ADMIN_IDS:
            await query.message.reply_text("لطفاً ویدیوی خود را ارسال کنید.")
            return
        else:
            await query.message.reply_text("این گزینه فقط برای ادمین فعال است.")
            return

    elif query.data == "admin" and user_id in ADMIN_IDS:
        status = "✅ روشن" if bot_enabled else "❌ خاموش"
        buttons = [
            [InlineKeyboardButton("🔄 تغییر وضعیت ربات", callback_data="toggle_bot")],
            [InlineKeyboardButton("👥 کاربران", callback_data="show_users")],
            [InlineKeyboardButton("📊 آمار بازدید", callback_data="show_stats")]
        ]
        await query.message.reply_text(f"وضعیت ربات: {status}", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data == "toggle_bot" and user_id in ADMIN_IDS:
        bot_enabled = not bot_enabled
        await query.message.reply_text("✅ ربات روشن شد" if bot_enabled else "❌ ربات خاموش شد")

    elif query.data == "show_users" and user_id in ADMIN_IDS:
        await query.message.reply_text(f"👥 تعداد کاربران: {len(data['users'])}")

    elif query.data == "show_stats" and user_id in ADMIN_IDS:
        await query.message.reply_text(f"📊 مجموع بازدید لینک‌ها: {data['stats']['views']}")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    file_id = update.message.video.file_id
    vid_id = generate_id()
    data["videos"][vid_id] = file_id
    save_data()

    link = f"https://t.me/{context.bot.username}?start={vid_id}"
    await update.message.reply_text(f"✅ ویدیو ذخیره شد. لینک:
{link}")


async def handle_start_with_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    args = context.args
    user_id = update.effective_user.id

    if not bot_enabled:
        await update.message.reply_text("ربات در حال حاضر غیرفعال است.")
        return

    if not args:
        return

    vid_id = args[0]
    if vid_id not in data["videos"]:
        await update.message.reply_text("ویدیو یافت نشد ❌")
        return

    is_member = await check_membership(user_id, context)
    if not is_member:
        buttons = [[InlineKeyboardButton("عضویت در کانال اول ✅", url=f"https://t.me/{CHANNELS[0][1:]}")],
                   [InlineKeyboardButton("عضویت در کانال دوم ✅", url=f"https://t.me/{CHANNELS[1][1:]}")],
                   [InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_membership")]]
        await update.message.reply_text("برای دریافت ویدیو باید در هر دو کانال عضو شوید:",
                                        reply_markup=InlineKeyboardMarkup(buttons))
        return

    file_id = data["videos"][vid_id]
    sent = await context.bot.send_video(chat_id=user_id, video=file_id)

    data["stats"]["views"] += 1
    save_data()

    await asyncio.sleep(30)
    await context.bot.delete_message(chat_id=user_id, message_id=sent.message_id)
    await context.bot.send_message(chat_id=user_id, text="⏱ فیلم‌های ارسالی ربات بعد از 30 ثانیه از ربات پاک می‌شوند.\n\n✅ فیلم را در پی‌وی دوستان خود یا در پیام‌های ذخیره شده ارسال و بعد دانلود کنید.")


async def check_membership_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    is_member = await check_membership(user_id, context)
    if is_member:
        await query.message.reply_text("✅ اکنون می‌توانید ویدیو را با ارسال دوباره لینک دریافت کنید.")
    else:
        await query.message.reply_text("❌ هنوز در کانال‌ها عضو نشده‌اید. لطفاً ابتدا عضو شوید.")


async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CallbackQueryHandler(check_membership_button, pattern="check_membership"))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(CommandHandler("start", handle_start_with_id))

    await app.run_polling()


if __name__ == '__main__':
    asyncio.run(main())
