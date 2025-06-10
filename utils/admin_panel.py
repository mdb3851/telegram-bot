from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def admin_menu():
    buttons = [
        [InlineKeyboardButton("📥 ارسال ویدیو", callback_data="send_video")],
        [InlineKeyboardButton("🛠 پنل مدیریت", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(buttons)
