#
# This is the final version, modified to run in Termux by removing the google-generativeai dependency.
#

import os
import datetime
import logging
import asyncio
import requests # Use the requests library
import json     # Use the json library

# Imports for python-telegram-bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from telegram.error import TelegramError
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove

# --- CONFIGURATION & TOKENS ---
TOKEN = os.environ.get("TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- LOGGING SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- NEW GEMINI SETUP (using requests) ---

#
# ----- REPLACE your old ask_gemini function with this entire block -----
#
async def ask_gemini(prompt: str) -> str:
    """
    Sends a prompt to the Gemini API using a simple HTTP request with a system instruction.
    """
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found in environment variables.")
        return "Sorry, my AI configuration is missing."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    # This is the new, more powerful system instruction
    system_prompt = {
        "parts": [{
            "text": "You are a professional, helpful, and concise project management assistant for the CipherCoin Team. Your answers must always be brief and to the point, with a maximum of 4 sentences. Do not use conversational fluff."
        }]
    }
    
    # The JSON payload now includes the system instruction
    data = {
        "contents": [{
            "parts": [{
                "text": prompt  # The user's question is now clean
            }]
        }],
        "system_instruction": system_prompt
    }

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(url, headers=headers, json=data, timeout=20))
        response.raise_for_status()
        
        result_json = response.json()
        
        # Safer parsing
        candidates = result_json.get('candidates')
        if candidates and isinstance(candidates, list) and len(candidates) > 0:
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if parts and isinstance(parts, list) and len(parts) > 0:
                return parts[0].get('text', "Sorry, I couldn't extract the text.").strip()

        logger.warning(f"Unexpected Gemini response structure: {result_json}")
        return "Sorry, I received an unusual response from my AI brain."
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini API request failed: {e}")
        return "Sorry, I'm having trouble connecting with my AI brain right now. Please try again later. 🧠"
    except (KeyError, IndexError) as e:
        logger.error(f"Failed to parse Gemini response: {e}")
        return "Sorry, I received an unusual response from my AI brain."



# --- USER DATA ---
# User Access Control (User Name -> User ID)
user_access = {
    "Anwar": 11111111, "Alaudeen": 22222222, "Musaraf": 1459790806, "Riyas": 6258844344,
    "Sahul": 7974817901, "Boopathi": 6028405161, "Ijas": 1824958978, "Jaila": 1624253775
}

# Detailed Profile Data for Each User
USER_DATA = {
    "Anwar": {
        "team_id": "0101", "login": "anwar0101@gmail.com", "role": "Operation Team Leader",
        "members": ["Ajay", "Asik", "Fathah"], "groups": []
    },
    "Alaudeen": {
        "team_id": "0102", "login": "alaudeen0102@gmail.com", "role": "Operation Team Leader",
        "members": ["Mujay", "Rabik", "Faizal"], "groups": ["https://t.me/penghasiluang_online1", "https://t.me/yZnNkN"]
    },
    "Musaraf": {
        "team_id": "0103", "login": "musaraf0103@gmail.com", "role": "Operation Team Leader",
        "members": ["Mansoor", "Jassim", "Buhari"], "groups": ["https://t.me/newplatformchat", "https://t.me/epicballad_ind"]
    },
    "Riyas": {
        "team_id": "0104", "login": "riyas0104@gmail.com", "role": "Operation Team Leader",
        "members": ["Ismail", "Yousuf", "Suhair"], "groups": ["https://t.me/madmazellilekazanmayadevam", "https://t.me/Xland_com"]
    },
    "Sahul": {
        "team_id": "0105", "login": "sahul0105@gmail.com", "role": "Operation Team Leader",
        "members": ["Sameen", "Ajay_2", "Rahman"], "groups": ["https://t.me/+xfQQT3ZHzfNkM2Q6", "https://t.me/ALKEN_LUX_INVISTETSION_GROUP"]
    },
    "Boopathi": {
        "team_id": "0100", "login": "boopathi100@gmail.com", "role": "Project Manager",
        "members": ["Musaraf", "Sahul"], "groups": ["https://t.me/epic_balled_india", "https://t.me/RoyalWinOfficialGroup888", "https://t.me/merobit_net"]
    },
    "Ijas": {
        "team_id": "0100", "login": "ijas100@gmail.com", "role": "Project Manager",
        "members": ["Anwar", "Alaudeen", "Riyas"], "groups": ["https://t.me/epic_balled_india", "https://t.me/RoyalWinOfficialGroup888", "https://t.me/merobit_net"]
    },
    "Jaila": {
        "team_id": "0106", "login": "jaila0106@gmail.com", "role": "Operation Team Leader",
        "members": ["Team Member 1", "Team Member 2"], "groups": []
    }
}


# --- NOTIFICATION JOB FUNCTIONS (Sends to ALL users) ---

async def send_notification_to_all_users(context: ContextTypes.DEFAULT_TYPE, prompt: str, title: str):
    """A generic function to generate and send a notification to all users."""
    logger.info(f"Running job: {title}")
    message = await ask_gemini(prompt)
    full_message = f"*{title}*\n\n{message}"

    user_ids = user_access.values()
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=full_message, parse_mode='MarkdownV2')
            await asyncio.sleep(0.2)
        except TelegramError as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred for user {user_id}: {e}")


async def send_attendance_notification(context: ContextTypes.DEFAULT_TYPE):
    prompt = "Create a friendly and motivational morning message for the CipherCoin team, reminding them to mark their attendance. Keep it short and energetic."
    await send_notification_to_all_users(context, prompt, "☀️ Good Morning Team!")

async def send_task_update_notification(context: ContextTypes.DEFAULT_TYPE):
    prompt = "Write a brief, encouraging message for the CipherCoin team to update their task status for the day. Emphasize the importance of teamwork and progress."
    await send_notification_to_all_users(context, prompt, "📊 Afternoon Check-in!")

async def send_reward_notification(context: ContextTypes.DEFAULT_TYPE):
    prompt = "Compose a positive end-of-day message for the CipherCoin team. Appreciate their hard work and mention that completing tasks leads to rewards."
    await send_notification_to_all_users(context, prompt, "🎉 Day Complete!")


# --- BOT HANDLER FUNCTIONS ---

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_buttons = list(USER_DATA.keys())
    user_pairs = [user_buttons[i:i + 2] for i in range(0, len(user_buttons), 2)]
    keyboard_layout = [[KeyboardButton(f"🧑‍💻 {name}") for name in pair] for pair in user_pairs]
    keyboard_layout.append([KeyboardButton("✅ Login Now")])
    reply_markup = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True, one_time_keyboard=True)
    
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Please select your name from the keyboard below 👇\n\nOr use `/ask <your question>` for team-related queries.",
        reply_markup=reply_markup
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu(update, context)

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = " ".join(context.args)
    if not user_question:
        await update.message.reply_text("Please ask a question after the command. Example: `/ask How can we improve team productivity?`")
        return

    base_prompt = f"As a project management assistant for the CipherCoin Team, answer the following question: {user_question}"
    await update.message.reply_text("🤖 Thinking...")
    gemini_response = await ask_gemini(base_prompt)
    await update.effective_message.edit_text(f"🤔 *Your Question:*\n_{user_question}_\n\n🤖 *Gemini's Answer:*\n{gemini_response}", parse_mode='MarkdownV2')

# Replace your old handle_user_selection function with this one

async def handle_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input_text = update.message.text
    user_id = update.message.from_user.id

    # --- Start of Debugging Prints ---
    print("--- BUTTON CLICKED ---")
    print(f"Button Text Received: '{user_input_text}'")
    
    cleaned_name = user_input_text.lstrip("🧑‍💻 ")
    print(f"Cleaned Name: '{cleaned_name}'")
    print(f"Clicker's User ID: {user_id}")
    # --- End of Debugging Prints ---

    if user_input_text == "✅ Login Now":
        # ... (rest of your login button code is fine)
        return

    if cleaned_name in USER_DATA:
        expected_id = user_access.get(cleaned_name)
        print(f"Expected User ID for '{cleaned_name}': {expected_id}") # Added one more print here
        
        if user_id == expected_id:
            # ... (The rest of your code to show user info)
            # This part is likely correct.
        else:
            await update.message.reply_text(
                "❌ *Access Denied*. This profile is not for you.", parse_mode='MarkdownV2', reply_markup=ReplyKeyboardRemove()
            )
            print("--- RESULT: Access Denied (ID mismatch) ---") # Final debug status
    else:
        print("--- RESULT: Name not found in USER_DATA ---") # Final debug status



async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "show_main_menu":
        await query.message.delete()
        await send_main_menu(update, context)


# --- MAIN BOT SETUP ---
def main():
    if not TOKEN:
        logger.critical("TELEGRAM TOKEN not found in environment variables. The bot cannot start.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # --- Register Handlers ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CallbackQueryHandler(inline_button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_selection))

    # --- Schedule Daily Notification Jobs ---
    job_queue = app.job_queue
    # All times are in UTC. India is UTC+5:30.
    job_queue.run_daily(send_attendance_notification, time=datetime.time(hour=3, minute=30, tzinfo=datetime.timezone.utc), name="attendance_check")
    job_queue.run_daily(send_task_update_notification, time=datetime.time(hour=8, minute=30, tzinfo=datetime.timezone.utc), name="task_update")
    job_queue.run_daily(send_reward_notification, time=datetime.time(hour=12, minute=30, tzinfo=datetime.timezone.utc), name="reward_eod")

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
                                           
