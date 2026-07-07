import os
import json
import time
import telebot
import google.generativeai as genai
from PIL import Image, ImageDraw

# এনভায়রনমেন্ট ভেরিয়েবল থেকে কনফিগারেশন
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)

# এআই কনফিগারেশন (উচ্চতর ক্রিয়েটিভিটির জন্য টেম্পারেচার ০.৯)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash-latest',
    generation_config={"temperature": 0.9}
)

def get_seo_content_from_gemini():
    prompt = """
    You are an expert English Grammar Tutor. Generate a unique grammar quiz in JSON format.
    
    1. TOPIC: Choose a completely random and different English grammar topic (e.g., Inversion, Conditionals, Gerunds, Modals, etc.).
    2. CONTENT: Provide a concise formula/rule and 3 challenging, unique MCQ questions.
    3. RANDOMIZATION: You MUST randomize the correct_index (0, 1, 2, or 3) for every question. Never keep it at index 0 always.
    4. SEO: Write an engaging 2-sentence caption with 5-7 trending, relevant hashtags.
    
    Output strictly in JSON format:
    {
      "topic": "Topic Name",
      "formula": "Concise rule/formula",
      "seo_caption": "Engaging caption with hashtags",
      "questions": [
        {
          "question": "Question text?",
          "options": ["Opt 1", "Opt 2", "Opt 3", "Opt 4"],
          "correct_index": 0,
          "explanation": "Brief explanation"
        }
      ]
    }
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error: {e}")
        return None

def create_notebook_image(topic, formula):
    # ইমেজ জেনারেশন
    img = Image.new('RGB', (800, 400), color='#F9F6EE')
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0), (800, 400)], outline="#B0C4DE", width=5)
    draw.text((50, 50), f"LESSON: {topic.upper()}", fill="#B22222", font_size=30)
    draw.text((50, 120), f"Formula/Rule:\n{formula}", fill="#333333", font_size=20)
    img.save("lesson.png")

def main():
    content = get_seo_content_from_gemini()
    if not content: return

    # ইমেজ তৈরি
    create_notebook_image(content["topic"], content["formula"])
    
    # ক্যাপশন ও ছবি পাঠানো
    caption = f"📘 *Topic: {content['topic']}*\n\n{content['seo_caption']}"
    with open("lesson.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=caption, parse_mode="Markdown")
    
    # কুইজ পাঠানো
    for index, q in enumerate(content["questions"], start=1):
        bot.send_poll(
            chat_id=CHANNEL_ID,
            question=f"{index}. {q['question']}",
            options=q["options"],
            type="quiz",
            correct_option_id=q["correct_index"],
            explanation=q["explanation"],
            is_anonymous=True
        )
        time.sleep(3)

if __name__ == "__main__":
    main()
    
