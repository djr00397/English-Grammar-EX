import os
import json
import re
import requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# 1. GitHub Secrets থেকে ক্রিশিয়াল ডাটা নেওয়া হচ্ছে
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# জেমিনি এপিআই কনফিগারেশন
genai.configure(api_key=GEMINI_API_KEY)

def get_grammar_content():
    """জেমিনি থেকে ডাটা নিয়ে আসা এবং সকল ফরম্যাটিং এরর দূর করা"""
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = '''
    You are an expert English Grammar instructor.
    Create a unique, highly advanced English grammar lesson.
    Provide the output STRICTLY in valid JSON format exactly matching this structure:
    {
      "topic": "Name of the advanced topic",
      "rule": "The grammar rule in short (max 2 sentences)",
      "example": "A clear example applying the rule",
      "seo_text": "Engaging SEO-optimized caption for a Telegram post including high traffic hashtags",
      "questions": [
        {
          "q": "Extremely difficult question 1",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_index": 0
        },
        {
          "q": "Extremely difficult question 2",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_index": 1
        },
        {
          "q": "Extremely difficult question 3",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_index": 2
        }
      ]
    }
    Important: Output ONLY the JSON object. Do not wrap it in markdown boxes or text.
    '''
    
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    # এরর প্রতিরোধের জন্য রেগুলার এক্সপ্রেশন ব্যবহার করে শুধু JSON অংশটুকু কেটে নেওয়া হচ্ছে
    try:
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            clean_text = json_match.group(0)
        else:
            clean_text = raw_text
            
        return json.loads(clean_text)
    except Exception as e:
        print(f"Critial Error Parsing JSON. Raw text was: {raw_text}")
        raise e

def load_system_font(size):
    """গিটহাব উবুন্টু সার্ভারের নিজস্ব ফন্ট লোড করা (এরর ফ্রি)"""
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
    """খাতার ডিজাইনে ইমেজ তৈরি করা"""
    width, height = 850, 600
    img = Image.new('RGB', (width, height), color='#fefcf7')
    draw = ImageDraw.Draw(img)

    # খাতার নীল দাগ
    for y in range(80, height, 45):
        draw.line([(0, y), (width, y)], fill='#b4d4ff', width=2)
    # খাতার লাল মার্জিন
    draw.line([(95, 0), (95, height)], fill='#ffb3ba', width=3)

    # ফন্ট সেটআপ
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

    # টেক্সট ড্রয়িং
    draw.text((120, 30), "📝 ADVANCED GRAMMAR NOTEBOOK", font=font_title, fill='#2c3e50')
    
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

def send_to_telegram(data, img_path):
    """টেলিগ্রাম চ্যানেলে রিকোয়েস্ট পাঠানো"""
    base_url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){BOT_TOKEN}"
    
    # ১. ছবি এবং ক্যাপশন পাঠানো (সম্পূর্ণ ইংরেজি)
    with open(img_path, 'rb') as photo:
        caption_text = f"{data['seo_text']}\n\n👉 **Read the advanced rule above carefully and answer the 3 questions below!** 🔽"
        payload = {
            "chat_id": CHANNEL_ID,
            "caption": caption_text,
            "parse_mode": "Markdown"
        }
        r1 = requests.post(f"{base_url}/sendPhoto", data=payload, files={"photo": photo})
        print(f"Photo Sent Status: {r1.status_code}, Response: {r1.text}")
            
    # ২. ৩টি কুইজ পোল পাঠানো (Quiz Mode)
    for idx, q_data in enumerate(data['questions']):
        poll_payload = {
            "chat_id": CHANNEL_ID,
            "question": f"Q{idx + 1}: {q_data['q']}",
            "options": json.dumps(q_data['options']),
            "is_anonymous": False,
            "type": "quiz", 
            "correct_option_id": int(q_data['correct_index'])
        }
        r2 = requests.post(f"{base_url}/sendPoll", data=poll_payload)
        print(f"Quiz {idx+1} Sent Status: {r2.status_code}, Response: {r2.text}")

if __name__ == "__main__":
    print("Step 1: Fetching grammar content from Gemini...")
    content = get_grammar_content()
    
    print("Step 2: Generating notebook style image...")
    img_file = create_notebook_image(content['topic'], content['rule'], content['example'])
    
    print("Step 3: Posting to Telegram Channel...")
    send_to_telegram(content, img_file)
    print("Process successfully finished!")
    
