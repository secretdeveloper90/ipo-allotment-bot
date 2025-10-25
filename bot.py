import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database import init_db, set_pan, get_pan, delete_pan
import os

API_URL = "https://ipoedge-scraping-be.vercel.app/api/ipos/allotedipo-list"

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update.message)

async def show_main_menu(message, text="Welcome to IPO Allotment Bot 📊"):
    keyboard = [
        [InlineKeyboardButton("➕ Add PAN", callback_data="add_pan"),
         InlineKeyboardButton("🧾 My PAN", callback_data="my_pan")],
        [InlineKeyboardButton("📈 Alloted IPOs", callback_data="ipo_list"),
         InlineKeyboardButton("🗑 Delete PAN", callback_data="delete_pan")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "add_pan":
        await query.message.reply_text("Please send your PAN (e.g. ABCDE1234F):")
        context.user_data["awaiting_pan"] = True

    elif data == "my_pan":
        pan = get_pan(user_id)
        await query.message.reply_text(f"Your saved PAN: {pan}" if pan else "No PAN saved yet.")

    elif data == "delete_pan":
        delete_pan(user_id)
        await query.message.reply_text("Your PAN has been deleted ❌")

    elif data == "ipo_list":
        res = requests.get(API_URL)
        if res.status_code == 200:
            ipos = res.json().get("data", [])
            if not ipos:
                await query.message.reply_text("No IPOs found ❌")
                return

            msg = "📋 *Alloted IPO List:*\n\n"
            for ipo in ipos:
                # Use lowercase keys as per API response
                ipo_name = ipo.get('iponame', 'N/A')
                msg += f"🔹 {ipo_name}\n\n"
            await query.message.reply_text(msg, parse_mode="Markdown")
        else:
            await query.message.reply_text("Failed to fetch IPO list ❌")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_pan"):
        pan = update.message.text.strip().upper()
        user_id = update.message.from_user.id
        set_pan(user_id, pan)
        context.user_data["awaiting_pan"] = False
        await update.message.reply_text(f"✅ PAN saved successfully: {pan}")

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
