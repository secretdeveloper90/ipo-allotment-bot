import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database import init_db, add_pan, get_all_pans, delete_pan_by_id, get_pan_count
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BASE_URL = "https://ipoedge-scraping-be.vercel.app/api"
API_URL = f"{BASE_URL}/ipos/allotedipo-list"
CHECK_ALLOTMENT_URL = f"{BASE_URL}/ipos/check-ipoallotment"

# Pagination settings
IPOS_PER_PAGE = 10

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Start command received from user {update.message.from_user.id}")

    # Send welcome message with bot description
    welcome_msg = "🎉 *Welcome to IPO Allotment Bot!*\n\n"
    welcome_msg += "This bot helps you check IPO allotment status for multiple PAN numbers.\n\n"
    welcome_msg += "*Features:*\n"
    welcome_msg += "• 📋 Manage multiple PAN numbers with names\n"
    welcome_msg += "• 📊 Select from available IPOs\n"
    welcome_msg += "• ✅ Check allotment status for all your PANs\n\n"
    welcome_msg += "Use the menu below to get started! 👇"

    # Reply keyboard (persistent keyboard at bottom)
    reply_keyboard = [
        ["🔍 Check IPO Allotment", "📋 Manage PAN Number"],
        ["🔄 Refresh IPO List", "🏠 Main Menu"]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    # Inline keyboard (buttons below message)
    inline_keyboard = [
        [InlineKeyboardButton("📋 Manage PAN Numbers", callback_data="manage_pan"),
         InlineKeyboardButton("📊 Check IPO Allotment", callback_data="ipo_list_0")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]

    logger.info(f"Sending start message with {len(inline_keyboard)} rows of buttons")

    await update.message.reply_text(
        welcome_msg,
        reply_markup=reply_markup,  # Use reply keyboard instead of inline
        parse_mode="Markdown"
    )

    logger.info("Start message sent successfully")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📚 *How to use IPO Allotment Bot:*\n\n"

    msg += "*1. Manage PAN Numbers* 📋\n"
    msg += "• Add PAN numbers with names (e.g., \"John Doe\")\n"
    msg += "• Delete PAN numbers you no longer need\n"
    msg += "• View all your saved PAN numbers\n\n"

    msg += "*2. Check IPO Allotment* 📊\n"
    msg += "• Click \"Check IPO Allotment\"\n"
    msg += "• Select an IPO from the available list\n"
    msg += "• Get allotment status for all your PAN numbers\n\n"

    msg += "*Commands:*\n"
    msg += "/start - Start the bot and show main menu\n"
    msg += "/help - Show this help message\n\n"

    msg += "*Flow:*\n"
    msg += "1️⃣ Add your PAN numbers\n"
    msg += "2️⃣ Click \"Check IPO Allotment\"\n"
    msg += "3️⃣ Choose an IPO\n"
    msg += "4️⃣ View results for all PANs\n\n"

    msg += "Use the buttons below to navigate! 👇"

    keyboard = [
        [InlineKeyboardButton("📋 Manage PAN Numbers", callback_data="manage_pan"),
         InlineKeyboardButton("📊 Check IPO Allotment", callback_data="ipo_list_0")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
    ]

    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_main_menu(message, text=None):
    if text is None:
        text = "🏠 *Main Menu*\n\nWhat would you like to do?"

    keyboard = [
        [InlineKeyboardButton("📋 Manage PAN Numbers", callback_data="manage_pan"),
         InlineKeyboardButton("📊 Check IPO Allotment", callback_data="ipo_list_0")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "manage_pan":
        # Show PAN management menu
        msg = "📋 *PAN Number Management*\n\n"
        msg += "Choose an option:"
        keyboard = [
            [InlineKeyboardButton("📋 View My PANs", callback_data="view_pans")],
            [InlineKeyboardButton("➕ Add PAN Number", callback_data="add_pan")],
            [InlineKeyboardButton("❌ Delete PAN Number", callback_data="delete_pan_menu")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")]
        ]
        await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "view_pans":
        # Show all PANs for the user
        pans = get_all_pans(user_id)
        total_pans = len(pans)

        if not pans:
            msg = "📋 *Your PAN Numbers:* (0/20)\n\n"
            msg += "❌ No PAN numbers saved yet.\n\n"
            msg += "Add your first PAN to start checking IPO allotments."
            keyboard = [
                [InlineKeyboardButton("➕ Add PAN Number", callback_data="add_pan")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")]
            ]
        else:
            msg = f"📋 *Your PAN Numbers:* ({total_pans}/20)\n\n"
            for idx, pan_data in enumerate(pans, 1):
                msg += f"{idx}. *{pan_data['name']}*\n"
                msg += f"   PAN: `{pan_data['pan']}`\n\n"

            keyboard = [
                [InlineKeyboardButton("➕ Add PAN Number", callback_data="add_pan"),
                 InlineKeyboardButton("❌ Delete PAN Number", callback_data="delete_pan_menu")],
                [InlineKeyboardButton("📋 View My PANs", callback_data="view_pans")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")]
            ]

        await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "help":
        msg = "📚 *How to use IPO Allotment Bot:*\n\n"

        msg += "*1. Manage PAN Numbers* 📋\n"
        msg += "• Add PAN numbers with names (e.g., \"John Doe\")\n"
        msg += "• Delete PAN numbers you no longer need\n"
        msg += "• View all your saved PAN numbers\n\n"

        msg += "*2. Check IPO Allotment* 📊\n"
        msg += "• Click \"Check IPO Allotment\"\n"
        msg += "• Select an IPO from the available list\n"
        msg += "• Get allotment status for all your PAN numbers\n\n"

        msg += "*Commands:*\n"
        msg += "/start - Start the bot and show main menu\n"
        msg += "/help - Show this help message\n\n"

        msg += "*Flow:*\n"
        msg += "1️⃣ Add your PAN numbers\n"
        msg += "2️⃣ Click \"Check IPO Allotment\"\n"
        msg += "3️⃣ Choose an IPO\n"
        msg += "4️⃣ View results for all PANs\n\n"

        msg += "Use the buttons below to navigate! 👇"

        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "add_pan":
        # Check if user has reached the limit
        pan_count = get_pan_count(user_id)
        if pan_count >= 20:
            msg = "⚠️ *Limit Reached*\n\n"
            msg += "You have reached the maximum limit of 20 PAN numbers.\n"
            msg += "Please delete some PANs before adding new ones."
            keyboard = [
                [InlineKeyboardButton("❌ Delete PAN", callback_data="delete_pan_menu")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
            ]
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            msg = "➕ *Add New PAN Number*\n\n"
            msg += "Send your PAN number with or without name:\n\n"
            msg += "ABCDE1234F (PAN only)\n"
            msg += "ABCDE1234F  John Doe (PAN with name)\n\n"
            msg += "📋 *Name is optional*"

            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")]]
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            context.user_data["awaiting_pan"] = True

    elif data == "delete_pan_menu":
        # Show list of PANs to delete
        pans = get_all_pans(user_id)

        if not pans:
            msg = "❌ *No PAN Numbers*\n\n"
            msg += "You don't have any PAN numbers to delete."
            keyboard = [
                [InlineKeyboardButton("➕ Add PAN Number", callback_data="add_pan")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
            ]
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            msg = "🗑 *Delete PAN Number*\n\n"
            msg += "Select a PAN to delete:\n\n"

            keyboard = []
            for idx, pan_data in enumerate(pans, 1):
                button_text = f"{idx}. {pan_data['name']} - {pan_data['pan']}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_pan_{pan_data['id']}")])

            keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
            await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("delete_pan_"):
        # Delete specific PAN
        pan_id = int(data.replace("delete_pan_", ""))
        delete_pan_by_id(pan_id)

        msg = "✅ *PAN Deleted Successfully*\n\n"
        msg += "The PAN has been removed from your list."
        keyboard = [
            [InlineKeyboardButton("📋 View My PANs", callback_data="view_pans")],
            [InlineKeyboardButton("➕ Add PAN Number", callback_data="add_pan")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
        ]
        await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("ipo_list_"):
        # Extract page number
        page = int(data.split("_")[-1])

        try:
            res = requests.get(API_URL, timeout=10)
            if res.status_code == 200:
                ipos = res.json().get("data", [])
                if not ipos:
                    await query.message.reply_text("❌ No IPOs found")
                    return

                # Get user's PAN count
                pan_count = get_pan_count(user_id)

                # Calculate pagination
                total_ipos = len(ipos)
                total_pages = (total_ipos + IPOS_PER_PAGE - 1) // IPOS_PER_PAGE
                start_idx = page * IPOS_PER_PAGE
                end_idx = min(start_idx + IPOS_PER_PAGE, total_ipos)

                # Create inline keyboard with IPO buttons for current page
                keyboard = []
                for ipo in ipos[start_idx:end_idx]:
                    ipo_name = ipo.get('iponame', 'N/A')
                    ipo_id = ipo.get('ipoid', '')
                    # Truncate long names
                    display_name = ipo_name[:45] + "..." if len(ipo_name) > 45 else ipo_name
                    keyboard.append([InlineKeyboardButton(f"🔹 {display_name}", callback_data=f"check_{ipo_id}")])

                # Add pagination buttons
                nav_buttons = []
                if page > 0:
                    nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"ipo_list_{page-1}"))
                if page < total_pages - 1:
                    nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"ipo_list_{page+1}"))

                if nav_buttons:
                    keyboard.append(nav_buttons)

                # Add refresh button
                keyboard.append([InlineKeyboardButton("🔄 Refresh IPO List", callback_data=f"ipo_list_{page}")])

                # Add back button
                keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")])

                # Build message with IPO count and PAN count
                msg = f"� *IPO Allotment Check*\n\n"
                msg += f"✅ IPO list updated ({total_ipos} IPOs available)\n\n"
                msg += f"Select an IPO to check allotment status for your {pan_count} PAN number(s):\n\n"
                msg += f"📄 Page {page + 1} of {total_pages}"

                await query.message.reply_text(
                    msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await query.message.reply_text("❌ Failed to fetch IPO list. Please try again later.")
        except requests.exceptions.Timeout:
            await query.message.reply_text("⏱️ Request timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error fetching IPO list: {e}")
            await query.message.reply_text("❌ An error occurred. Please try again later.")

    elif data == "back_to_menu":
        await show_main_menu(query.message)

    elif data.startswith("check_"):
        # Extract IPO ID from callback data
        ipo_id = data.replace("check_", "")

        # Get IPO name from the API
        ipo_name = "IPO"
        try:
            res = requests.get(API_URL, timeout=10)
            if res.status_code == 200:
                ipos = res.json().get("data", [])
                for ipo in ipos:
                    if ipo.get('ipoid') == ipo_id:
                        ipo_name = ipo.get('iponame', 'IPO')
                        break
        except Exception as e:
            logger.error(f"Error fetching IPO name: {e}")

        # Get all user's PANs
        pans = get_all_pans(user_id)
        if not pans:
            keyboard = [[InlineKeyboardButton("➕ Add PAN Now", callback_data="add_pan")]]
            await query.message.reply_text(
                "❌ *PAN Not Found!*\n\n"
                "Please add your PAN card to check allotment status.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

        # Show loading message
        pan_count = len(pans)
        loading_msg = await query.message.reply_text(
            f"🔍 *Checking allotment status...*\n\n⏳ Checking {pan_count} PAN number(s)...\nPlease wait...",
            parse_mode="Markdown"
        )

        # Call the check allotment API
        try:
            # Extract just the PAN numbers
            pan_numbers = [pan_data["pan"] for pan_data in pans]

            payload = {
                "ipoid": ipo_id,
                "pancard": pan_numbers
            }

            # Log the payload for debugging
            logger.info(f"Sending payload to API: {payload}")

            response = requests.post(CHECK_ALLOTMENT_URL, json=payload, timeout=30)

            # Log the response for debugging
            logger.info(f"API Response Status: {response.status_code}")
            logger.info(f"API Response Body: {response.text}")

            if response.status_code == 200:
                result = response.json()

                # Format the response
                if result.get("success"):
                    data_array = result.get("data", [])

                    # Create a mapping of PAN to response data for easy lookup
                    pan_response_map = {}
                    for item in data_array:
                        pancard = item.get("pancard", "")
                        pan_response_map[pancard] = item.get("data", {})

                    # Build the message header
                    msg = "🏦 *IPO Allotment Status*\n\n"
                    msg += f"🏢 *IPO:* {ipo_name}\n\n"

                    # Process each PAN and display status
                    for idx, pan_data in enumerate(pans, 1):
                        pan_number = pan_data["pan"]
                        pan_name = pan_data["name"]

                        msg += f"*{idx}. {pan_name}*\n"
                        msg += f"   PAN: {pan_number}\n"

                        # Get the response for this PAN
                        pan_response = pan_response_map.get(pan_number, {})

                        if pan_response and pan_response.get("success"):
                            # Extract dataResult from the nested structure
                            data_result = pan_response.get("dataResult", {})
                            status = data_result.get("status", "Unknown")
                            shares_allotted = data_result.get("shares_allotted", "0")

                            # Check status and display accordingly
                            if status.lower() == "not apply":
                                msg += f"   Status: ❌ NOT APPLIED\n\n"
                            elif status.lower() == "allotted":
                                msg += f"   Status: ✅ ALLOTTED\n"
                                msg += f"   Shares Allotted: {shares_allotted}\n\n"
                            else:
                                # Show any other status
                                msg += f"   Status: {status}\n"
                                if shares_allotted and shares_allotted != "0":
                                    msg += f"   Shares Allotted: {shares_allotted}\n"
                                msg += "\n"
                        else:
                            # No valid response for this PAN
                            msg += f"   Status: ❌ NOT APPLIED\n\n"

                    # Add timestamp
                    current_time = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")
                    msg += f"\n🕐 *Updated:* {current_time}"

                    # Add navigation buttons
                    keyboard = [
                        [InlineKeyboardButton("🔙 Check Another IPO", callback_data="ipo_list_0")],
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
                    ]
                    await loading_msg.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
                else:
                    msg = f"❌ *Error*\n\n{result.get('message', 'Failed to check allotment')}"
                    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="ipo_list_0")]]
                    await loading_msg.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                msg = f"❌ *Failed to check allotment*\n\nError code: {response.status_code}\n\nPlease try again later."
                keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="ipo_list_0")]]
                await loading_msg.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

        except requests.exceptions.Timeout:
            msg = "⏱️ *Request Timed Out*\n\nThe server is taking too long to respond.\nPlease try again later."
            keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data=f"check_{ipo_id}")]]
            await loading_msg.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Error checking allotment: {e}")
            msg = "❌ *An error occurred*\n\nPlease try again later."
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="ipo_list_0")]]
            await loading_msg.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id

    # Handle reply keyboard button presses
    if text == "🔍 Check IPO Allotment":
        # Simulate callback query for IPO list
        try:
            page = 0
            res = requests.get(API_URL, timeout=10)
            if res.status_code == 200:
                ipos = res.json().get("data", [])
                if not ipos:
                    await update.message.reply_text("❌ No IPOs found")
                    return

                # Get user's PAN count
                pan_count = get_pan_count(user_id)

                # Calculate pagination
                total_ipos = len(ipos)
                total_pages = (total_ipos + IPOS_PER_PAGE - 1) // IPOS_PER_PAGE
                start_idx = page * IPOS_PER_PAGE
                end_idx = min(start_idx + IPOS_PER_PAGE, total_ipos)

                # Create inline keyboard with IPO buttons for current page
                keyboard = []
                for ipo in ipos[start_idx:end_idx]:
                    ipo_name = ipo.get('iponame', 'N/A')
                    ipo_id = ipo.get('ipoid', '')
                    # Truncate long names
                    display_name = ipo_name[:45] + "..." if len(ipo_name) > 45 else ipo_name
                    keyboard.append([InlineKeyboardButton(f"🔹 {display_name}", callback_data=f"check_{ipo_id}")])

                # Add pagination buttons
                nav_buttons = []
                if page > 0:
                    nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"ipo_list_{page-1}"))
                if page < total_pages - 1:
                    nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"ipo_list_{page+1}"))

                if nav_buttons:
                    keyboard.append(nav_buttons)

                # Add refresh button
                keyboard.append([InlineKeyboardButton("🔄 Refresh IPO List", callback_data=f"ipo_list_{page}")])

                # Add back button
                keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")])

                # Build message with IPO count and PAN count
                msg = f"📊 *IPO Allotment Check*\n\n"
                msg += f"✅ IPO list updated ({total_ipos} IPOs available)\n\n"
                msg += f"Select an IPO to check allotment status for your {pan_count} PAN number(s):\n\n"
                msg += f"📄 Page {page + 1} of {total_pages}"

                await update.message.reply_text(
                    msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Failed to fetch IPO list. Please try again later.")
        except requests.exceptions.Timeout:
            await update.message.reply_text("⏱️ Request timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error fetching IPO list: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again later.")

    elif text == "📋 Manage PAN Number":
        # Show PAN management menu
        msg = "📋 *PAN Number Management*\n\n"
        msg += "Choose an option:"
        keyboard = [
            [InlineKeyboardButton("📋 View My PANs", callback_data="view_pans")],
            [InlineKeyboardButton("➕ Add PAN Number", callback_data="add_pan")],
            [InlineKeyboardButton("❌ Delete PAN Number", callback_data="delete_pan_menu")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif text == "🔄 Refresh IPO List":
        # Refresh IPO list
        await update.message.reply_text("🔄 Refreshing IPO list...")
        # Trigger the same action as "Check IPO Allotment"
        try:
            page = 0
            res = requests.get(API_URL, timeout=10)
            if res.status_code == 200:
                ipos = res.json().get("data", [])
                if not ipos:
                    await update.message.reply_text("❌ No IPOs found")
                    return

                pan_count = get_pan_count(user_id)
                total_ipos = len(ipos)
                total_pages = (total_ipos + IPOS_PER_PAGE - 1) // IPOS_PER_PAGE
                start_idx = page * IPOS_PER_PAGE
                end_idx = min(start_idx + IPOS_PER_PAGE, total_ipos)

                keyboard = []
                for ipo in ipos[start_idx:end_idx]:
                    ipo_name = ipo.get('iponame', 'N/A')
                    ipo_id = ipo.get('ipoid', '')
                    display_name = ipo_name[:45] + "..." if len(ipo_name) > 45 else ipo_name
                    keyboard.append([InlineKeyboardButton(f"🔹 {display_name}", callback_data=f"check_{ipo_id}")])

                nav_buttons = []
                if page > 0:
                    nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"ipo_list_{page-1}"))
                if page < total_pages - 1:
                    nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"ipo_list_{page+1}"))

                if nav_buttons:
                    keyboard.append(nav_buttons)

                keyboard.append([InlineKeyboardButton("🔄 Refresh IPO List", callback_data=f"ipo_list_{page}")])
                keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")])

                msg = f"📊 *IPO Allotment Check*\n\n"
                msg += f"✅ IPO list refreshed ({total_ipos} IPOs available)\n\n"
                msg += f"Select an IPO to check allotment status for your {pan_count} PAN number(s):\n\n"
                msg += f"📄 Page {page + 1} of {total_pages}"

                await update.message.reply_text(
                    msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Failed to refresh IPO list. Please try again later.")
        except Exception as e:
            logger.error(f"Error refreshing IPO list: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again later.")

    elif text == "🏠 Main Menu":
        # Show main menu
        await show_main_menu(update.message)

    elif context.user_data.get("awaiting_pan"):
        # Handle PAN input
        # Parse the input - support multiple formats
        # Format 1: ABCDE1234F (PAN only)
        # Format 2: ABCDE1234F  John Doe (PAN with name, separated by spaces)

        parts = text.split(None, 1)  # Split on first whitespace

        if len(parts) == 1:
            # Just PAN provided
            pan = parts[0].upper()
            name = "No Name"
        elif len(parts) == 2:
            # PAN and name provided
            pan = parts[0].upper()
            name = parts[1].strip()
        else:
            await update.message.reply_text(
                "❌ *Invalid Format*\n\n"
                "Please use one of these formats:\n"
                "• ABCDE1234F (PAN only)\n"
                "• ABCDE1234F  John Doe (PAN with name)",
                parse_mode="Markdown"
            )
            return

        # Validate PAN format (basic validation)
        if len(pan) != 10:
            await update.message.reply_text(
                "❌ *Invalid PAN*\n\n"
                "PAN must be 10 characters long.\n"
                "*Format:* ABCDE1234F",
                parse_mode="Markdown"
            )
            return

        # Add the PAN
        try:
            add_pan(user_id, name, pan)
            context.user_data["awaiting_pan"] = False

            msg = f"✅ *PAN Added Successfully!*\n\n"
            msg += f"👤 *Name:* {name}\n"
            msg += f"📋 *PAN:* `{pan}`\n\n"
            msg += "You can now check IPO allotment status."

            keyboard = [
                [InlineKeyboardButton("📋 View My PANs", callback_data="view_pans")],
                [InlineKeyboardButton("📊 Check Allotment", callback_data="ipo_list_0")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
            ]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error adding PAN: {e}")
            error_msg = str(e)

            # Show specific error message
            if "Maximum 20 PAN" in error_msg:
                await update.message.reply_text(
                    "❌ *Limit Reached*\n\n"
                    "You have reached the maximum limit of 20 PAN numbers.\n"
                    "Please delete some PANs before adding new ones.",
                    parse_mode="Markdown"
                )
            elif "already added" in error_msg:
                await update.message.reply_text(
                    "❌ *Duplicate PAN*\n\n"
                    "This PAN number is already added to your account.",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "❌ *Error*\n\n"
                    "Failed to add PAN. Please try again.",
                    parse_mode="Markdown"
                )
            context.user_data["awaiting_pan"] = False

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and notify user"""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ *An error occurred*\n\nPlease try again later or contact support.",
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-app.onrender.com
    PORT = int(os.getenv("PORT", 10000))
    USE_WEBHOOK = os.getenv("USE_WEBHOOK", "true").lower() == "true"

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Add error handler
    app.add_error_handler(error_handler)

    logger.info("🚀 Bot is running...")
    print("🚀 Bot is running...")

    if USE_WEBHOOK and WEBHOOK_URL:
        # Webhook mode for production (Render)
        logger.info(f"Using webhook mode: {WEBHOOK_URL}")

        # Use python-telegram-bot's built-in webhook support
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    else:
        # Polling mode for local development
        logger.info("Using polling mode")
        app.run_polling()

if __name__ == "__main__":
    main()

