import telebot
import json
import time

TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
ADMINS = [1476858288, 6998318486]
CHANNELS = ["@zappasmagz", "@magzsukhte"]

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
user_membership_message = {}

def check_all_subscribed(user_id):
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

def send_membership_message(user_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for ch in CHANNELS:
        keyboard.add(telebot.types.InlineKeyboardButton(text=f"کانال {ch}", url=f"https://t.me/{ch.strip('@')}"))
    keyboard.add(telebot.types.InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_sub"))
    text = (
        "سلام حاجی!\n\n"
        "برای دریافت ویدیو ابتدا باید عضو کانال‌ها باشید."
    )
    sent_msg = bot.send_message(user_id, text, reply_markup=keyboard)
    user_membership_message[user_id] = sent_msg.message_id

def send_main_menu(user_id):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        telebot.types.KeyboardButton("ارسال ویدیو"),
        telebot.types.KeyboardButton("پنل ادمین")
    )
    bot.send_message(user_id, "منوی اصلی:", reply_markup=keyboard)

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    if check_all_subscribed(user_id):
        bot.send_message(user_id, "سلام حاجی!\nخوش آمدی به ربات.", reply_markup=telebot.types.ReplyKeyboardRemove())
        send_main_menu(user_id)
    else:
        send_membership_message(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.from_user.id
    if check_all_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ شما عضو همه کانال‌ها هستید. حالا می‌توانید ویدیوها را دریافت کنید.")
        # حذف پیام عضویت قبلی
        if user_id in user_membership_message:
            try:
                bot.delete_message(user_id, user_membership_message[user_id])
            except Exception:
                pass
            del user_membership_message[user_id]
        bot.send_message(user_id, "🎉 عضویت شما تایید شد. حالا می‌توانید ویدیوها را دریافت کنید.")
        send_main_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ شما عضو یکی از کانال‌ها نیستید! لطفا ابتدا عضو شوید.")

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
            # اینجا میتونی بخش های پنل ادمین رو اضافه کنی
            bot.send_message(user_id, "⚙️ به پنل ادمین خوش آمدید!\nفعلاً اینجا خالی است.")
        else:
            bot.send_message(user_id, "❌ شما ادمین نیستید.")
        return

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

print("Bot started...")
bot.infinity_polling()
