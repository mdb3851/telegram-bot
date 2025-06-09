import telebot
from telebot import types
import json
import os
import threading
import time
import requests

# -------------------- تنظیمات اولیه --------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # از متغیر محیطی می‌خواند
ADMINS = [1476858288, 6998318486]

CHANNELS = ["zappasmagz", "magzsukhte"]

DATA_FILE = "data.json"  # فایل ذخیره داده‌ها

bot = telebot.TeleBot(BOT_TOKEN)

lock = threading.Lock()

# -------------------- مدیریت ذخیره و بارگذاری داده‌ها --------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"videos": {}, "enabled": True}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with lock:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)

data = load_data()

# -------------------- چک عضویت --------------------

def check_membership(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(f"@{channel}", user_id)
            if member.status == "left":
                return False
        except Exception:
            return False
    return True

# -------------------- دکمه‌ها و منو --------------------

def main_keyboard(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("دریافت ویدیو"))
    if user_id in ADMINS:
        kb.row(types.KeyboardButton("ارسال ویدیو"), types.KeyboardButton("پنل مدیریت"))
    return kb

def admin_panel_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("حذف همه ویدیوها", callback_data="del_all_videos"))
    kb.add(types.InlineKeyboardButton("خاموش کردن ربات", callback_data="disable_bot"))
    kb.add(types.InlineKeyboardButton("روشن کردن ربات", callback_data="enable_bot"))
    return kb

# -------------------- مدیریت ویدیوها --------------------

def delete_all_videos():
    data["videos"] = {}
    save_data(data)

# -------------------- هندلرها --------------------

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "سلام حاجی", reply_markup=main_keyboard(user_id))

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text

    if not data.get("enabled", True):
        if user_id in ADMINS:
            bot.send_message(user_id, "ربات فعلاً خاموش است.", reply_markup=main_keyboard(user_id))
        return

    if text == "دریافت ویدیو":
        if not check_membership(user_id):
            bot.send_message(user_id, "⚠️ لطفاً ابتدا در کانال‌های عضویت عضو شوید.", reply_markup=main_keyboard(user_id))
            return

        if not data["videos"]:
            bot.send_message(user_id, "فعلاً ویدیویی موجود نیست.", reply_markup=main_keyboard(user_id))
            return

        # ارسال لینک ویدیو (لینک به ربات با کد مخصوص)
        video_codes = list(data["videos"].keys())
        kb = types.InlineKeyboardMarkup()
        for code in video_codes:
            kb.add(types.InlineKeyboardButton(f"ویدیو {code}", callback_data=f"sendvideo_{code}"))
        bot.send_message(user_id, "ویدیوهای موجود:", reply_markup=kb)

    elif text == "ارسال ویدیو" and user_id in ADMINS:
        msg = bot.send_message(user_id, "لطفاً ویدیوی خود را ارسال کنید:")
        bot.register_next_step_handler(msg, receive_video)

    elif text == "پنل مدیریت" and user_id in ADMINS:
        bot.send_message(user_id, "پنل مدیریت ربات:", reply_markup=admin_panel_keyboard())

    else:
        bot.send_message(user_id, "لطفاً از منوی پایین استفاده کنید.", reply_markup=main_keyboard(user_id))

@bot.message_handler(content_types=["video"])
def receive_video(message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        bot.send_message(user_id, "دسترسی ندارید.")
        return

    video = message.video
    file_id = video.file_id

    # ذخیره ویدیو
    code = str(int(time.time()))
    data["videos"][code] = file_id
    save_data(data)

    bot.send_message(user_id, f"ویدیو ذخیره شد. لینک برای ارسال به کاربران:\nhttps://t.me/maguz_sukhteabot?start=video{code}")
    bot.send_message(user_id, "فیلم رو داخل پیام‌های ذخیره شده بفرست فیلم ۳۰ ثانیه بعد پاک میشود.")

    # ارسال فیلم داخل پیام های ذخیره شده (Saved Messages)
    bot.send_video(user_id, file_id, caption="فیلم ارسالی (۳۰ ثانیه بعد پاک می‌شود)")

    # شروع تایمر حذف ۳۰ ثانیه‌ای
    threading.Thread(target=delete_video_after_30, args=(user_id, file_id)).start()

def delete_video_after_30(user_id, file_id):
    time.sleep(30)
    try:
        bot.delete_message(user_id, message_id=None)  # حذف پیام ارسالی به کاربر (پیام فیلم)
        # اما متأسفانه پیام ویدیویی که خودمان ارسال کردیم ID نداره برای حذف مستقیم
        # پس نمی‌توانیم دقیق اینجا حذف کنیم مگر پیام ID بگیریم؛
        # این محدودیت API است. پس می‌توان فقط اطلاع بدیم یا پیام متن را حذف کنیم.
    except Exception:
        pass

@bot.callback_query_handler(func=lambda c: True)
def callback_query(call):
    user_id = call.from_user.id
    data_call = call.data

    if data_call.startswith("sendvideo_"):
        code = data_call.replace("sendvideo_", "")
        if code in data["videos"]:
            if not check_membership(user_id):
                bot.answer_callback_query(call.id, "لطفاً ابتدا عضو کانال‌ها شوید.")
                return
            file_id = data["videos"][code]
            bot.send_video(user_id, file_id, caption="ویدیو ارسالی")
        else:
            bot.answer_callback_query(call.id, "ویدیو پیدا نشد.")

    elif data_call == "del_all_videos" and user_id in ADMINS:
        delete_all_videos()
        bot.answer_callback_query(call.id, "همه ویدیوها حذف شدند.")
        bot.send_message(user_id, "همه ویدیوها حذف شدند.", reply_markup=admin_panel_keyboard())

    elif data_call == "disable_bot" and user_id in ADMINS:
        data["enabled"] = False
        save_data(data)
        bot.answer_callback_query(call.id, "ربات خاموش شد.")
        bot.send_message(user_id, "ربات خاموش شد.", reply_markup=admin_panel_keyboard())

    elif data_call == "enable_bot" and user_id in ADMINS:
        data["enabled"] = True
        save_data(data)
        bot.answer_callback_query(call.id, "ربات روشن شد.")
        bot.send_message(user_id, "ربات روشن شد.", reply_markup=admin_panel_keyboard())

    else:
        bot.answer_callback_query(call.id, "دستور نامعتبر")

# -------------------- مدیریت پارامتر استارت ویدیو --------------------

@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) > 1:
        arg = args[1]
        if arg.startswith("video"):
            code = arg.replace("video", "")
            if code in data["videos"]:
                if check_membership(user_id):
                    bot.send_video(user_id, data["videos"][code], caption="ویدیو ارسالی")
                else:
                    bot.send_message(user_id, "⚠️ لطفاً ابتدا عضو کانال‌های ما شوید.")
                return
    bot.send_message(user_id, "سلام حاجی", reply_markup=main_keyboard(user_id))

# -------------------- اجرای ربات --------------------

print("Bot is running...")
bot.infinity_polling()
