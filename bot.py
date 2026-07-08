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
    prompt = '''
    Create a unique, advanced English Grammar lesson.
    Output ONLY JSON (no markdown):
    {
      "topic": "Topic Name",
      "rule": "Only the core rule in 2-3 short lines",
      "example": "One clear solved example",
      "caption": "Engaging English caption with hashtags",
      "questions": [
        {"q": "Question 1 text", "options": ["A", "B", "C", "D", "E"], "correct": 0},
        {"q": "Question 2 text", "options": ["A", "B", "C", "D", "E"], "correct": 1},
        {"q": "Question 3 text", "options": ["A", "B", "C", "D", "E"], "correct": 2}
      ]
    }
    '''
    response = model.generate_content(prompt)
    return json.loads(response.text.replace('```json', '').replace('```', ''))

def create_image(data):
    # ছবির সাইজ বাড়ানো হয়েছে যাতে লেখা পরিষ্কার থাকে
    img = Image.new('RGB', (1000, 800), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    
    # চ্যানেলের নাম
    draw.text((300, 30), "English Grammar EX", fill='#0000FF')
    # টপিক
    draw.text((50, 100), f"TOPIC: {data['topic']}", fill='#000000')
    
    # লেখাগুলোকে র‍্যাপ করা যাতে ভেঙে না যায়
    rule_lines = textwrap.wrap(f"RULE: {data['rule']}", width=60)
    y = 160
    for line in rule_lines:
        draw.text((50, y), line, fill='#FF0000')
        y += 30
        
    ex_lines = textwrap.wrap(f"EXAMPLE: {data['example']}", width=60)
    y += 40
    for line in ex_lines:
        draw.text((50, y), line, fill='#008000')
        y += 30
        
    img.save("post.png")
    return "post.png"

def run():
    data = get_grammar_data()
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    img_path = create_image(data)
    
    # ছবি পাঠানো
    with open(img_path, 'rb') as f:
        requests.post(base_url + "/sendPhoto", data={"chat_id": CHANNEL_ID, "caption": data['caption']}, files={"photo": f})
    
    # এমসিকিউ পোল পাঠানো (লুপ দিয়ে ৩টি পোল)
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
    run()
    
