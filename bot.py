import os
import json
import re
import requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

genai.configure(api_key=GEMINI_API_KEY)

# ফিক্সড সিরিয়াল - প্রতিবার রান হওয়ার সময় Gemini থেকে জেনারেট হবে যাতে গিটহাবের ফাইলের ওপর নির্ভর করতে না হয়
def get_grammar_content():
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = '''
    You are an expert English Grammar professor. Create a highly advanced, non-repetitive English grammar lesson.
    Based on the rule, create 3 extremely challenging exam-style MCQ questions with 5 options (A, B, C, D, E).
    Output STRICTLY in JSON format:
    {
      "topic": "Topic Name",
      "rule": "The grammar rule",
      "example": "Advanced example",
      "seo_text": "SEO caption",
      "questions": [
        {"q": "Q1 text", "options": ["A) opt", "B) opt", "C) opt", "D) opt", "E) opt"], "correct_index": 0},
        {"q": "Q2 text", "options": ["A) opt", "B) opt", "C) opt", "D) opt", "E) opt"], "correct_index": 1},
        {"q": "Q3 text", "options": ["A) opt", "B) opt", "C) opt", "D) opt", "E) opt"], "correct_index": 2}
      ]
    }
    '''
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    return json.loads(json_match.group(0))

def create_notebook_image(topic, rule, example):
    width, height = 850, 600
    img = Image.new('RGB', (width, height), color='#fefcf7')
    draw = ImageDraw.Draw(img)
    for y in range(80, height, 45):
        draw.line([(0, y), (width, y)], fill='#b4d4ff', width=2)
    draw.line([(95, 0), (95, height)], fill='#ffb3ba', width=3)
    
    # আপনার চ্যানেলের নাম
    draw.text((120, 30), "📝 English Grammar EX", font=ImageFont.load_default(), fill='#2c3e50')
    
    y_pos = 110
    draw.text((120, y_pos), f"TOPIC: {topic}", fill='#c0392b')
    draw.text((120, y_pos + 50), f"RULE: {rule}", fill='#2980b9')
    draw.text((120, y_pos + 150), f"EX: {example}", fill='#27ae60')
    
    img_path = "grammar_lesson.png"
    img.save(img_path)
    return img_path

def send_to_telegram(data):
    p1 = "https://"
    p2 = "api.telegram.org"
    p3 = "/bot"
    base_url = p1 + p2 + p3 + str(BOT_TOKEN)
    
    img_path = create_notebook_image(data['topic'], data['rule'], data['example'])
    
    with open(img_path, 'rb') as photo:
        requests.post(base_url + "/sendPhoto", data={"chat_id": CHANNEL_ID, "caption": data['seo_text']}, files={"photo": photo})
            
    for idx, q_data in enumerate(data['questions']):
        payload = {
            "chat_id": CHANNEL_ID,
            "question": f"Question (Advanced): {q_data['q']}",
            "options": json.dumps(q_data['options']),
            "is_anonymous": False,
            "type": "quiz",
            "correct_option_id": int(q_data['correct_index'])
        }
        requests.post(base_url + "/sendPoll", payload)

if __name__ == "__main__":
    content = get_grammar_content()
    send_to_telegram(content)
    
