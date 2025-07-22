import os
import datetime
import logging
import asyncio
import requests
import json
import pytz  # New import for timezones

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup

# --- CONFIGURATION & TOKENS ---
TOKEN = os.environ.get("TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- LOGGING SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- USER DATA & STATE MANAGEMENT ---
# Using a single structure for user data is cleaner
USER_DATA = {
    "Anwar":    {"id": 11111111, "team_id": "0101", "login": "anwar0101@gmail.com", "role": "Operation Team Leader", "members": ["Ajay", "Asik", "Fathah"], "groups": []},
    "Alaudeen": {"id": 22222222, "team_id": "0102", "login": "alaudeen0102@gmail.com", "role": "Operation Team Leader", "members": ["Mujay", "Rabik", "Faizal"], "groups": ["https://t.me/penghasiluang_online1", "https://t.me/yZnNkN"]},
    "Musaraf":  {"id": 1459790806, "team_id": "0103", "login": "musaraf0103@gmail.com", "role": "Operation Team Leader", "members": ["Mansoor", "Jassim", "Buhari"], "groups": ["https://t.me/newplatformchat", "https://t.me/epicballad_ind"]},
    "Riyas":    {"id": 6258844344, "team_id": "0104", "login": "riyas0104@gmail.com", "role": "Operation Team Leader", "members": ["Ismail", "Yousuf", "Suhair"], "groups": ["https://t.me/madmazellilekazanmayadevam", "https://t.me/Xland_com"]},
    "Sahul":    {"id": 7974817901, "team_id": "0105", "login": "sahul0105@gmail.com", "role": "Operation Team Leader", "members": ["Sameen", "Ajay_2", "Rahman"], "groups": ["https://t.me/+xfQQT3ZHzfNkM2Q6", "https://t.me/ALKEN_LUX_INVISTETSION_GROUP"]},
    "Boopathi": {"id": 6028405161, "team_id": "0100", "login": "boopathi100@gmail.com", "role": "Project Manager", "members": ["Musaraf", "Sahul"], "groups": ["https://t.me/epic_balled_india", "https://t.me/RoyalWinOfficialGroup888", "https://t.me/merobit_net"]},
    "Ijas":     {"id": 1824958978, "team_id": "0100", "login": "ijas100@gmail.com", "role": "Project Manager", "members": ["Anwar", "Alaudeen", "Riyas"], "groups": ["https://t.me/epic_balled_india", "https://t.me/RoyalWinOfficialGroup888", "https://t.me/merobit_net"]},
    "Jaila":    {"id": 1624253775, "team_id": "0106", "login": "jaila0106@gmail.com", "role": "Operation Team Leader", "members": ["Team Member 1", "Team Member 2"], "groups": []}
}

# In-memory attendance tracking
# It will reset to empty every day by a scheduled job
attendance_log = {
    'morning': set(),
    'evening': set()
}

# --- GEMINI API FUNCTION ---
async def ask_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found.")
        return "My AI configuration is missing."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    system_prompt = {
        "parts": [{"text": "You are a professional, helpful, and concise project management assistant for the CipherCoin Team. Your answers must always be brief and to the point, with a maximum of 4 sentences. Do not use conversational fluff."}]
    }
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "system_instruction": system_prompt
    }

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(url, headers=headers, json=data, timeout=20))
        response.raise_for_status()
        
        result_json = response.json()
        text_response = result_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "Sorry, I couldn't generate a proper response.")
        return text_response.strip()
    except Exception as e:
        logger.error(f"Gemini API request failed: {e}")
        return "I'm having trouble connecting to my AI brain right now."

# --- NOTIFICATION & JOB FUNCTIONS ---

async def send_task_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Sends an hourly task reminder to all users."""
    logger.info("Running hourly task reminder job.")
    prompt = "Create a very brief, one-line motivational reminder for the team to stay focused on their tasks."
    message = await ask_gemini(prompt)

    for user_data in USER_DATA.values():
        user_id = user_data.get('id')
        if user_id:
            try:
                await context.bot.send_message(chat_id=user_id, text=f"🔔 *Hourly Reminder*\n\n_{message}_", parse_mode='MarkdownV2')
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Failed to send reminder to user {user_id}: {e}")

async def reset_attendance_job(context: ContextTypes.DEFAULT_TYPE):
    """Resets the attendance log every day at midnight."""
    logger.info("Resetting daily attendance logs.")
    global attendance_log
    attendance_log['morning'].clear()
    attendance_log['evening'].clear()

# --- BOT HANDLER FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the main menu keyboard."""
    user_first_name = update.message.from_user.first_name
    
    user_buttons = [f"🧑‍💻 {name}" for name in USER_DATA.keys()]
    user_pairs = [user_buttons[i:i + 2] for i in range(0, len(user_buttons), 2)]
    
    keyboard_layout = user_pairs + [
        [KeyboardButton("☀️ Morning Attendance"), KeyboardButton("🌙 Evening Attendance")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Hi {user_first_name}, welcome to the CipherCoin Team Bot! Please choose an option.",
        reply_markup=reply_markup
    )

async def handle_profile_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, user_name: str):
    """Handles when a user clicks on a name button."""
    user_first_name = update.message.from_user.first_name
    clicked_user_id = update.message.from_user.id
    
    profile_data = USER_DATA.get(user_name)
    expected_user_id = profile_data.get('id')

    if clicked_user_id == expected_user_id:
        members_str = "\n".join([f"  - {member}" for member in profile_data['members']])
        groups_str = "\n".join([f"  - [Group Link {i+1}]({link})" for i, link in enumerate(profile_data['groups'])]) if profile_data['groups'] else "No groups assigned."
        
        reply_text = (
            f"Hi {user_first_name}, here is the info for *{user_name}*:\n\n"
            f"*Team ID*: {profile_data['team_id']}\n"
            f"*Role*: {profile_data['role']}\n"
            f"*Login*: `{profile_data['login']}`\n\n"
            f"*Team Members*:\n{members_str}\n\n"
            f"*Assignment Groups*:\n{groups_str}"
        )
        await update.message.reply_text(reply_text, parse_mode='MarkdownV2', disable_web_page_preview=True)
    else:
        await update.message.reply_text(f"Hi {user_first_name}, that's not for you! Access to *{user_name}*'s profile is denied.", parse_mode='MarkdownV2')

async def handle_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the attendance buttons."""
    user = update.message.from_user
    user_first_name = user.first_name
    user_id = user.id
    button_text = update.message.text

    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.datetime.now(ist)
    current_hour = now_ist.hour

    if "Morning" in button_text:
        if 6 <= current_hour < 15: # 6:00 AM to 2:59 PM
            if user_id in attendance_log['morning']:
                await update.message.reply_text(f"Hi {user_first_name}, you've already marked your morning attendance today.")
            else:
                attendance_log['morning'].add(user_id)
                await update.message.reply_text(f"✅ Got it, {user_first_name}! Your morning attendance is marked.")
        else:
            await update.message.reply_text(f"Hi {user_first_name}, morning attendance can only be marked between 6 AM and 3 PM IST.")
            
    elif "Evening" in button_text:
        if 18 <= current_hour < 23: # 6:00 PM to 10:59 PM
            if user_id in attendance_log['evening']:
                await update.message.reply_text(f"Hi {user_first_name}, you've already marked your evening attendance today.")
            else:
                attendance_log['evening'].add(user_id)
                await update.message.reply_text(f"✅ Thanks, {user_first_name}! Your evening attendance is marked.")
        else:
            await update.message.reply_text(f"Hi {user_first_name}, evening attendance can only be marked between 6 PM and 11 PM IST.")

async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The main router for all incoming text messages."""
    message_text = update.message.text
    user_first_name = update.message.from_user.first_name

    # Check if a profile button was clicked
    if message_text.startswith("🧑‍💻"):
        user_name = message_text.lstrip("🧑‍💻 ").strip()
        await handle_profile_selection(update, context, user_name)
        return

    # Check if an attendance button was clicked
    if "Attendance" in message_text:
        await handle_attendance(update, context)
        return

    # If it's none of the above, treat it as a direct message to the AI
    await update.message.reply_text("🤖 Thinking...", quote=True)
    gemini_response = await ask_gemini(message_text)
    await update.effective_message.edit_text(f"Hi {user_first_name}, here's what I think:\n\n{gemini_response}")

# --- MAIN BOT SETUP ---
def main():
    if not TOKEN:
        logger.critical("TELEGRAM TOKEN not found. The bot cannot start.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # --- Register Handlers ---
    app.add_handler(CommandHandler("start", start))
    # This single MessageHandler now routes all non-command text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_message))

    # --- Schedule Daily Notification Jobs ---
    job_queue = app.job_queue
    # 1. Hourly task reminder
    job_queue.run_repeating(send_task_reminder, interval=3600, first=30, name="hourly_reminder")
    # 2. Daily job to reset attendance logs at midnight IST (18:30 UTC)
    job_queue.run_daily(reset_attendance_job, time=datetime.time(hour=18, minute=30, tzinfo=datetime.timezone.utc), name="reset_attendance")
    
    logger.info("Bot is running with all new features...")
    app.run_polling()

if __name__ == '__main__':
    main()

