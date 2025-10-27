import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database import init_db, add_pan, get_all_pans, delete_pan_by_id, get_pan_count
from datetime import datetime
import os
import logging
import asyncio
import sys
import traceback

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
IPOS_PER_PAGE = 8  # Reduced from 10 to 8 to avoid scrolling on smaller devices

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
        ["📋 Manage PAN Numbers", "📊 Check IPO Allotment"],
        ["ℹ️ Help"]
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
    msg += "➕ Add PAN numbers with names (e.g., \"John Doe\")\n"
    msg += "❌ Delete PAN numbers you no longer need\n"
    msg += "👁️ View all your saved PAN numbers\n\n"

    msg += "*2. Check IPO Allotment* 📊\n"
    msg += "🔍 Click \"Check IPO Allotment\"\n"
    msg += "📝 Select an IPO from the available list\n"
    msg += "📈 Get allotment status for all your PAN numbers\n\n"

    msg += "*Commands:*\n"
    msg += "▶️ /start - Start the bot and show main menu\n"
    msg += "ℹ️ /help - Show this help message\n\n"

    msg += "*Flow:*\n"
    msg += "1️⃣ Add your PAN numbers\n"
    msg += "2️⃣ Click \"Check IPO Allotment\"\n"
    msg += "3️⃣ Choose an IPO\n"
    msg += "4️⃣ View results for all PANs\n\n"

    msg += "💡 Use the keyboard buttons below to navigate!"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def show_main_menu(message, text=None):
    if text is None:
        text = "🏠 *Main Menu*\n\nWhat would you like to do?"

    # Reply keyboard for main menu
    reply_keyboard = [
        ["📋 Manage PAN Numbers", "📊 Check IPO Allotment"],
        ["ℹ️ Help"]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "manage_pan":
        # Show PAN management menu with reply keyboard
        msg = "📋 *PAN Number Management*\n\n"
        msg += "Choose an option:"

        # Reply keyboard for PAN management
        reply_keyboard = [
            ["➕ Add PAN Number", "❌ Delete PAN Number"],
            ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

        await query.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

    elif data == "view_pans":
        # Show all PANs for the user
        pans = get_all_pans(user_id)
        total_pans = len(pans)

        if not pans:
            msg = "📋 *Your PAN Numbers:* (0/20)\n\n"
            msg += "❌ No PAN numbers saved yet.\n\n"
            msg += "💡 Add your first PAN to start checking IPO allotments."
        else:
            msg = f"📋 *Your PAN Numbers:* ({total_pans}/20)\n\n"
            for idx, pan_data in enumerate(pans, 1):
                msg += f"👤 {idx}. *{pan_data['name']}*\n"
                msg += f"   📄 PAN: `{pan_data['pan']}`\n\n"

        # Show PAN management keyboard
        reply_keyboard = [
            ["➕ Add PAN Number", "❌ Delete PAN Number"],
            ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await query.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

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

            # Show PAN management keyboard
            reply_keyboard = [
                ["➕ Add PAN Number", "❌ Delete PAN Number"],
                ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
            ]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            await query.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            context.user_data["awaiting_pan"] = True
            msg = f"➕ *Add New PAN Number* ({pan_count}/20)\n\n"
            msg += "Please send your PAN details in one of these formats:\n\n"
            msg += "*Format 1:* PAN only\n"
            msg += "`ABCDE1234F`\n\n"
            msg += "*Format 2:* PAN with name\n"
            msg += "`ABCDE1234F  John Doe`\n\n"
            msg += "� Tip: Separate PAN and name with a space"

            # Show only Back to PAN Management button while waiting for PAN input
            reply_keyboard = [
                ["🔙 Back to PAN Management"]
            ]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            await query.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

    elif data == "delete_pan_menu":
        # Show list of PANs to delete
        pans = get_all_pans(user_id)

        if not pans:
            msg = "❌ *No PAN Numbers*\n\n"
            msg += "You don't have any PAN numbers to delete."

            # Show PAN management keyboard
            reply_keyboard = [
                ["➕ Add PAN Number", "❌ Delete PAN Number"],
                ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
            ]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            await query.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            # Store PANs in user context for deletion
            context.user_data["pans_for_deletion"] = pans

            msg = "❌ *Delete PAN Number*\n\n"
            msg += "Select a PAN to delete from the keyboard below:"

            # Create keyboard with PAN list (2 buttons per row)
            reply_keyboard = []
            for idx, pan_data in enumerate(pans, 1):
                name = pan_data['name']
                pan = pan_data['pan']
                button_text = f"🗑️ Delete {idx}: {pan} - {name}"

                # Add 2 buttons per row
                if idx % 2 == 1:
                    reply_keyboard.append([button_text])
                else:
                    reply_keyboard[-1].append(button_text)

            # Add back button
            reply_keyboard.append(["🔙 Back to PAN Management"])

            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            await query.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

    elif data.startswith("delete_pan_"):
        # Delete specific PAN
        pan_id = int(data.replace("delete_pan_", ""))
        delete_pan_by_id(pan_id)

        msg = "✅ *PAN Deleted Successfully*\n\n"
        msg += "The PAN has been removed from your list."

        # Show PAN management keyboard
        reply_keyboard = [
            ["➕ Add PAN Number", "❌ Delete PAN Number"],
            ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await query.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

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

                # Create reply keyboard with IPO buttons for current page (2 per row)
                reply_keyboard = []
                for idx, ipo in enumerate(ipos[start_idx:end_idx]):
                    ipo_name = ipo.get('iponame', 'N/A')
                    ipo_id = ipo.get('ipoid', '')
                    # Truncate long names - no icon
                    display_name = ipo_name[:35] + "..." if len(ipo_name) > 35 else ipo_name
                    button_text = display_name

                    # Add 2 buttons per row
                    if idx % 2 == 0:
                        reply_keyboard.append([button_text])
                    else:
                        reply_keyboard[-1].append(button_text)

                # Store IPO mapping in context for button handling
                context.user_data["ipo_list"] = ipos[start_idx:end_idx]
                context.user_data["current_page"] = page

                # Add pagination buttons (Previous and Next)
                nav_buttons = []
                if page > 0:
                    nav_buttons.append("⬅️ Previous")
                if page < total_pages - 1:
                    nav_buttons.append("Next ➡️")

                if nav_buttons:
                    reply_keyboard.append(nav_buttons)

                # Add refresh and back buttons in one row
                reply_keyboard.append(["🔄 Refresh IPO List", "🔙 Back to Main Menu"])

                reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

                # Build message with IPO count and PAN count
                msg = f"📊 *IPO Allotment Check*\n\n"
                msg += f"✅ IPO list updated ({total_ipos} IPOs available)\n\n"
                msg += f"Select an IPO to check allotment status for your {pan_count} PAN number(s):\n\n"
                msg += f"📄 Page {page + 1} of {total_pages}"

                await query.message.reply_text(
                    msg,
                    reply_markup=reply_markup,
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
                    msg += f"📋 *IPO:* {ipo_name}\n\n"

                    # Track allotment status
                    allotted_count = 0
                    not_allotted_count = 0

                    # Process each PAN and display status
                    for idx, pan_data in enumerate(pans, 1):
                        pan_number = pan_data["pan"]
                        pan_name = pan_data["name"]

                        msg += f"*{idx}.* 👤 *{pan_name}*\n"
                        msg += f"      📋 PAN: `{pan_number}`\n"

                        # Get the response for this PAN
                        pan_response = pan_response_map.get(pan_number, {})

                        if pan_response and pan_response.get("success"):
                            # Extract dataResult from the nested structure
                            data_result = pan_response.get("dataResult", {})
                            status = data_result.get("status", "Unknown")
                            shares_allotted = data_result.get("shares_allotted", "0")

                            # Check status and display accordingly
                            if status.lower() == "not apply":
                                msg += f"      📊 Status: ❌ NOT APPLIED\n\n"
                            elif status.lower() == "allotted":
                                allotted_count += 1
                                msg += f"      ✅ Status: *ALLOTTED*\n"
                                msg += f"      📈 Shares: *{shares_allotted}*\n\n"
                            else:
                                # Check if it's "not allotted" status
                                if status.lower() in ["not allotted", "not alloted"]:
                                    not_allotted_count += 1
                                    msg += f"      ❌ Status: *NOT ALLOTTED*\n\n"
                                else:
                                    # Show any other status
                                    msg += f"      📊 Status: {status}\n"
                                    if shares_allotted and shares_allotted != "0":
                                        msg += f"      📈 Shares: {shares_allotted}\n"
                                    msg += "\n"
                        else:
                            # No valid response for this PAN
                            msg += f"      📊 Status: ❌ NOT APPLIED\n\n"

                    # Add congratulatory or encouragement message
                    if allotted_count > 0:
                        if allotted_count == 1:
                            msg += "🎉 *Congratulations!* You have been allotted 1 IPO!\n"
                        else:
                            msg += f"🎉 *Congratulations!* You have been allotted {allotted_count} IPOs!\n"
                    elif not_allotted_count > 0:
                        msg += "💪 *Better luck next time!* Keep trying.\n"

                    # Add navigation buttons
                    keyboard = [
                        [InlineKeyboardButton("� Refresh IPO List", callback_data="ipo_list_0")],
                        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_menu")]
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

    # IMPORTANT: Check awaiting_pan FIRST before any other text handling
    if context.user_data.get("awaiting_pan"):
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
            msg += f"📄 *PAN:* `{pan}`\n\n"
            msg += "🎉 You can now check IPO allotment status."

            # Show PAN management keyboard
            reply_keyboard = [
                ["➕ Add PAN Number", "❌ Delete PAN Number"],
                ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
            ]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error adding PAN: {e}")
            error_msg = str(e)

            # Show PAN management keyboard after error
            reply_keyboard = [
                ["➕ Add PAN Number", "❌ Delete PAN Number"],
                ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
            ]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

            # Show specific error message
            if "Maximum 20 PAN" in error_msg:
                await update.message.reply_text(
                    "❌ *Limit Reached*\n\n"
                    "You have reached the maximum limit of 20 PAN numbers.\n"
                    "Please delete some PANs before adding new ones.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            elif "already added" in error_msg:
                await update.message.reply_text(
                    "❌ *Duplicate PAN*\n\n"
                    "This PAN number is already added to your account.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "❌ *Error*\n\n"
                    "Failed to add PAN. Please try again.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            context.user_data["awaiting_pan"] = False
        return

    # Handle reply keyboard button presses
    if text == "📊 Check IPO Allotment":
        # Show IPO list with reply keyboard
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

                # Create reply keyboard with IPO buttons for current page (2 per row)
                reply_keyboard = []
                for idx, ipo in enumerate(ipos[start_idx:end_idx]):
                    ipo_name = ipo.get('iponame', 'N/A')
                    ipo_id = ipo.get('ipoid', '')
                    # Truncate long names - no icon
                    display_name = ipo_name[:35] + "..." if len(ipo_name) > 35 else ipo_name
                    button_text = display_name

                    # Add 2 buttons per row
                    if idx % 2 == 0:
                        reply_keyboard.append([button_text])
                    else:
                        reply_keyboard[-1].append(button_text)

                # Store IPO mapping in context for button handling
                context.user_data["ipo_list"] = ipos[start_idx:end_idx]
                context.user_data["current_page"] = page

                # Add pagination buttons (Previous and Next)
                nav_buttons = []
                if page > 0:
                    nav_buttons.append("⬅️ Previous")
                if page < total_pages - 1:
                    nav_buttons.append("Next ➡️")

                if nav_buttons:
                    reply_keyboard.append(nav_buttons)

                # Add refresh and back buttons in one row
                reply_keyboard.append(["🔄 Refresh IPO List", "🔙 Back to Main Menu"])

                reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

                # Build message with IPO count and PAN count
                msg = f"📊 *IPO Allotment Check*\n\n"
                msg += f"✅ IPO list updated ({total_ipos} IPOs available)\n\n"
                msg += f"Select an IPO to check allotment status for your {pan_count} PAN number(s):\n\n"
                msg += f"📄 Page {page + 1} of {total_pages}"

                await update.message.reply_text(
                    msg,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Failed to fetch IPO list. Please try again later.")
        except requests.exceptions.Timeout:
            await update.message.reply_text("⏱️ Request timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error fetching IPO list: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again later.")

    elif text and not text.startswith("⬅️") and not text.startswith("Next") and not text.startswith("🔄") and not text.startswith("🔙") and not text.startswith("📋") and not text.startswith("❌") and not text.startswith("ℹ️") and not text.startswith("➕") and not text.startswith("🗑️"):
        # Handle IPO selection from keyboard (any text that's not a special button)
        ipo_list = context.user_data.get("ipo_list", [])
        if ipo_list:
            # Extract IPO name from button text
            selected_ipo_name = text.strip()

            # Find the matching IPO
            selected_ipo = None
            for ipo in ipo_list:
                ipo_name = ipo.get('iponame', 'N/A')
                display_name = ipo_name[:35] + "..." if len(ipo_name) > 35 else ipo_name
                if display_name == selected_ipo_name:
                    selected_ipo = ipo
                    break

            if selected_ipo:
                # Get user's PANs
                pans = get_all_pans(user_id)
                if not pans:
                    # Show PAN management keyboard when no PANs found
                    reply_keyboard = [
                        ["➕ Add PAN Number", "❌ Delete PAN Number"],
                        ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
                    ]
                    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
                    await update.message.reply_text(
                        "❌ *No PAN numbers found.*\n\n"
                        "Please add a PAN first to check IPO allotment status.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    return

                # Prepare API request
                ipo_id = selected_ipo.get('ipoid', '')
                ipo_name = selected_ipo.get('iponame', 'N/A')

                try:
                    # Extract just the PAN numbers
                    pan_numbers = [pan["pan"] for pan in pans]

                    payload = {
                        "ipoid": ipo_id,
                        "pancard": pan_numbers
                    }

                    logger.info(f"Sending payload to API: {payload}")
                    response = requests.post(CHECK_ALLOTMENT_URL, json=payload, timeout=30)

                    logger.info(f"API Response Status: {response.status_code}")
                    logger.info(f"API Response Body: {response.text}")

                    if response.status_code == 200:
                        result = response.json()

                        if result.get("success"):
                            data_array = result.get("data", [])

                            pan_response_map = {}
                            for item in data_array:
                                pancard = item.get("pancard", "")
                                pan_response_map[pancard] = item.get("data", {})

                            msg = "🏦 *IPO Allotment Status*\n\n"
                            msg += f"📋 *IPO:* {ipo_name}\n\n"

                            # Track allotment status
                            allotted_count = 0
                            not_allotted_count = 0

                            for idx, pan_data in enumerate(pans, 1):
                                pan_number = pan_data["pan"]
                                pan_name = pan_data["name"]

                                msg += f"*{idx}.* 👤 *{pan_name}*\n"
                                msg += f"      📋 PAN: `{pan_number}`\n"

                                pan_response = pan_response_map.get(pan_number, {})

                                if pan_response and pan_response.get("success"):
                                    data_result = pan_response.get("dataResult", {})
                                    status = data_result.get("status", "Unknown")
                                    shares_allotted = data_result.get("shares_allotted", "0")

                                    if status.lower() == "not apply":
                                        msg += f"      📊 Status: ❌ NOT APPLIED\n\n"
                                    elif status.lower() == "allotted":
                                        allotted_count += 1
                                        msg += f"      ✅ Status: *ALLOTTED*\n"
                                        msg += f"      📈 Shares: *{shares_allotted}*\n\n"
                                    else:
                                        # Check if it's "not allotted" status
                                        if status.lower() in ["not allotted", "not alloted"]:
                                            not_allotted_count += 1
                                            msg += f"      ❌ Status: *NOT ALLOTTED*\n\n"
                                        else:
                                            # Show any other status
                                            msg += f"      📊 Status: {status}\n"
                                            if shares_allotted and shares_allotted != "0":
                                                msg += f"      📈 Shares: {shares_allotted}\n"
                                            msg += "\n"
                                else:
                                    msg += f"      📊 Status: ❌ NOT APPLIED\n\n"

                            # Add congratulatory or encouragement message
                            if allotted_count > 0:
                                if allotted_count == 1:
                                    msg += "🎉 *Congratulations!* You have been allotted 1 IPO!\n"
                                else:
                                    msg += f"🎉 *Congratulations!* You have been allotted {allotted_count} IPOs!\n"
                            elif not_allotted_count > 0:
                                msg += "💪 *Better luck next time!* Keep trying.\n"

                            await update.message.reply_text(msg, parse_mode="Markdown")
                        else:
                            await update.message.reply_text("❌ Failed to fetch allotment status. Please try again.")
                    else:
                        await update.message.reply_text("❌ API Error. Please try again later.")
                except Exception as e:
                    logger.error(f"Error checking allotment: {e}")
                    await update.message.reply_text("❌ An error occurred. Please try again.")

    elif text == "⬅️ Previous":
        # Handle previous page
        current_page = context.user_data.get("current_page", 0)
        if current_page > 0:
            new_page = current_page - 1
            # Simulate callback for previous page
            class FakeQuery:
                def __init__(self):
                    self.from_user = update.message.from_user
                    self.data = f"ipo_list_{new_page}"
                async def answer(self):
                    pass
                class FakeMessage:
                    async def reply_text(self, *args, **kwargs):
                        await update.message.reply_text(*args, **kwargs)
                message = FakeMessage()

            fake_query = FakeQuery()
            fake_update = type('obj', (object,), {'callback_query': fake_query})()
            await handle_buttons(fake_update, context)
        else:
            await update.message.reply_text("❌ Already on first page.")

    elif text == "Next ➡️":
        # Handle next page
        current_page = context.user_data.get("current_page", 0)
        res = requests.get(API_URL, timeout=10)
        if res.status_code == 200:
            ipos = res.json().get("data", [])
            total_ipos = len(ipos)
            total_pages = (total_ipos + IPOS_PER_PAGE - 1) // IPOS_PER_PAGE

            if current_page < total_pages - 1:
                new_page = current_page + 1
                # Simulate callback for next page
                class FakeQuery:
                    def __init__(self):
                        self.from_user = update.message.from_user
                        self.data = f"ipo_list_{new_page}"
                    async def answer(self):
                        pass
                    class FakeMessage:
                        async def reply_text(self, *args, **kwargs):
                            await update.message.reply_text(*args, **kwargs)
                    message = FakeMessage()

                fake_query = FakeQuery()
                fake_update = type('obj', (object,), {'callback_query': fake_query})()
                await handle_buttons(fake_update, context)
            else:
                await update.message.reply_text("❌ Already on last page.")

    elif text == "🔄 Refresh IPO List":
        # Handle refresh - go back to page 0
        class FakeQuery:
            def __init__(self):
                self.from_user = update.message.from_user
                self.data = "ipo_list_0"
            async def answer(self):
                pass
            class FakeMessage:
                async def reply_text(self, *args, **kwargs):
                    await update.message.reply_text(*args, **kwargs)
            message = FakeMessage()

        fake_query = FakeQuery()
        fake_update = type('obj', (object,), {'callback_query': fake_query})()
        await handle_buttons(fake_update, context)

    elif text == "📋 Manage PAN Numbers":
        # Show PAN management menu with reply keyboard
        msg = "📋 *PAN Number Management*\n\n"
        msg += "Choose an option:"

        # Reply keyboard for PAN management
        reply_keyboard = [
            ["➕ Add PAN Number", "❌ Delete PAN Number"],
            ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

    elif text == "➕ Add PAN Number":
        # Handle Add PAN Number button
        pan_count = get_pan_count(user_id)

        # Check if user has reached the limit
        if pan_count >= 20:
            msg = "❌ *Limit Reached*\n\n"
            msg += "You have reached the maximum limit of 20 PAN numbers.\n"
            msg += "Please delete some PANs before adding new ones."

            # Show PAN management keyboard
            reply_keyboard = [
                ["➕ Add PAN Number", "❌ Delete PAN Number"],
                ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
            ]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            context.user_data["awaiting_pan"] = True
            msg = f"📋 *Add PAN Number* ({pan_count}/20)\n\n"
            msg += "Please send your PAN details in one of these formats:\n\n"
            msg += "*Format 1:* PAN only\n"
            msg += "`ABCDE1234F`\n\n"
            msg += "*Format 2:* PAN with name\n"
            msg += "`ABCDE1234F  John Doe`\n\n"
            msg += "💡 Tip: Separate PAN and name with a space"

            # Show only Back to PAN Management button while waiting for PAN input
            reply_keyboard = [
                ["🔙 Back to PAN Management"]
            ]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

    elif text == "ℹ️ Help":
        # Show help message
        msg = "📚 *How to use IPO Allotment Bot:*\n\n"

        msg += "*1. Manage PAN Numbers* 📋\n"
        msg += "➕ Add PAN numbers with names (e.g., \"John Doe\")\n"
        msg += "❌ Delete PAN numbers you no longer need\n"
        msg += "👁️ View all your saved PAN numbers\n\n"

        msg += "*2. Check IPO Allotment* 📊\n"
        msg += "🔍 Click \"Check IPO Allotment\"\n"
        msg += "📝 Select an IPO from the available list\n"
        msg += "📈 Get allotment status for all your PAN numbers\n\n"

        msg += "*Commands:*\n"
        msg += "▶️ /start - Start the bot and show main menu\n"
        msg += "ℹ️ /help - Show this help message\n\n"

        msg += "*Flow:*\n"
        msg += "1️⃣ Add your PAN numbers\n"
        msg += "2️⃣ Click \"Check IPO Allotment\"\n"
        msg += "3️⃣ Choose an IPO\n"
        msg += "4️⃣ View results for all PANs\n\n"

        msg += "💡 Use the keyboard buttons below to navigate!"

        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "❌ Delete PAN Number":
        # Show list of PANs to delete
        pans = get_all_pans(user_id)
        if not pans:
            msg = "❌ *No PAN Numbers Found*\n\n"
            msg += "You don't have any PAN numbers saved yet.\n"
            msg += "Add a PAN number first to get started."

            # Show PAN management keyboard
            reply_keyboard = [
                ["➕ Add PAN Number", "❌ Delete PAN Number"],
                ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
            ]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            # Store PANs in user context for deletion
            context.user_data["pans_for_deletion"] = pans

            msg = "❌ *Delete PAN Number*\n\n"
            msg += "Select a PAN to delete from the keyboard below:"

            # Create keyboard with PAN list (2 buttons per row)
            reply_keyboard = []
            for idx, pan_data in enumerate(pans, 1):
                name = pan_data['name']
                pan = pan_data['pan']
                button_text = f"🗑️ Delete {idx}: {pan} - {name}"

                # Add 2 buttons per row
                if idx % 2 == 1:
                    reply_keyboard.append([button_text])
                else:
                    reply_keyboard[-1].append(button_text)

            # Add back button
            reply_keyboard.append(["🔙 Back to PAN Management"])

            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

    elif text == "📋 View PAN Numbers":
        # Show all PANs for the user
        pans = get_all_pans(user_id)
        total_pans = len(pans)

        if not pans:
            msg = "📋 *Your PAN Numbers:* (0/20)\n\n"
            msg += "❌ No PAN numbers saved yet.\n\n"
            msg += "💡 Add your first PAN to start checking IPO allotments."
        else:
            msg = f"📋 *Your PAN Numbers:* ({total_pans}/20)\n\n"
            for idx, pan_data in enumerate(pans, 1):
                msg += f"👤 {idx}. *{pan_data['name']}*\n"
                msg += f"   📄 PAN: `{pan_data['pan']}`\n\n"

        # Show PAN management keyboard
        reply_keyboard = [
            ["➕ Add PAN Number", "❌ Delete PAN Number"],
            ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

    elif text == "🔙 Back to PAN Management":
        # Clear deletion state and go back to PAN management
        context.user_data["pans_for_deletion"] = None
        context.user_data["awaiting_pan"] = False

        # Show PAN management keyboard
        reply_keyboard = [
            ["➕ Add PAN Number", "❌ Delete PAN Number"],
            ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await update.message.reply_text("📋 *PAN Number Management*", reply_markup=reply_markup, parse_mode="Markdown")

    elif text == "🔙 Back to Main Menu":
        # Clear any pending state
        context.user_data["awaiting_pan"] = False
        context.user_data["pans_for_deletion"] = None

        # Show Main Menu keyboard
        reply_keyboard = [
            ["📋 Manage PAN Numbers", "📊 Check IPO Allotment"],
            ["ℹ️ Help"]
        ]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        await update.message.reply_text("🏠 *Main Menu*", reply_markup=reply_markup, parse_mode="Markdown")

    elif text.startswith("🗑️ Delete "):
        # Handle delete PAN button press
        pans = context.user_data.get("pans_for_deletion", [])
        if not pans:
            await update.message.reply_text("❌ Error: No PANs available for deletion.")
            return

        # Extract the index from button text (e.g., "🗑️ Delete 1: ABCDE1234F - John Doe" -> 1)
        try:
            # Remove the prefix "🗑️ Delete " and split by ":"
            # Format: "🗑️ Delete 1: ABCDE1234F - John Doe"
            text_without_prefix = text.replace("🗑️ Delete ", "").strip()
            # Split by ":" to separate index from rest
            parts = text_without_prefix.split(":", 1)
            pan_index = int(parts[0].strip()) - 1  # Convert to 0-based index

            if 0 <= pan_index < len(pans):
                pan_data = pans[pan_index]
                pan_id = pan_data['id']
                name = pan_data['name']
                pan = pan_data['pan']

                # Delete the PAN
                delete_pan_by_id(pan_id)

                msg = f"✅ *PAN Deleted Successfully*\n\n"
                msg += f"🗑️ Deleted: `{pan}` - *{name}*"

                # Clear deletion state
                context.user_data["pans_for_deletion"] = None

                # Show PAN management keyboard
                reply_keyboard = [
                    ["➕ Add PAN Number", "❌ Delete PAN Number"],
                    ["📋 View PAN Numbers", "🔙 Back to Main Menu"]
                ]
                reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
                await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Invalid PAN selection.")
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing delete button: {e}")
            logger.error(f"Button text was: {text}")
            await update.message.reply_text("❌ Error processing deletion.")

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

async def run_bot_with_retry():
    """Run bot with automatic restart on failure - Optimized for Render"""
    max_retries = 10
    retry_count = 0
    retry_delay = 3  # Start with 3 seconds
    max_retry_delay = 60  # Max 1 minute between retries

    while True:
        try:
            BOT_TOKEN = os.getenv("BOT_TOKEN")
            WEBHOOK_URL = os.getenv("WEBHOOK_URL")
            PORT = int(os.getenv("PORT", 10000))
            USE_WEBHOOK = os.getenv("USE_WEBHOOK", "true").lower() == "true"

            if not BOT_TOKEN:
                logger.error("❌ BOT_TOKEN not set in environment variables")
                sys.exit(1)

            app = ApplicationBuilder().token(BOT_TOKEN).build()

            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("help", help_command))
            app.add_handler(CallbackQueryHandler(handle_buttons))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

            # Add error handler
            app.add_error_handler(error_handler)

            logger.info("🚀 Bot is starting...")
            print("🚀 Bot is starting...")

            if USE_WEBHOOK and WEBHOOK_URL:
                # Webhook mode for production (Render)
                logger.info(f"Using webhook mode: {WEBHOOK_URL}")
                try:
                    app.run_webhook(
                        listen="0.0.0.0",
                        port=PORT,
                        url_path=BOT_TOKEN,
                        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
                        allowed_updates=Update.ALL_TYPES,
                        drop_pending_updates=True
                    )
                except Exception as e:
                    logger.error(f"❌ Webhook error: {e}")
                    raise
            else:
                # Polling mode for local development with retry
                logger.info("Using polling mode with auto-restart")
                await app.initialize()
                await app.start()

                try:
                    # Run polling with timeout handling
                    await app.updater.start_polling(
                        allowed_updates=Update.ALL_TYPES,
                        drop_pending_updates=True,
                        timeout=30,
                        read_timeout=15,
                        write_timeout=15,
                        connect_timeout=15,
                        pool_timeout=15
                    )
                except Exception as e:
                    logger.error(f"❌ Polling error: {e}")
                    raise
                finally:
                    await app.stop()
                    await app.shutdown()

        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            print("🛑 Bot stopped by user")
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Bot crashed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"❌ Bot crashed: {e}")

            if retry_count >= max_retries:
                logger.error(f"❌ Max retries ({max_retries}) reached. Render will restart the service.")
                print(f"❌ Max retries ({max_retries}) reached. Render will restart the service.")
                sys.exit(1)

            logger.info(f"🔄 Restarting bot in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")
            print(f"🔄 Restarting bot in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")

            await asyncio.sleep(retry_delay)

            # Exponential backoff: increase delay for next retry
            retry_delay = min(retry_delay * 1.5, max_retry_delay)

def main():
    """Main entry point"""
    try:
        asyncio.run(run_bot_with_retry())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped")
        print("🛑 Bot stopped")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

