import os
import json
import asyncio
import uuid
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# --- সিক্রেট ও কনফিগারেশন ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@EnglishGrammarEX")
ADDSTAR_LINK = "https://www.effectivecpmnetwork.com/d3zp257u?key=17a91a0db9aa186628c02308b1b20e9a"

genai.configure(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
DATA_FILE = 'data.json'

# --- ডাটাবেস ফাংশন ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"users": {}, "last_update_id": 0, "last_leaderboard_month": 0}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- ভোট কাউন্ট সিস্টেম ---
async def process_pending_votes(data):
    """সারাদিনের জমা হওয়া উত্তরগুলো গিটহাবে সেভ করবে"""
    offset = data.get("last_update_id", 0) + 1
    try:
        updates = await bot.get_updates(offset=offset, timeout=10)
        for update in updates:
            data["last_update_id"] = update.update_id
            if update.callback_query:
                user = update.callback_query.from_user
                user_id = str(user.id)
                user_name = user.first_name
                cb_data = update.callback_query.data
                
                if user_id not in data["users"]:
                    data["users"][user_id] = {"name": user_name, "score": 0, "voted_questions": []}
                
                if cb_data.startswith("correct_"):
                    question_id = cb_data.split("_")[1]
                    # ডাবল ভোট চেক (একবার উত্তর দিলে আর পয়েন্ট পাবে না)
                    if question_id not in data["users"][user_id]["voted_questions"]:
                        data["users"][user_id]["score"] += 1
                        data["users"][user_id]["voted_questions"].append(question_id)
        save_data(data)
    except Exception as e:
        print("Error fetching votes:", e)

# --- লিডারবোর্ড ও ইনবক্স মেসেজ সিস্টেম ---
async def post_monthly_leaderboard(data):
    """মাসের ১ তারিখে চ্যানেলে লিস্ট এবং টপ ১০ জনকে ইনবক্সে মেসেজ দিবে"""
    current_month = datetime.now().month
    
    if datetime.now().day == 1 and data.get("last_leaderboard_month") != current_month:
        users = data.get("users", {})
        if not users: 
            return
        
        # বেশি পয়েন্ট পাওয়া ১০ জনকে সাজানো
        sorted_users = sorted(users.items(), key=lambda x: x[1]['score'], reverse=True)
        top_10 = sorted_users[:10]
        
        # ১. চ্যানেলের জন্য পোস্ট তৈরি
        channel_text = "🏆 **Global Grammar Masters - Monthly Leaderboard** 🏆\n\n"
        channel_text += "Here are our TOP 10 highest scorers of all time:\n\n"
        for i, (uid, info) in enumerate(top_10, 1):
            channel_text += f"*{i}.* {info['name']} — {info['score']} points\n"
        
        channel_text += "\nKeep answering the daily hard questions to climb the ranks! 🚀\n#Leaderboard #EnglishGrammarEX"
        await bot.send_message(chat_id=CHANNEL_ID, text=channel_text, parse_mode='Markdown')
        
        # ২. টপ ১০ জনের ইনবক্সে (DM) মেসেজ পাঠানো
        for rank, (uid, info) in enumerate(top_10, 1):
            dm_text = (
                f"🎉 **Congratulations {info['name']}!** 🎉\n\n"
                f"You have ranked **#{rank}** in our TOP 10 Grammar Masters list with a total of **{info['score']} points**! 🏆\n\n"
                f"Keep up the great work, maintain your top position, and invite your friends to challenge your score!\n\n"
                f"🔗 **Channel Link:** https://t.me/EnglishGrammarEX"
            )
            try:
                await bot.send_message(chat_id=uid, text=dm_text, parse_mode='Markdown')
            except Exception as e:
                # ইউজার যদি বট স্টার্ট না করে থাকে তবে এরর দিবে, কিন্তু কোড ক্র্যাশ করবে না
                print(f"Could not send DM to {info['name']}. Reason: {e}")
        
        data["last_leaderboard_month"] = current_month
        save_data(data)

# --- প্রশ্ন ও ছবি তৈরি ---
def generate_questions():
    """Gemini 1.5 Pro দিয়ে ৫টি কঠিন প্রশ্ন তৈরি"""
    model = genai.GenerativeModel('gemini-1.5-pro')
    prompt = """
    Create 5 extremely difficult, advanced English grammar MCQ questions.
    Return strictly a valid JSON array. Do not include markdown formatting like ```json.
    Format: [{"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "correct": "A"}]
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print("Gemini API Error:", e)
        return []

def create_notebook_image():
    """অ্যাডভান্সড গাইডলাইন খাতার ডিজাইন"""
    img = Image.new('RGB', (800, 400), color=(250, 250, 250))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    # খাতার মার্জিন ও লাইন
    d.line([(80, 0), (80, 400)], fill=(255, 100, 100), width=2) # লাল মার্জিন
    for i in range(80, 400, 50):
        d.line([(0, i), (800, i)], fill=(100, 150, 255), width=2) # নীল লাইন
    
    text = "📝 Advanced Grammar Guidelines\n\nPay attention to the hidden rules.\nToday's challenge is extremely hard!"
    d.text((100, 90), text, fill=(0, 0, 0), font=font)
    
    bio = BytesIO()
    bio.name = 'guideline.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

# --- মেইন এক্সিকিউশন ---
async def main():
    data = load_data()
    
    # ১. পুরোনো উত্তর আপডেট ও লিডারবোর্ড চেক
    await process_pending_votes(data)
    await post_monthly_leaderboard(data)
    
    # ২. জেমিনি থেকে প্রশ্ন তৈরি
    questions = generate_questions()
    if not questions:
        print("No questions generated. Exiting.")
        return
        
    # ৩. চ্যানেলে খাতার ছবি পোস্ট
    intro_text = "📚 **Today's Advanced English Challenge!**\n\nOnly the top 1% can answer these correctly. Test your limits!\n\n#AdvancedEnglish #GrammarRules #EnglishGrammarEX"
    image = create_notebook_image()
    await bot.send_photo(chat_id=CHANNEL_ID, photo=image, caption=intro_text, parse_mode='Markdown')
    
    # ৪. ৫টি এমসিকিউ পোস্ট করা
    for i, q in enumerate(questions):
        question_id = str(uuid.uuid4())[:8] # প্রশ্নের জন্য ইউনিক আইডি
        keyboard = []
        
        for key, value in q['options'].items():
            if key == q['correct']:
                keyboard.append([InlineKeyboardButton(f"✅ {key}: {value}", callback_data=f"correct_{question_id}")])
            else:
                keyboard.append([InlineKeyboardButton(f"❌ {key}: {value}", url=ADDSTAR_LINK)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(chat_id=CHANNEL_ID, text=f"❓ **Q{i+1}:** {q['question']}", reply_markup=reply_markup, parse_mode='Markdown')

if __name__ == '__main__':
    asyncio.run(main())
    
