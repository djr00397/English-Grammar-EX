import os
import time
import json
import telebot
import google.generativeai as genai
from PIL import Image, ImageDraw

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def get_seo_content():
    prompt = """
    Create an advanced English Grammar Lesson. Topic: Inversion/Subjunctive/Participle.
    Return ONLY valid JSON. Randomize correct_index (0-3).
    {
      "topic": "Title",
      "formula": "Concise rule.",
      "seo_caption": "Caption with hashtags.",
      "questions": [
        {"question": "Q?", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "Briefly why."}
      ]
    }
    Generate 3 questions.
    """
    try:
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(response_mime_type="application/json"))
        return json.loads(response.text.strip())
    except: return None

def create_image(topic, formula):
    img = Image.new('RGB', (800, 800), color='#F9F6EE')
    draw = ImageDraw.Draw(img)
    for y in range(120, 800, 50): draw.line([(0, y), (800, y)], fill="#B0C4DE", width=2)
    draw.line([(100, 0), (100, 800)], fill="#FA8072", width=3)
    draw.text((120, 50), f"GRAMMAR LESSON: {topic.upper()}", fill="#B22222", font_size=28)
    draw.text((120, 130), "📌 FORMULA & RULES:", fill="#000080", font_size=24)
    y_offset = 180
    for line in formula.split('\n'):
        draw.text((120, y_offset), line, fill="#333333", font_size=22)
        y_offset += 50
    img.save("lesson.png")

def main():
    data = get_seo_content()
    if not data: return
    create_image(data["topic"], data["formula"])
    with open("lesson.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=f"📘 **Topic:** {data['topic']}\n\n{data['seo_caption']}", parse_mode="Markdown")
    for i, q in enumerate(data["questions"], 1):
        bot.send_poll(CHANNEL_ID, f"{i}. {q['question']}", q["options"], type="quiz", correct_option_id=q["correct_index"], is_anonymous=True)
        time.sleep(3)

if __name__ == "__main__":
    main()
    
