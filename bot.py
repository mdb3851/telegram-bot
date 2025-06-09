import telebot
import json
import time
import threading

# ======= تنظیمات اولیه =======
TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
ADMINS = [1476858288, 6998318486]

# لینک کانال‌ها برای چک عضویت
CHANNELS = ["@zappasmagz", "@magzsukhte"]

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"
awaiting_video = {}

# ======= بارگذاری و ذخیره اطلاعات =======
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"videos": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# ======= تابع حذف پیام بعد 30 ثانیه =======
def delete_message_after_30(chat_id, message_id):
    time.sleep(30)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass

# ======= استارت و بررسی عضویت =======
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) == 1:
        # استارت ساده، پیام خوش آمد + توضیح کانال‌ها + دکمه بررسی عضویت
        keyboard = telebot.types.InlineKeyboardMarkup()
        for ch in CHANNELS:
            keyboard.add(telebot.types.InlineKeyboardButton(text=f"کانال {ch}", url=f"https://t.me/{ch.strip('@')}"))
        keyboard.add(telebot.types.InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_sub"))

        text = (
            "سلام حاجی!\n\n"
            "برای دریافت ویدیو ابتدا باید عضو کانال‌ها باشید."
        )
        bot.send_message(user_id, text, reply_markup=keyboard)
    else:
        # اگر لینک استارت همراه پارامتر video بود (لینک ویدیو)
        param = args[1]
        if param.startswith("video"):
            code = param.replace("video", "")
            file_id = data["videos"].get(code)
            if not file_id:
                bot.send_message(user_id, "❌ این ویدیو پیدا نشد یا حذف شده است.")
                return

            # چک عضویت
            all_subscribed = True
            for ch in CHANNELS:
                status = bot.get_chat_member(ch, user_id).status
                if status in ["left", "kicked"]:
                    all_subscribed = False
                    break

            if not all_subscribed:
                bot.send_message(user_id, "❌ شما عضو یکی از کانال‌ها نیستید! ابتدا عضو شوید.")
                return

            # ارسال ویدیو به کاربر
            sent = bot.send_video(user_id, file_id)

            # ارسال پیام هشدار بلافاصله بعد ارسال ویدیو
            bot.send_message(user_id,
                "⏱ فیلم های ارسالی ربات بعد از 30 ثانیه از ربات پاک میشوند.\n\n"
                "✅ فیلم را در پی وی دوستان خود یا در پیام های ذخیره شده ارسال و بعد دانلود کنید.️")

            # حذف ویدیو بعد 30 ثانیه
            threading.Thread(target=delete_message_after_30, args=(user_id, sent.message_id)).start()

# ======= هندلر بررسی عضویت =======
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.from_user.id
    all_subscribed = True
    for ch in CHANNELS:
        status = bot.get_chat_member(ch, user_id).status
        if status in ["left", "kicked"]:
            all_subscribed = False
            break

    if all_subscribed:
        bot.answer_callback_query(call.id, "✅ شما عضو همه کانال‌ها هستید. می‌توانید ویدیوها را دریافت کنید.")
    else:
        bot.answer_callback_query(call.id, "❌ شما عضو یکی از کانال‌ها نیستید! لطفا ابتدا عضو شوید.")

# ======= دستور ارسال ویدیو توسط ادمین =======
@bot.message_handler(commands=["sendvideo"])
def send_video_command(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        awaiting_video[user_id] = True
        bot.send_message(user_id, "📥 لطفا ویدیوی خود را ارسال کنید.")
    else:
        bot.send_message(user_id, "❌ شما ادمین نیستید.")

# ======= دریافت ویدیو از ادمین =======
@bot.message_handler(content_types=["video"])
def receive_video(message):
    user_id = message.from_user.id

    if user_id not in ADMINS or not awaiting_video.get(user_id, False):
        bot.send_message(user_id, "❌ شما اجازه ارسال ویدیو ندارید یا در حالت ارسال نیستید.")
        return

    awaiting_video[user_id] = False
    video = message.video
    file_id = video.file_id

    code = str(int(time.time()))
    data["videos"][code] = file_id
    save_data(data)

    bot_username = bot.get_me().username
    link = f"https://t.me/{bot_username}?start=video{code}"
    bot.send_message(user_id, f"✅ ویدیو ذخیره شد.\nلینک اشتراک:\n{link}")

# ======= اجرای ربات =======
print("Bot started...")
bot.infinity_polling()
