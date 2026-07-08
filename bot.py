import os
import json
import re
import requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# কনফিগারেশন
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

genai.configure(api_key=GEMINI_API_KEY)

# ধারাবাহিকভাবে সিরিয়াল নাম্বার ট্র্যাক করার জন্য একটি সিম্পল ফাইল
SERIAL_FILE = "serial.txt"

def get_next_serial():
    if not os.path.exists(SERIAL_FILE):
        return 1
    with open(SERIAL_FILE, "r") as f:
        return int(f.read().strip())

def update_serial(last_serial):
    with open(SERIAL_FILE, "w") as f:
        f.write(str(last_serial + 3))

def get_grammar_content():
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = '''
    Act as a Grammar Professor. Generate a unique, highly advanced English grammar lesson.
    Output MUST be a JSON object (no markdown):
    {
      "topic": "Name",
      "rule": "Detailed rule",
      "example": "Solved example",
      "seo_text": "Engaging English caption with trending hashtags",
      "questions": [
        {"q": "Q1", "options": ["A)", "B)", "C)", "D)", "E)"], "correct": 0},
        {"q": "Q2", "options": ["A)", "B)", "C)", "D)", "E)"], "correct": 1},
        {"q": "Q3", "options": ["A)", "B)", "C)", "D)", "E)"], "correct": 2}
      ]
    }
    '''
    response = model.generate_content(prompt)
    return json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))

def create_image(topic, rule, example):
    img = Image.new('RGB', (800, 1000), color='#fefcf7')
    draw = ImageDraw.Draw(img)
    # আপনার চ্যানেলের নাম ওয়াটারমার্ক হিসেবে
    draw.text((50, 20), "English Grammar EX", fill='#000000')
    draw.text((50, 60), f"TOPIC: {topic}", fill='#ff0000')
    draw.text((50, 120), f"RULE:\n{rule}", fill='#0000ff')
    draw.text((50, 300), f"SOLVED EXAMPLE:\n{example}", fill='#008000')
    img.save("post.png")
    return "post.png"

def post_to_telegram(data):
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    serial = get_next_serial()
    
    # ইমেজ পোস্ট
    img_path = create_image(data['topic'], data['rule'], data['example'])
    with open(img_path, 'rb') as f:
        requests.post(base_url + "/sendPhoto", data={"chat_id": CHANNEL_ID, "caption": data['seo_text']}, files={"photo": f})
    
    # ৩টি কঠিন এমসিকিউ পোল (Quiz Mode)
    for i, q in enumerate(data['questions']):
        requests.post(base_url + "/sendPoll", data={
            "chat_id": CHANNEL_ID,
            "question": f"{serial + i}. {q['q']}",
            "options": json.dumps(q['options']),
            "type": "quiz",
            "correct_option_id": q['correct'],
            "is_anonymous": False
        })
    update_serial(serial)

if __name__ == "__main__":
    data = get_grammar_content()
    post_to_telegram(data)
    
