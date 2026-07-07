import os
import json
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# ১. API Keys এবং Token সেটআপ (এগুলো GitHub Secrets থেকে আসবে)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # যেমন: @EnglishGrammarEX
ADDSTAR_LINK = "https://www.effectivecpmnetwork.com/d3zp257u?key=17a91a0db9aa186628c02308b1b20e9a"

genai.configure(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

# ২. জেমিনি দিয়ে কঠিন প্রশ্ন তৈরি করা
def generate_questions():
    model = genai.GenerativeModel('gemini-pro')
    prompt = """
    Act as an Advanced English Grammar Professor. 
    Create 5 extremely difficult MCQ questions about complex English grammar.
    For each question, provide:
    1. The question.
    2. Four options (A, B, C, D).
    3. The correct option letter.
    Format as JSON: [{"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "correct": "A"}]
    Ensure SEO keywords like #AdvancedEnglish #GrammarRules are used in a brief intro text.
    """
    response = model.generate_content(prompt)
    try:
        data = json.loads(response.text)
        return data
    except Exception as e:
        print("Error parsing Gemini response:", e)
        return None

# ৩. খাতার মতো ছবি তৈরি করা
def create_notebook_image(text_content):
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # এখানে ডিফল্ট ফন্ট ব্যবহার করা হচ্ছে। আপনি চাইলে .ttf ফন্ট ফাইল আপলোড করে লিঙ্ক দিতে পারেন।
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # খাতার লাইনের মতো দাগ দেওয়া
    for i in range(50, 600, 40):
        d.line([(0, i), (800, i)], fill=(200, 200, 255), width=2)
    
    # টেক্সট লেখা
    d.text((20, 60), "Advanced Grammar Guidelines\n" + text_content, fill=(0, 0, 0), font=font)
    
    bio = BytesIO()
    bio.name = 'image.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

# ৪. টেলিগ্রামে পোস্ট করা এবং বাটন সেট করা
async def post_to_telegram():
    questions = generate_questions()
    if not questions:
        return
    
    intro_text = "📚 **Master the Toughest Grammar Rules Today!**\n#AdvancedEnglish #GrammarRules #EnglishGrammarEX"
    image = create_notebook_image("Focus on the exceptions. The test begins now.")
    
    # ছবি পোস্ট করা
    await bot.send_photo(chat_id=CHANNEL_ID, photo=image, caption=intro_text, parse_mode='Markdown')
    
    # ৫টি প্রশ্ন পরপর পোস্ট করা
    for q in questions:
        keyboard = []
        options = q['options']
        correct_ans = q['correct']
        
        for key, value in options.items():
            if key == correct_ans:
                # সঠিক উত্তরের জন্য callback_data ব্যবহার করা হচ্ছে (এটি পরে লিডারবোর্ডের জন্য কাজে লাগবে)
                keyboard.append([InlineKeyboardButton(f"{key}: {value}", callback_data=f"correct_{key}")])
            else:
                # ভুল উত্তরের জন্য আপনার ডাইরেক্ট লিঙ্ক
                keyboard.append([InlineKeyboardButton(f"{key}: {value}", url=ADDSTAR_LINK)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(chat_id=CHANNEL_ID, text=f"❓ {q['question']}", reply_markup=reply_markup)

# ৫. মেইন ফাংশন রান করা
if __name__ == '__main__':
    import asyncio
    asyncio.run(post_to_telegram())
  
