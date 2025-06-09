import telebot
from telebot import types
import json
import os
import time
import threading

TOKEN = "7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI"
bot = telebot.TeleBot(TOKEN)

ADMINS = [1476858288, 6998318486]

CHANNELS = [
    "@zappasmagz",
    "@magzsukhte"
]

DATA_FILE = "data.json"

# --- بارگذاری و ذخیره داده‌ها ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {"videos": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

awaiting_video = {}  # برای ادمین‌ها که آیا در حالت ارسال ویدیو هستند یا نه


# --- ارسال منوی اصلی برای کاربر ---
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("بررسی عضویت ✅")
    if user_id in ADMINS:
        markup.add("ارسال ویدیو 🎥")
        markup.add("پنل ادمین ⚙️")
    return markup


# --- پیام خوش‌آمدگویی با دکمه‌های کانال ---
def send_welcome_with_channels(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)

    for ch in CHANNELS:
        btn = types.InlineKeyboardButton(
            text=f"عضویت در کانال {ch}", url=f"https://t.me/{ch.strip('@')}")
        markup.add(btn)

    check_btn = types.InlineKeyboardButton(
        text="✅ بررسی عضویت", callback_data="check_membership")
    markup.add(check_btn)

    text = "سلام حاجی!\nبرای دریافت ویدیو ابتدا باید عضو کانال‌ها باشید."
    bot.send_message(chat_id, text, reply_markup=markup)


# --- هندلر دستور start ---
@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id
    send_welcome_with_channels(user_id)


# --- هندلر دکمه بررسی عضویت ---
@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def check_membership(call):
    user_id = call.from_user.id
    is_member = True
    not_member_channels = []

    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                is_member = False
                not_member_channels.append(ch)
        except Exception as e:
            is_member = False
            not_member_channels.append(ch)

    if is_member:
        bot.answer_callback_query(
            call.id, "🎉 شما عضو همه کانال‌ها هستید.", show_alert=True)
        bot.send_message(user_id, "شما عضو همه کانال‌ها هستید. حالا می‌توانید از ربات استفاده کنید.",
                         reply_markup=main_menu(user_id))
    else:
        text = "❌ شما عضو کانال‌های زیر نیستید:\n"
        for ch in not_member_channels:
            text += f"➡️ {ch}\n"
        text += "\nلطفاً ابتدا عضو کانال‌ها شوید و دوباره بررسی کنید."
        bot.answer_callback_query(call.id, "شما عضو نیستید!", show_alert=True)
        bot.send_message(user_id, text)


# --- هندلر دکمه‌ها (متنی) ---
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text

    # بررسی عضویت قبل از ارسال ویدیو
    if text == "ارسال ویدیو 🎥":
        if user_id not in ADMINS:
            bot.send_message(user_id, "❌ شما ادمین نیستید!")
            return

        # بررسی عضویت ادمین در کانال‌ها هم اگر خواستی (اختیاری)
        if not check_user_membership(user_id):
            bot.send_message(user_id, "❌ ابتدا باید عضو کانال‌ها باشید.")
            return

        awaiting_video[user_id] = True
        bot.send_message(user_id, "لطفا ویدیوی خود را ارسال کنید.")

    elif text == "بررسی عضویت ✅":
        send_welcome_with_channels(user_id)

    elif text == "پنل ادمین ⚙️":
        if user_id in ADMINS:
            send_admin_panel(user_id)
        else:
            bot.send_message(user_id, "❌ شما ادمین نیستید!")

    else:
        bot.send_message(user_id, "دستور نامعتبر است. لطفاً از منو استفاده کنید.")


# --- تابع بررسی عضویت (استفاده داخلی) ---
def check_user_membership(user_id):
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True


# --- هندلر دریافت ویدیو ---
@bot.message_handler(content_types=["video"])
def receive_video(message):
    user_id = message.from_user.id

    if user_id not in ADMINS or not awaiting_video.get(user_id, False):
        bot.send_message(user_id, "❌ شما اجازه ارسال ویدیو ندارید یا در حالت ارسال نیستید.")
        return

    awaiting_video[user_id] = False
    video = message.video
    file_id = video.file_id

    # کد یکتا
    code = str(int(time.time()))
    data["videos"][code] = file_id
    save_data(data)

    bot_username = bot.get_me().username
    link = f"https://t.me/{bot_username}?start=video{code}"
    bot.send_message(user_id, f"✅ ویدیو ذخیره شد.\nلینک اشتراک:\n{link}")

    sent = bot.send_video(user_id, file_id, caption="🎬 فیلم ذخیره شده — ۳۰ ثانیه دیگر حذف می‌شود.")
    threading.Thread(target=delete_message_after_30, args=(user_id, sent.message_id)).start()


# --- حذف پیام پس از ۳۰ ثانیه ---
def delete_message_after_30(chat_id, message_id):
    time.sleep(30)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"❌ خطا در حذف پیام: {e}")


# --- پنل ادمین ساده ---
def send_admin_panel(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("لیست ویدیوها 📂", "حذف ویدیو ❌")
    markup.add("خاموش کردن ربات 🔴", "روشن کردن ربات 🟢")
    markup.add("بازگشت 🔙")
    bot.send_message(user_id, "پنل ادمین:", reply_markup=markup)


# --- متغیر کنترل روشن یا خاموش بودن ربات ---
bot_active = True


# --- هندلرهای پنل ادمین (نمونه) ---
@bot.message_handler(func=lambda m: m.text == "خاموش کردن ربات 🔴" and m.from_user.id in ADMINS)
def shutdown_bot(message):
    global bot_active
    bot_active = False
    bot.send_message(message.chat.id, "ربات خاموش شد.")

@bot.message_handler(func=lambda m: m.text == "روشن کردن ربات 🟢" and m.from_user.id in ADMINS)
def start_bot(message):
    global bot_active
    bot_active = True
    bot.send_message(message.chat.id, "ربات روشن شد.")

# --- اینجا می‌تونی هندلرهای بیشتری برای مدیریت ویدیو و کاربران اضافه کنی ---


# --- هندلر شروع با لینک ویدیو ---
@bot.message_handler(commands=["start"])
def handle_start_video(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("video"):
        code = args[1][5:]
        if code in data["videos"]:
            if check_user_membership(user_id):
                file_id = data["videos"][code]
                bot.send_video(user_id, file_id)
            else:
                send_welcome_with_channels(user_id)
        else:
            bot.send_message(user_id, "ویدیوی مورد نظر پیدا نشد.")
    else:
        send_welcome_with_channels(user_id)


# --- شروع ربات ---
print("ربات در حال اجراست...")
bot.infinity_polling()
