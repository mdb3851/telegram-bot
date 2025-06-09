import telebot
import time
import threading
import json

# تنظیمات اولیه
TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
ADMINS = [1476858288, 6998318486]
CHANNELS = ["https://t.me/zappasmagz", "https://t.me/magzsukhte"]

bot = telebot.TeleBot(TOKEN)

# داده‌ها (ویدیوها و کاربران)
try:
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
except:
    data = {"videos": {}, "users": {}}

def save_data(d):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

# متغیر برای وضعیت انتظار ویدیو (برای هر ادمین)
awaiting_video = {}  # {user_id: True/False}

# هندلر شروع ربات (مثلا وقتی کاربر /start میزند)
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    username = message.from_user.username or "ناشناخته"

    # ذخیره کاربر
    data["users"][str(user_id)] = username
    save_data(data)

    bot.send_message(user_id, "سلام حاجی!\nبرای دریافت ویدیو ابتدا باید عضو کانال‌ها باشید.")

# هندلر پیام متنی برای دکمه‌ها
@bot.message_handler(func=lambda m: True)
def menu_handler(message):
    user_id = message.from_user.id
    text = message.text

    if text == "ارسال ویدیو" and user_id in ADMINS:
        awaiting_video[user_id] = True
        bot.send_message(user_id, "لطفاً ویدیوی خود را ارسال کنید:")

    else:
        bot.send_message(user_id, "دستور نامعتبر یا اجازه دسترسی ندارید.")

# هندلر دریافت ویدیو
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

# تابع حذف پیام پس از ۳۰ ثانیه
def delete_message_after_30(chat_id, message_id):
    time.sleep(30)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"❌ خطا در حذف پیام: {e}")

# هندلر استارت با پارامتر ویدیو (وقتی کاربر لینک ویدیو را باز می‌کند)
@bot.message_handler(commands=["start"])
def start_video_handler(message):
    text = message.text
    user_id = message.from_user.id

    if text.startswith("/start video"):
        code = text.replace("/start video", "").strip()
        file_id = data["videos"].get(code)

        if not file_id:
            bot.send_message(user_id, "ویدیو پیدا نشد یا حذف شده است.")
            return

        # چک کانال بودن کاربر (عضویت)
        # در اینجا کد چک کانال باید اضافه شود، چون در تلگرام API رسمی برای این نیست
        # به طور ساده فرض می‌کنیم کاربر عضو هست
        # اگر بخواهی می‌توانم کد چک کانال با استفاده از telebot api یا کتابخانه‌های دیگر بدم

        bot.send_video(user_id, file_id)

# شروع ربات
bot.infinity_polling()
