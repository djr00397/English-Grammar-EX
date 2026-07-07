import os
import time
import json
import telebot
import google.generativeai as genai
from PIL import Image, ImageDraw

# এনভায়রনমেন্ট ভেরিয়েবল
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def main():
    # জেমিনি থেকে ডেটা নেওয়া
    prompt = "Create a grammar lesson (Topic, Formula, Caption, 3 Questions with options and correct_index). Return strictly valid JSON."
    response = model.generate_content(prompt)
    data = json.loads(response.text.replace("```json", "").replace("```", "").strip())

    # ইমেজ তৈরি
    img = Image.new('RGB', (800, 800), color='#F9F6EE')
    draw = ImageDraw.Draw(img)
    draw.text((120, 50), f"GRAMMAR: {data['topic'].upper()}", fill="#B22222", font_size=28)
    draw.text((120, 130), f"RULE: {data['formula']}", fill="#333333", font_size=22)
    img.save("lesson.png")

    # টেলিগ্রামে পোস্ট
    with open("lesson.png", "rb") as photo:
        bot.send_photo(os.getenv("CHANNEL_ID"), photo, caption=data['seo_caption'])
    
    for i, q in enumerate(data['questions'], 1):
        bot.send_poll(os.getenv("CHANNEL_ID"), f"{i}. {q['question']}", q['options'], type="quiz", correct_option_id=q['correct_index'], is_anonymous=True)
        time.sleep(2)

if __name__ == "__main__":
    main()
    
