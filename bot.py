import os
import json
import requests
import textwrap
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

genai.configure(api_key=GEMINI_API_KEY)

def get_grammar_data():
    model = genai.GenerativeModel('gemini-2.5-flash')
    # জেমিনিকে দিয়ে শুধু সূত্র এবং এমসিকিউ তৈরি করা হচ্ছে
    prompt = '''
    Create one advanced English Grammar rule, one example, and 3 hard MCQ questions.
    Output JSON:
    {
      "topic": "Topic Name",
      "rule": "One short, clear rule",
      "example": "One clear example",
      "questions": [
        {"q": "Q1", "options": ["A", "B", "C", "D", "E"], "correct": 0},
        {"q": "Q2", "options": ["A", "B", "C", "D", "E"], "correct": 1},
        {"q": "Q3", "options": ["A", "B", "C", "D", "E"], "correct": 2}
      ]
    }
    '''
    response = model.generate_content(prompt)
    return json.loads(response.text.replace('```json', '').replace('```', ''))

def create_clean_image(data):
    # কার্ড ডিজাইন - পরিষ্কার ব্যাকগ্রাউন্ড
    img = Image.new('RGB', (1000, 500), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # চ্যানেলের নাম
    draw.text((350, 30), "English Grammar EX", fill='#0000FF')
    # সূত্র ও উদাহরণ
    draw.text((50, 100), f"TOPIC: {data['topic']}", fill='#000000')
    draw.text((50, 150), f"RULE: {data['rule']}", fill='#FF0000')
    draw.text((50, 250), f"EXAMPLE: {data['example']}", fill='#008000')
    
    img.save("card.png")
    return "card.png"

def post_to_telegram(data):
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    img_path = create_clean_image(data)
    
    # ছবি পাঠানো
    with open(img_path, 'rb') as f:
        requests.post(base_url + "/sendPhoto", data={"chat_id": CHANNEL_ID}, files={"photo": f})
    
    # ৩টি এমসিকিউ বাটন পাঠানো
    for q in data['questions']:
        requests.post(base_url + "/sendPoll", data={
            "chat_id": CHANNEL_ID,
            "question": q['q'],
            "options": json.dumps(q['options']),
            "type": "quiz",
            "correct_option_id": q['correct'],
            "is_anonymous": False
        })

if __name__ == "__main__":
    data = get_grammar_data()
    post_to_telegram(data)
    
