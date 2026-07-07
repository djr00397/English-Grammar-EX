import os
import time
import json
import telebot
import google.generativeai as genai
from PIL import Image, ImageDraw

# GitHub Secrets থেকে ডেটা রিড
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)

# লেটেস্ট গুগল মডেল
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def get_seo_content_from_gemini():
    """Generates Random English Grammar Content with Randomized Answers."""
    prompt = """
    Select a random, challenging English grammar topic. 
    Create 3 unique MCQ questions. 
    IMPORTANT: Randomize the correct answer index (0, 1, 2, or 3) for each question. Do not keep it always at 0.
    Output MUST be valid JSON only.
    
    {
      "topic": "Name of the topic",
      "formula": "Concise grammar rule",
      "seo_caption": "2-sentence engaging caption with 5-7 trending hashtags",
      "questions": [
        {
          "question": "Question text?",
          "options": ["A", "B", "C", "D"],
          "correct_index": 1,
          "explanation": "Why this is correct."
        }
      ]
    }
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        # JSON ক্লিন করা
        return json.loads(response.text.strip())
    except Exception as e:
        print("API Error:", e)
        return None

def create_notebook_image(topic, formula):
    """Creates a professional grammar notebook style image."""
    img = Image.new('RGB', (800, 800), color='#F9F6EE')
    draw = ImageDraw.Draw(img)
    
    for y in range(120, 800, 50):
        draw.line([(0, y), (800, y)], fill="#B0C4DE", width=2)
    draw.line([(100, 0), (100, 800)], fill="#FA8072", width=3)
    
    draw.text((120, 50), f"GRAMMAR: {topic.upper()}", fill="#B22222")
    draw.text((120, 130), "📌 FORMULA:", fill="#000080")
    
    y_offset = 180
    for line in formula.split('\n'):
        draw.text((120, y_offset), line, fill="#333333")
        y_offset += 50
        
    img.save("lesson.png")

def main():
    print("Starting Automated Grammar Bot...")
    
    content = get_seo_content_from_gemini()
    if not content:
        print("Failed to get content.")
        return

    create_notebook_image(content["topic"], content["formula"])
    
    caption = f"📘 Topic: {content['topic']}\n\n{content['seo_caption']}"
    
    with open("lesson.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=caption, parse_mode="Markdown")
    
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
        
    print("Post sent successfully!")

if __name__ == "__main__":
    main()
    
