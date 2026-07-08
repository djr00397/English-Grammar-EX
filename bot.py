import os
import json
import requests
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# Fetch data from GitHub Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def get_grammar_content():
    """Generate high-quality advanced grammar lesson and questions via Gemini"""
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = '''
    You are an expert English Grammar instructor.
    Create a unique, highly advanced English grammar lesson. Do not repeat basic topics.
    Provide the output strictly in valid JSON format exactly matching this structure (no markdown tags around the JSON):
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
    Important: 
    1. Ensure the correct_index (0 to 3) is randomized for each question so it's not always the same option.
    2. Output ONLY the JSON object, do not wrap in markdown boxes.
    '''
    
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    # JSON Clean up
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
        
    return json.loads(raw_text.strip())

def download_font():
    """Download a clean bold font for the image generator"""
    font_url = "[https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf](https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf)"
    font_path = "Roboto-Bold.ttf"
    if not os.path.exists(font_path):
        response = requests.get(font_url)
        with open(font_path, "wb") as f:
            f.write(response.content)
    return font_path

def create_notebook_image(topic, rule, example):
    """Create a digital notebook-style image with the grammar rule"""
    width, height = 850, 600
    img = Image.new('RGB', (width, height), color='#fefcf7')
    draw = ImageDraw.Draw(img)

    # Draw horizontal notebook lines (blue)
    for y in range(80, height, 45):
        draw.line([(0, y), (width, y)], fill='#b4d4ff', width=2)
    # Draw vertical margin line (red)
    draw.line([(95, 0), (95, height)], fill='#ffb3ba', width=3)

    # Load Font
    font_path = download_font()
    font_title = ImageFont.truetype(font_path, 30)
    font_section = ImageFont.truetype(font_path, 24)
    font_text = ImageFont.truetype(font_path, 22)

    def draw_wrapped_text(text, position, font, fill, max_width=680):
        import textwrap
        lines = textwrap.wrap(text, width=50)
        y_text = position[1]
        for line in lines:
            draw.text((position[0], y_text), line, font=font, fill=fill)
            y_text += 45
        return y_text

    # Populate notebook layout
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
    """Post image and Quiz questions to Telegram Channel"""
    base_url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){BOT_TOKEN}"
    
    # 1. Send Photo with English SEO Caption
    with open(img_path, 'rb') as photo:
        caption_text = f"{data['seo_text']}\n\n👉 **Read the advanced rule above carefully and answer the 3 questions below!** 🔽"
        payload = {
            "chat_id": CHANNEL_ID,
            "caption": caption_text,
            "parse_mode": "Markdown"
        }
        requests.post(f"{base_url}/sendPhoto", data=payload, files={"photo": photo})
            
    # 2. Send 3 Telegram Native Quizzes (Quiz Mode enabled - locks answer once clicked)
    for idx, q_data in enumerate(data['questions']):
        poll_payload = {
            "chat_id": CHANNEL_ID,
            "question": f"Q{idx + 1}: {q_data['q']}",
            "options": json.dumps(q_data['options']),
            "is_anonymous": False,
            "type": "quiz", 
            "correct_option_id": q_data['correct_index']
        }
        requests.post(f"{base_url}/sendPoll", data=poll_payload)

if __name__ == "__main__":
    print("Fetching grammar content from Gemini...")
    content = get_grammar_content()
    print("Generating notebook style image...")
    img_file = create_notebook_image(content['topic'], content['rule'], content['example'])
    print("Posting to Telegram Channel...")
    send_to_telegram(content, img_file)
    print("Successfully Posted!")
    
