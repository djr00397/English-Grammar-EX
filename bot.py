import os
import json
import re
import requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# GitHub Secrets থেকে ডাটা নেওয়া
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

genai.configure(api_key=GEMINI_API_KEY)

DATA_FILE = "data.json"

def get_next_serial_number():
    """data.json থেকে ধারাবাহিক সিরিয়াল নাম্বার পড়া এবং আপডেট করা"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                current_serial = data.get("last_serial", 0)
        except:
            current_serial = 0
    else:
        current_serial = 0
    
    next_serial = current_serial + 1
    return next_serial, current_serial + 3

def save_next_serial_number(last_used_serial):
    """সর্বশেষ ব্যবহৃত সিরিয়াল নাম্বার সেভ করা"""
    with open(DATA_FILE, "w") as f:
        json.dump({"last_serial": last_used_serial}, f)

def get_grammar_content():
    """জেমিনি থেকে ইউনিক টপিক, রুল এবং ৩টি অত্যন্ত কঠিন ৫-অপশনের MCQ নেওয়া"""
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = '''
    You are an expert English Grammar professor. 
    Generate a highly advanced, non-repetitive English grammar lesson.
    Based strictly on that specific rule, create exactly 3 extremely challenging exam-style MCQ questions.
    Each question must have exactly 5 options: A, B, C, D, and E.
    Provide the output STRICTLY in valid JSON format matching this structure:
    {
      "topic": "Name of the advanced topic",
      "rule": "The core grammar rule/formula in short",
      "example": "A highly advanced example applying the rule",
      "seo_text": "Engaging SEO-optimized caption for a Telegram post with high-traffic hashtags",
      "questions": [
        {
          "q": "The question text goes here",
          "options": ["A) option text", "B) option text", "C) option text", "D) option text", "E) option text"],
          "correct_index": 0
        },
        {
          "q": "The question text goes here",
          "options": ["A) option text", "B) option text", "C) option text", "D) option text", "E) option text"],
          "correct_index": 1
        },
        {
          "q": "The question text goes here",
          "options": ["A) option text", "B) option text", "C) option text", "D) option text", "E) option text"],
          "correct_index": 2
        }
      ]
    }
    Important Constraints:
    1. The correct_index must match the correct option (0=A, 1=B, 2=C, 3=D, 4=E). Randomize the correct option for each question.
    2. Output ONLY the JSON object. No markdown, no wrap.
    '''
    
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    try:
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            clean_text = json_match.group(0)
        else:
            clean_text = raw_text
        return json.loads(clean_text)
    except Exception as e:
        print(f"JSON Parsing Error. Raw text: {raw_text}")
        raise e

def load_system_font(size):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def create_notebook_image(topic, rule, example):
    """English Grammar EX ওয়াটারমার্কসহ খাতার ছবি তৈরি"""
    width, height = 850, 600
    img = Image.new('RGB', (width, height), color='#fefcf7')
    draw = ImageDraw.Draw(img)
    
    for y in range(80, height, 45):
        draw.line([(0, y), (width, y)], fill='#b4d4ff', width=2)
    draw.line([(95, 0), (95, height)], fill='#ffb3ba', width=3)
    
    font_title = load_system_font(30)
    font_section = load_system_font(24)
    font_text = load_system_font(22)
    
    def draw_wrapped_text(text, position, font, fill):
        import textwrap
        lines = textwrap.wrap(text, width=50)
        y_text = position[1]
        for line in lines:
            draw.text((position[0], y_text), line, font=font, fill=fill)
            y_text += 45
        return y_text
        
    # ADVANCED GRAMMAR NOTEBOOK এর বদলে আপনার চ্যানেলের নাম দেওয়া হলো
    draw.text((120, 30), "📝 English Grammar EX", font=font_title, fill='#2c3e50')
    
    y_pos = 110
    y_pos = draw_wrapped_text(f"📌 TOPIC: {topic}", (120, y_pos), font=font_section, fill='#c0392b')
    y_pos += 15
    draw.text((120, y_pos), "📖 RULE:", font=font_section, fill='#2980b9')
    y_pos += 40
    y_pos = draw_wrapped_text(rule, (120, y_pos), font=font_text, fill='#34495e')
    y_pos += 15
    draw.text((120, y_pos), "💡 EXAMPLE:", font=font_section, fill='#27ae60')
    y_pos += 40
    draw_wrapped_text(example, (120, y_pos), font=font_text, fill='#2c3e50')
    
    img_path = "grammar_lesson.png"
    img.save(img_path)
    return img_path

def send_to_telegram(data, img_path, start_num):
    p1 = "https://"
    p2 = "api.telegram.org"
    p3 = "/bot"
    base_url = p1 + p2 + p3 + str(BOT_TOKEN)
    
    # ১. ছবি ও এসইও ক্যাপশন পাঠানো
    with open(img_path, 'rb') as photo:
        caption_text = f"{data['seo_text']}\n\n👉 **Analyze the rule above and solve the examination questions below!** 🔽"
        payload = {
            "chat_id": CHANNEL_ID,
            "caption": caption_text,
            "parse_mode": "Markdown"
        }
        requests.post(base_url + "/sendPhoto", data=payload, files={"photo": photo})
            
    # ২. ৩টি রিয়েল কুইজ পোল পাঠানো (A, B, C, D, E অপশনসহ)
    # কুইজ মোডের কারণে একবার ক্লিক করলে উত্তর আর পরিবর্তন করা যাবে না।
    for idx, q_data in enumerate(data['questions']):
        current_num = start_num + idx
        poll_payload = {
            "chat_id": CHANNEL_ID,
            "question": f"Question {current_num}: {q_data['q']}",
            "options": json.dumps(q_data['options']),
            "is_anonymous": False,
            "type": "quiz",  # রিয়েল কুইজ মোড (সবুজ/লাল আলো জ্বলবে)
            "correct_option_id": int(q_data['correct_index'])
        }
        requests.post(base_url + "/sendPoll", poll_payload)

if __name__ == "__main__":
    print("Step 1: Reading serial numbers...")
    start_serial, end_serial = get_next_serial_number()
    
    print("Step 2: Fetching content from Gemini...")
    content = get_grammar_content()
    
    print("Step 3: Generating image with watermark...")
    img_file = create_notebook_image(content['topic'], content['rule'], content['example'])
    
    print("Step 4: Posting Image and Real Quiz Polls...")
    send_to_telegram(content, img_file, start_serial)
    
    print("Step 5: Saving current serial back to JSON...")
    save_next_serial_number(end_serial)
    
    print("Process successfully finished!")
            
