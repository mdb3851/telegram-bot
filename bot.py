import telebot
import time
import threading
import json

TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
ADMINS = [1476858288, 6998318486]
CHANNELS = ["zappasmagz", "magzsukhte"]  # فقط یوزرنیم کانال بدون @ و https

bot = telebot.TeleBot(TOKEN)

try:
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
except:
    data = {"videos": {}, "users": {}}

def save_data(d):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

awaiting_video = {}

def is_member(chat_id, user_id):
    # چک عضویت کاربر در کانال‌ها
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(f"@{channel}", user_id)
            if member.status not in ['left', 'kicked']:
                return True
        except Exception as e:
            print(f"Error checking membership in @{channel}: {e}")
    return False

@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) == 1:
        # فقط /start بدون پارامتر
        bot.send_message(user_id, "سلام حاجی!\nبرای دریافت ویدیو ابتدا باید عضو کانال‌ها باشید.")
        # ذخیره کاربر
        username = message.from_user.username or "ناشناخته"
        data["users"][str(user_id)] = username
        save_data(data)
        return

    param = args[1]

    if param.startswith("video"):
        code = param[5:]  # حذف 'video' و گرفتن کد

        # چک ویدیو موجود باشد
        file_id = data["videos"].get(code)
        if not file_id:
            bot.send_message(user_id, "ویدیو پیدا نشد یا حذف شده است.")
            return

        # چک عضویت کانال‌ها
        if not is_member(message.chat.id, user_id):
            bot.send_message(user_id,
                "برای دریافت ویدیو باید ابتدا عضو همه کانال‌های زیر شوید:\n" +
                "\n".join([f"https://t.me/{ch}" for ch in CHANNELS]))
            return

        # ارسال ویدیو
        bot.send_video(user_id, file_id)

@bot.message_handler(func=lambda m: True)
def menu_handler(message):
    user_id = message.from_user.id
    text = message.text

    if text == "ارسال ویدیو" and user_id in ADMINS:
        awaiting_video[user_id] = True
        bot.send_message(user_id, "لطفاً ویدیوی خود را ارسال کنید:")

    else:
        bot.send_message(user_id, "دستور نامعتبر یا اجازه دسترسی ندارید.")

@bot.message_handler(content_types=["video"])
def receive_video(message):
    user_id = message.from_user.id

    if user_id not in ADMINS or not awaiting_video.get(user_id):
        return

    awaiting_video[user_id] = False

    video = message.video
    file_id = video.file_id

    code = str(int(time.time()))
    data["videos"][code] = file_id
    save_data(data)

    bot.send_message(user_id,
        f"✅ ویدیو ذخیره شد.\n📎 لینک اشتراک‌گذاری:\nhttps://t.me/{bot.get_me().username}?start=video{code}")

    sent = bot.send_video(user_id, file_id,
        caption="🎬 فیلم در پیام‌های ذخیره شده — ۳۰ ثانیه دیگر حذف می‌شود.")

    threading.Thread(target=delete_message_after_30, args=(user_id, sent.message_id)).start()

def delete_message_after_30(chat_id, message_id):
    time.sleep(30)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"❌ خطا در حذف پیام: {e}")

bot.infinity_polling()
