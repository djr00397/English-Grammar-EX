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

def get_content():
    model = genai.GenerativeModel('gemini-2.5-flash')
    # জেমিনিকে ইন্সট্রাকশন দেয়া হয়েছে ভিন্ন টপিক এবং ৩টি প্রশ্নের জন্য
    prompt = '''
    Create a unique, advanced English Grammar lesson on a random topic.
    Return ONLY JSON:
    {
      "topic": "Topic Name",
      "rule": "Short Rule",
      "example": "Simple Example",
      "seo_hashtags": "#EnglishGrammar #LearnEnglish #AdvancedGrammar",
      "questions": [
        {"q": "Q1 text?", "options": ["A", "B", "C", "D"], "correct": 0},
        {"q": "Q2 text?", "options": ["A", "B", "C", "D"], "correct": 1},
        {"q": "Q3 text?", "options": ["A", "B", "C", "D"], "correct": 2}
      ]
    }
    '''
    response = model.generate_content(prompt)
    return json.loads(response.text.replace('```json', '').replace('```', ''))

def create_image(data):
    img = Image.new('RGB', (1000, 500), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    # শিরোনাম, রুল এবং উদাহরণ বড় ফন্টে
    draw.text((300, 20), "ENGLISH GRAMMAR EX", fill='#0000FF')
    draw.text((50, 100), f"TOPIC: {data['topic']}", fill='#000000')
    draw.text((50, 180), f"RULE: {textwrap.fill(data['rule'], 50)}", fill='#FF0000')
    draw.text((50, 350), f"EXAMPLE: {textwrap.fill(data['example'], 50)}", fill='#008000')
    img.save("card.png")
    return "card.png"

def run():
    data = get_content()
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    # ১. ইমেজ পোস্ট (এসইও হ্যাশট্যাগসহ)
    img = create_image(data)
    requests.post(base_url + "/sendPhoto", data={
        "chat_id": CHANNEL_ID, 
        "caption": f"📖 Master today's grammar rule! \n\n{data['seo_hashtags']}",
        "photo": open(img, 'rb')
    })
    
    # ২. ৩টি আলাদা পোল (প্রশ্ন) পোস্ট করা
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
    
