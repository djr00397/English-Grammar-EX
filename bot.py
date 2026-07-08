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
    Generate one advanced English grammar rule, one example, and 3 hard MCQ questions (5 options each).
    Output JSON:
    {
      "topic": "Topic Name",
      "rule": "The core grammar rule (short)",
      "example": "One clear example",
      "seo_caption": "Caption with #EnglishGrammar #GrammarQuiz #LearnEnglish",
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
    # বড় এবং পরিষ্কার ছবি (1000x600)
    img = Image.new('RGB', (1000, 600), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    # বড় ফন্ট সেটআপ
    font = ImageFont.load_default() 
    
    draw.text((350, 20), "English Grammar EX", fill='#0000FF')
    draw.text((50, 100), f"TOPIC: {data['topic']}", fill='#000000')
    
    # লেখা যেন বড় এবং পড়ার যোগ্য হয়
    rule_text = textwrap.fill(f"RULE: {data['rule']}", width=50)
    draw.text((50, 180), rule_text, fill='#FF0000')
    
    example_text = textwrap.fill(f"EXAMPLE: {data['example']}", width=50)
    draw.text((50, 350), example_text, fill='#008000')
    
    img.save("clean_card.png")
    return "clean_card.png"

def post_to_telegram(data):
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    img_path = create_clean_image(data)
    
    # ১. ইমেজ পোস্ট (শুধুমাত্র নাম, সূত্র, উদাহরণ)
    requests.post(base_url + "/sendPhoto", data={"chat_id": CHANNEL_ID, "caption": data['seo_caption']}, files={"photo": open(img_path, 'rb')})
    
    # ২. ৩টি প্রশ্ন আলাদা আলাদা পোস্ট (বাটনসহ পোল)
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
    
