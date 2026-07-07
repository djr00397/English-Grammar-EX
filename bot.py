import os
import json
import asyncio
import uuid
import logging
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- কনফিগারেশন ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1004329287779") # আপনার সঠিক আইডি এখানে দিন
ADDSTAR_LINK = "https://www.effectivecpmnetwork.com/d3zp257u?key=17a91a0db9aa186628c02308b1b20e9a"

genai.configure(api_key=API_KEY)
bot = Bot(token=TOKEN)
DATA_FILE = 'data.json'

# --- ডাটাবেস ফাংশন ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {"users": {}, "last_update_id": 0, "last_leaderboard_month": 0}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- ইমেজ ফাংশন (ফন্ট এররমুক্ত) ---
def create_notebook_image():
    img = Image.new('RGB', (800, 300), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # ডিফল্ট ফন্ট ব্যবহার করা হয়েছে যাতে এরর না হয়
    d.text((50, 50), "Advanced English Grammar Challenge\nTest your limits!", fill=(0,0,0))
    bio = BytesIO()
    bio.name = 'quiz.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

async def main():
    logger.info("Bot is running...")
    
    # জেমিনি থেকে প্রশ্ন নেওয়া
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = "Give 3 hard grammar MCQ in JSON: [{'question': '...', 'options': {'A':'', 'B':'', 'C':'', 'D':''}, 'correct': 'A'}]"
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        questions = json.loads(text)
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return

    # চ্যানেলে পোস্ট করা
    try:
        image = create_notebook_image()
        await bot.send_photo(chat_id=CHANNEL_ID, photo=image, caption="📚 **Today's Quiz**")
        
        for q in questions:
            keyboard = []
            for key, val in q['options'].items():
                if key == q['correct']:
                    keyboard.append([InlineKeyboardButton(f"✅ {key}: {val}", callback_data="correct")])
                else:
                    keyboard.append([InlineKeyboardButton(f"❌ {key}: {val}", url=ADDSTAR_LINK)])
            
            await bot.send_message(chat_id=CHANNEL_ID, text=f"❓ {q['question']}", reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info("Successfully posted to channel!")
    except Exception as e:
        logger.error(f"Telegram Post Error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
