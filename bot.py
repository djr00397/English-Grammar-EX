import os
import json
import requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

genai.configure(api_key=GEMINI_API_KEY)

def get_grammar_data():
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = '''
    Create an advanced English Grammar lesson with 3 hard MCQ questions based on the rule.
    Return ONLY JSON (no markdown):
    {
      "topic": "Topic Name",
      "rule": "Detailed rule explanation",
      "example": "Solved example",
      "seo_text": "Engaging caption with hashtags like #EnglishGrammar #AdvancedGrammar",
      "questions": [
        {"q": "Q1", "options": ["A", "B", "C", "D", "E"], "correct": 0},
        {"q": "Q2", "options": ["A", "B", "C", "D", "E"], "correct": 1},
        {"q": "Q3", "options": ["A", "B", "C", "D", "E"], "correct": 2}
      ]
    }
    '''
    response = model.generate_content(prompt)
    return json.loads(response.text.replace('```json', '').replace('```', ''))

def create_image(data):
    img = Image.new('RGB', (1000, 700), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    # চ্যানেলের নাম
    draw.text((350, 20), "English Grammar EX", fill='#0000FF', font_size=40)
    # রুল ও এক্সাম্পল
    draw.text((50, 100), f"TOPIC: {data['topic']}", fill='#000000', font_size=30)
    draw.text((50, 160), f"RULE: {data['rule']}", fill='#FF0000', font_size=25)
    draw.text((50, 300), f"EXAMPLE: {data['example']}", fill='#008000', font_size=25)
    img.save("post.png")
    return "post.png"

def run_bot():
    data = get_grammar_data()
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    # ছবি ও ক্যাপশন
    img_path = create_image(data)
    with open(img_path, 'rb') as f:
        requests.post(base_url + "/sendPhoto", data={"chat_id": CHANNEL_ID, "caption": data['seo_text']}, files={"photo": f})
    
    # ৩টি এমসিকিউ পোল
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
    run_bot()
    
