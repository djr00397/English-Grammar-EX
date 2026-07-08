import os
import json
import requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# GitHub Secrets থেকে ডাটা নেওয়া হচ্ছে (ADSTERRA_LINK বাদ দেওয়া হয়েছে)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# জেমিনি এপিআই কনফিগারেশন
genai.configure(api_key=GEMINI_API_KEY)

def get_grammar_content():
    """জেমিনি থেকে নতুন, কঠিন প্রশ্ন এবং সূত্র তৈরি করা"""
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = '''
    You are an expert English Grammar instructor.
    Create a unique, highly advanced English grammar lesson. Do not repeat previous topics.
    Provide the output strictly in valid JSON format exactly matching this structure (no markdown tags around the JSON):
    {
      "topic": "Name of the advanced topic",
      "rule": "The grammar rule in short (max 2 sentences)",
      "example": "A clear example applying the rule",
      "seo_text": "Engaging SEO-optimized caption for a Telegram post including high traffic hashtags",
      "questions": [
        {
          "q": "Extremely difficult question 1",
          "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
          "correct_index": 0
        },
        {
          "q": "Extremely difficult question 2",
          "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
          "correct_index": 1
        },
        {
          "q": "Extremely difficult question 3",
          "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
          "correct_index": 2
        }
      ]
    }
    Important: 
    1. Ensure the correct_index (0 to 3) is randomized for each question (It can be A, B, C, or D).
    2. Output ONLY the JSON object.
    '''
    
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    # JSON ফরম্যাট ক্লিনিং
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
        
    return json.loads(raw_text.strip())

def create_notebook_image(topic, rule, example):
    """সূত্র ও উদাহরণ দিয়ে খাতার মত ছবি তৈরি করা"""
    width, height = 800, 500
    img = Image.new('RGB', (width, height), color='#fdfbf7')
    draw = ImageDraw.Draw(img)

    # খাতার দাগ টানা
    for y in range(80, height, 40):
        draw.line([(0, y), (width, y)], fill='#a1c4fd', width=2)
    draw.line([(80, 0), (80, height)], fill='#ffb3ba', width=3)

    try:
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_text = ImageFont.truetype("arial.ttf", 22)
    except IOError:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    def draw_wrapped_text(text, position, font, fill, max_width=650):
        import textwrap
        lines = textwrap.wrap(text, width=55)
        y_text = position[1]
        for line in lines:
            draw.text((position[0], y_text), line, font=font, fill=fill)
            y_text += 40
        return y_text

    # টেক্সট বসানো
    y_pos = 90
    draw.text((100, 30), "📚 Advanced Grammar Guide", font=font_title, fill='#e74c3c')
    
    y_pos = draw_wrapped_text(f"Topic: {topic}", (100, y_pos), font=font_title, fill='#2c3e50')
    y_pos += 10
    
    draw.text((100, y_pos), "Rule:", font=font_title, fill='#2980b9')
    y_pos += 40
    y_pos = draw_wrapped_text(rule, (100, y_pos), font=font_text, fill='#34495e')
    y_pos += 10
    
    draw.text((100, y_pos), "Example:", font=font_title, fill='#27ae60')
    y_pos += 40
    draw_wrapped_text(example, (100, y_pos), font=font_text, fill='#34495e')

    img_path = "grammar_lesson.png"
    img.save(img_path)
    return img_path

def send_to_telegram(data, img_path):
    """টেলিগ্রামে পোস্ট করা (ছবি এবং কুইজ)"""
    base_url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){BOT_TOKEN}"
    
    # ১. ছবি এবং SEO ক্যাপশন পাঠানো
    with open(img_path, 'rb') as photo:
        # ক্যাপশন থেকে লিংক বাদ দেওয়া হয়েছে
        caption_text = f"{data['seo_text']}\n\n👉 **উপরের ছবিটি ভালোভাবে পড়ুন এবং নিচের কুইজগুলোর উত্তর দিন!**"
        payload = {
            "chat_id": CHANNEL_ID,
            "caption": caption_text,
            "parse_mode": "Markdown"
        }
        requests.post(f"{base_url}/sendPhoto", data=payload, files={"photo": photo})
            
    # ২. কুইজ পোল পাঠানো (Quiz Mode - পরিবর্তন করা যাবে না)
    for idx, q_data in enumerate(data['questions']):
        poll_payload = {
            "chat_id": CHANNEL_ID,
            "question": f"Q{idx + 1}: {q_data['q']}",
            "options": json.dumps(q_data['options']),
            "is_anonymous": False,
            "type": "quiz", # কুইজ মোড চালু
            "correct_option_id": q_data['correct_index']
            # বাটন এবং এক্সপ্লানেশন লিংক রিমুভ করা হয়েছে
        }
        requests.post(f"{base_url}/sendPoll", data=poll_payload)

if __name__ == "__main__":
    content = get_grammar_content()
    img_file = create_notebook_image(content['topic'], content['rule'], content['example'])
    send_to_telegram(content, img_file)
    
