import os
import sys
from telethon import TelegramClient, events  # <-- FIX IS HERE
import google.generativeai as genai

# --- 1. CONFIGURATION FOR CIPHERCOIN ---
# Securely load credentials from environment variables.
API_ID = 24606973
API_HASH = os.environ.get('API_HASH')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
SESSION_NAME = 'ciphercoin-session'

# Verify that credentials were loaded
if not all([API_HASH, GEMINI_API_KEY]):
    print("❌ FATAL ERROR: API_HASH or GEMINI_API_KEY not found in environment variables.")
    print("Please set them in your console before running the script.")
    sys.exit(1)

# --- AI Instructions for CipherCoin ---
BUSINESS_INSTRUCTIONS = """
You are "CipherCoin Support", a helpful and friendly assistant for the CipherCoin crypto mixing platform.
Your goal is to act like a real person helping out, not a robot.

**Your Personality & Style:**
- Be conversational and friendly. Use a human-like tone.
- Keep your replies short and clear. Avoid long paragraphs. Use line breaks to make things easy to read.
- Your entire reply should not exceed 15 lines.
- Use emojis sometimes to make the conversation feel more natural. 👍
- If you don't know something, it's okay to say so. Just be helpful.

**Core Service Information:**
- CipherCoin is a non-custodial crypto mixer. We help users break the link between their old and new transactions for better privacy.
- We have a strict no-logs policy. 🕵️‍♂️
- The process is easy: 1. Get your new wallet address ready. 2. Send coins to the address we provide. 3. Receive clean coins in your new wallet.
- We support cryptos like Bitcoin (BTC), Ethereum (ETH), and Litecoin (LTC).
- Users can add a time delay for extra anonymity.

**CRITICAL SAFETY RULES:**
- **Never** give financial advice. No price talk!
- **Never** ask for private keys, seed phrases, or passwords. Ever.
- For specific transaction problems, guide them to the official support on cipher-coin.com.
- If asked about illegal stuff, just say: "Our service is for legitimate financial privacy only."
- Always point to cipher-coin.com as the main source of info.
"""

# --- 2. SETUP CLIENTS ---

# Configure the Gemini client.
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=BUSINESS_INSTRUCTIONS
    )
    print("✅ Gemini AI model configured with a human-like personality.")
except Exception as e:
    print(f"❌ Error configuring Gemini AI: {e}")
    sys.exit(1)

# Configure Telegram client for PythonAnywhere Paid Accounts
# On Zeabur, no proxy or special connection is needed.
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# --- 3. EVENT HANDLER FOR NEW MESSAGES ---

@client.on(events.NewMessage(incoming=True))
async def auto_reply(event):
    """Handles incoming customer messages for CipherCoin."""
    sender = await event.get_sender()
    me = await client.get_me()

    if sender.id == me.id or event.is_group:
        return

    incoming_msg = event.message.message
    print(f"📩 Customer message from {sender.username or sender.id}: {incoming_msg}")

    try:
        chat_response = model.generate_content(incoming_msg)
        reply_text = chat_response.text
    except Exception as e:
        reply_text = "Oops, having a little trouble connecting right now. 😅 Please try again in a moment, or check out our website cipher-coin.com!"
        print(f"❌ AI Error: {str(e)}")

    await event.reply(reply_text)
    print(f"✅ Replied: {reply_text}")

# --- 4. RUN THE BOT ---

def main():
    """Main function to start the bot."""
    print("🤖 CipherCoin Telegram Bot is starting...")
    client.start()
    print("✅ Bot is connected and ready to chat with customers.")
    client.run_until_disconnected()

if __name__ == '__main__':
    main()
  
