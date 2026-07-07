import os
import time
import json
import telebot
import textwrap
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# GitHub Secrets থেকে ডেটা রিড
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)

model = genai.GenerativeModel('gemini-1.5-flash-latest')

def get_seo_content_from_gemini():
    prompt = """
    Create an advanced English Grammar Lesson.
    1. Topic: Choose a unique advanced topic (e.g., Subjunctive, Inversion, Participle Clauses, etc.).
    2. Formula: A clear, concise rule.
    3. SEO Caption: Catchy text ending with #IELTS #EnglishGrammarEX and 4-5 relevant dynamic hashtags.
    4. MCQs: 3 challenging questions with 4 options. Randomize 'correct_index' (0-3).
    
    Output MUST be valid JSON only (no markdown, no tags).
    {
      "topic": "Topic Name",
      "formula": "Concise rule.",
      "seo_caption": "Engaging caption with hashtags.",
      "questions": [
        {"question": "Q?", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "Why?"}
      ]
    }
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print("API Error:", e)
        return None

def create_notebook_image(topic, formula):
    # ইমেজ সাইজ বড় করা হয়েছে (১২০০x৯০০)
    img = Image.new('RGB', (1200, 900), color='#F9F6EE')
    draw = ImageDraw.Draw(img)
    
    # ব্যাকগ্রাউন্ড দাগ
    for y in range(150, 900, 60):
        draw.line([(0, y), (1200, y)], fill="#B0C4DE", width=2)
    draw.line([(120, 0), (120, 900)], fill="#FA8072", width=5)
    
    # হেডিং ও টেক্সট
    draw.text((150, 50), f"LESSON: {topic.upper()}", fill="#B22222", font_size=40)
    draw.text((150, 160), "📌 FORMULA & RULES:", fill="#000080", font_size=35)
    
    # লেখা টেক্সট র‍্যাপ করা যাতে বড় না হয়
    wrapper = textwrap.TextWrapper(width=60)
    lines = wrapper.wrap(text=formula)
    
    y_offset = 220
    for line in lines:
        draw.text((150, y_offset), line, fill="#333333", font_size=30)
        y_offset += 50
        
    img.save("lesson.png")

def main():
    content = get_seo_content_from_gemini()
    if not content: return
        
    create_notebook_image(content["topic"], content["formula"])
    
    caption = f"📘 **Topic:** {content['topic']}\n\n{content['seo_caption']}"
    
    with open("lesson.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=caption, parse_mode="Markdown")
    
    for index, q in enumerate(content["questions"], start=1):
        bot.send_poll(
            chat_id=CHANNEL_ID,
            question=f"{index}. {q['question']}",
            options=q["options"],
            type="quiz",
            correct_option_id=q["correct_index"],
            explanation=q.get("explanation", "Keep learning!"),
            is_anonymous=True
        )
        time.sleep(2)

if __name__ == "__main__":
    main()
        
