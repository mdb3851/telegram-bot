import telebot
import json
import time
import threading

TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
ADMINS = [1476858288, 6998318486]
CHANNELS = ["zappasmagz", "magzsukhte"]  # بدون @ برای راحتی استفاده در URL

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "data.json"
awaiting_video = {}

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

def check_all_subscribed(user_id):
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(f"@{ch}", user_id).status
            if status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

def send_membership_message(user_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for ch in CHANNELS:
        keyboard.add(telebot.types.InlineKeyboardButton(text=f"کانال @{ch}", url=f"https://t.me/{ch}"))
    keyboard.add(telebot.types.InlineKeyboardButton("✅ من عضو هستم", callback_data="check_sub"))
    text = (
        "سلام حاجی!\n\n"
        "برای دریافت ویدیو ابتدا باید عضو کانال‌ها باشید.\n"
        "لطفاً روی دکمه‌های زیر کلیک کرده و عضو شوید."
    )
    bot.send_message(user_id, text, reply_markup=keyboard)

def send_main_menu(user_id):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        telebot.types.KeyboardButton("ارسال ویدیو"),
        telebot.types.KeyboardButton("پنل ننننادمین")
    )
    bot.send_message(user_id, "منوی اصلی:", reply_markup=keyboard)

@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    if check_all_subscribed(user_id):
        bot.send_message(user_id, "سلام حاجی!\nخوش آمدی به ربات.", reply_markup=telebot.types.ReplyKeyboardRemove())
        send_main_menu(user_id)
    else:
        send_membership_message(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    if check_all_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد.")
        bot.send_message(user_id, "🎉 تبریک! شما عضو همه کانال‌ها هستید.")
        send_main_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ شما هنوز عضو همه کانال‌ها نیستید. لطفا ابتدا عضو شوید.")

@bot.message_handler(func=lambda m: True)
def main_menu_handler(message):
    user_id = message.from_user.id
    text = message.text

    if not check_all_subscribed(user_id):
        send_membership_message(user_id)
        return

    if text == "ارسال ویدیو":
        if user_id in ADMINS:
            awaiting_video[user_id] = True
            bot.send_message(user_id, "📥 لطفا ویدیوی خود را ارسال کنید.")
        else:
            bot.send_message(user_id, "❌ شما ادمین نیستید.")
        return

    if text == "پنل ادمین":
        if user_id in ADMINS:
            # اینجا می‌تونی بخش پنل ادمین رو توسعه بدی
            bot.send_message(user_id, "⚙️ به پنل ادمین خوش آمدید! فعلاً این بخش خالی است.")
        else:
            bot.send_message(user_id, "❌ شما ادمین نیستید.")
        return

@bot.message_handler(content_types=["video"])
def video_handler(message):
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

def delete_message_later(chat_id, message_id, delay=30):
    def job():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=job).start()

@bot.message_handler(commands=["start"])
def start_video_handler(message):
    args = message.text.split()
    user_id = message.from_user.id
    if len(args) > 1 and args[1].startswith("video"):
        code = args[1][5:]
        if code in data["videos"]:
            if not check_all_subscribed(user_id):
                send_membership_message(user_id)
                return
            video_id = data["videos"][code]
            sent = bot.send_video(user_id, video_id)
            text_msg = bot.send_message(user_id,
                "⏱ فیلم های ارسالی ربات بعد از 30 ثانیه از ربات پاک میشوند.\n\n"
                "✅ فیلم را در پی وی دوستان خود یا در پیام های ذخیره شده ارسال و بعد دانلود کنید.️"
            )
            delete_message_later(user_id, sent.message_id, 30)
            delete_message_later(user_id, text_msg.message_id, 30)
        else:
            bot.send_message(user_id, "❌ لینک ویدیو معتبر نیست.")
    else:
        # اینجا پیام استارت معمولی قبلی را هندل کن
        if check_all_subscribed(user_id):
            bot.send_message(user_id, "سلام حاجی!\nخوش آمدی به ربات.", reply_markup=telebot.types.ReplyKeyboardRemove())
            send_main_menu(user_id)
        else:
            send_membership_message(user_id)

print("Bot started...")
bot.infinity_polling()
