import os
import time
import json
import random
import telebot
import textwrap
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# কনফিগারেশন
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def get_seo_content_from_gemini():
    # টপিক লিস্ট থেকে একটি রেন্ডম টপিক সিলেক্ট করা
    topics = ["Inversion", "Subjunctive Mood", "Participle Clauses", "Conditionals", "Cleft Sentences", "Relative Clauses"]
    target_topic = random.choice(topics)
    
    prompt = f"""
    Create an advanced English Grammar lesson about: {target_topic}.
    1. Formula: Give a clear, concise grammar rule.
    2. Caption: Engaging SEO-friendly text with 5 unique trending hashtags relevant to {target_topic}.
    3. Questions: Generate 3 difficult MCQs. Randomly shuffle the position of the correct answer (correct_index must be 0, 1, 2 or 3 randomly).
    
    Return ONLY pure JSON. No markdown formatting.
    {{
      "topic": "{target_topic}",
      "formula": "The exact rule string here.",
      "seo_caption": "Engaging text with hashtags.",
      "questions": [
        {{"question": "Q?", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "Why?"}}
      ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error: {e}")
        return None

def create_notebook_image(topic, formula):
    img = Image.new('RGB', (1000, 800), color='#F9F6EE')
    draw = ImageDraw.Draw(img)
    
    # ব্যাকগ্রাউন্ড ডিজাইন
    for y in range(100, 800, 50):
        draw.line([(0, y), (1000, y)], fill="#D3D3D3", width=1)
    draw.line([(100, 0), (100, 800)], fill="#FFB6C1", width=5)
    
    # বড় টেক্সট লেখার জন্য ডিফল্ট ফন্ট সাইজ বাড়ানো
    # লিনাক্স এনভায়রনমেন্টে ডিফল্ট ফন্ট ছোট হয়, তাই আমরা মাল্টিপল লাইন টেক্সট র‍্যাপ করছি
    draw.text((120, 30), f"LESSON: {topic}", fill="#8B0000") # শিরোনাম
    
    wrapper = textwrap.TextWrapper(width=50)
    lines = wrapper.wrap(text=formula)
    
    y_pos = 120
    for line in lines:
        draw.text((120, y_pos), line, fill="#000000")
        y_pos += 40
        
    img.save("lesson.png")

def main():
    content = get_seo_content_from_gemini()
    if not content: return
        
    create_notebook_image(content["topic"], content["formula"])
    
    # পোস্ট করা
    with open("lesson.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=f"📘 **Topic:** {content['topic']}\n\n{content['seo_caption']}", parse_mode="Markdown")
    
    for q in content["questions"]:
        bot.send_poll(
            chat_id=CHANNEL_ID,
            question=q["question"],
            options=q["options"],
            type="quiz",
            correct_option_id=q["correct_index"],
            explanation=q["explanation"],
            is_anonymous=True
        )
        time.sleep(2)

if __name__ == "__main__":
    main()
