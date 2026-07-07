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

def get_seo_content_from_gemini():
    # প্রম্পটে পরিবর্তন আনা হয়েছে যাতে উত্তর সবসময় 'A' না হয়
    prompt = """
    Create an advanced English Grammar Lesson. Topic: Inversion/Subjunctive/Participle.
    Output MUST be valid JSON. 
    Make sure the correct_index (0-3) is randomized for every question.
    
    {
      "topic": "Title Here",
      "formula": "Concise rule.",
      "seo_caption": "Caption with hashtags.",
      "questions": [
        {
          "question": "Question text?",
          "options": ["A", "B", "C", "D"],
          "correct_index": (Random number between 0 and 3),
          "explanation": "Brief explanation."
        }
      ]
    }
    Generate 3 questions.
    """
    try:
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(response_mime_type="application/json"))
        return json.loads(response.text.strip())
    except Exception as e:
        return None # এরর হলে অটোমেটিক্যালি হ্যান্ডেল হবে

def create_notebook_image(topic, formula):
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
    content = get_seo_content_from_gemini()
    if not content: return
    create_notebook_image(content["topic"], content["formula"])
    
    with open("lesson.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=f"📘 **Topic:** {content['topic']}\n\n{content['seo_caption']}", parse_mode="Markdown")
    
    for index, q in enumerate(content["questions"], start=1):
        bot.send_poll(
            chat_id=CHANNEL_ID,
            question=f"{index}. {q['question']}",
            options=q["options"],
            type="quiz",
            correct_option_id=q["correct_index"],
            explanation=q.get("explanation", "Correct Answer"),
            is_anonymous=True
        )
        time.sleep(3)

if __name__ == "__main__":
    main()
    
