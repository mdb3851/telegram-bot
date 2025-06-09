from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من آنلاینم 🌟")

app = ApplicationBuilder().token("7721995609:AAHFik1G49bu0OACtFWpv_NBHDzOESxVtTI").build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
