import os
import json
import time
from datetime import datetime
import telebot
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# GitHub Secrets থেকে নিরাপদে ডেটা রিড করা হচ্ছে
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_seo_content_from_gemini():
    """Generates High-Quality Advanced Grammar Content and Poll Questions"""
    prompt = """
    Create an advanced English Grammar Lesson. The topic should be highly challenging (e.g., Inversion, Advanced Subjunctive, Dangling Modifiers, Complex Concord).
    Output must be in strictly valid JSON format with the following keys. Do not include markdown code blocks or ```json wrappers.
    
    {
      "title": "SEO Optimized Catchy Title",
      "concept": "A deep, advanced explanation of the concept with examples.",
      "questions": [
        {
          "question": "Difficult Multiple Choice Question?",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_index": 0,
          "explanation": "Why this is correct."
        }
      ]
    }
    Generate 5 such difficult questions for the same topic. Ensure the explanation is solid. All in English.
    """
    response = model.generate_content(prompt)
    try:
        text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(text)
        return data
    except Exception as e:
        print("JSON Parsing Error, retrying with fallback...", e)
        return {
            "title": "Advanced Subject-Verb Agreement",
            "concept": "Advanced cases of inversion and hypothetical conditional agreement.",
            "questions": [
                {"question": "Hardly _______ the room when the phone rang.", "options": ["had he entered", "he had entered", "entered he", "has he entered"], "correct_index": 0, "explanation": "Negative inversion requires auxiliary verb before subject."}
            ] * 5
        }

def create_notebook_image(title, concept):
    """Creates a 'Handwritten Advanced Notebook/Khata' style Image"""
    img = Image.new('RGB', (800, 1000), color='#FDF6E3')
    draw = ImageDraw.Draw(img)
    
    for y in range(100, 1000, 40):
        draw.line([(50, y), (750, y)], fill="#D2E4F0", width=1)
    draw.line([(120, 0), (120, 1000)], fill="#F9A7A7", width=2)
    
    draw.text((140, 60), f"TOPIC: {title.upper()}", fill="#B58900", font_size=24)
    draw.rectangle([(140, 140), (740, 400)], fill="#FFF9E6", outline="#E6DBB2", width=2)
    
    lines = [concept[i:i+45] for i in range(0, len(concept), 45)]
    y_offset = 160
    draw.text((150, y_offset), "ADVANCED GUIDELINES:", fill="#CB4B16", font_size=18)
    
    for line in lines[:7]:
        y_offset += 30
        draw.text((150, y_offset), line, fill="#073642", font_size=16)
        
    img.save("lesson.png")

def load_leaderboard():
    if not os.path.exists("leaderboard.json"):
        return {"monthly": {}, "lifetime": {}, "last_reset_month": ""}
    with open("leaderboard.json", "r") as f:
        return json.load(f)

def save_leaderboard(data):
    with open("leaderboard.json", "w") as f:
        json.dump(data, f, indent=2)

def generate_leaderboard_post():
    data = load_leaderboard()
    current_month = datetime.now().strftime("%B %Y")
    
    top_month = sorted(data["monthly"].items(), key=lambda x: x[1], reverse=True)[:10]
    top_life = sorted(data["lifetime"].items(), key=lambda x: x[1], reverse=True)[:10]
    
    msg = f"🏆 **OFFICIAL ENGLISH GRAMMAR LEADERBOARD** 🏆\n"
    msg += f"📅 *Period: {current_month}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += "🥇 **TOP 10 PERFORMERS (THIS MONTH)**\n"
    if not top_month:
        msg += "No data yet. Start answering to rank up!\n"
    for i, (user, score) in enumerate(top_month, 1):
        msg += f"{i}. {user} ➔ {score} Pts\n"
        
    msg += "\n👑 **LEGENDS OF ALL TIME (LIFETIME)**\n"
    if not top_life:
        msg += "No data yet.\n"
    for i, (user, score) in enumerate(top_life, 1):
        msg += f"{i}. {user} ➔ {score} Pts\n"
        
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🔥 *Want to see your name here? Answer today's quizzes correctly! Once submitted, answers cannot be changed.*"
    return msg

def check_and_post_monthly_leaderboard():
    data = load_leaderboard()
    current_month = datetime.now().strftime("%Y-%m")
    
    if data.get("last_reset_month") != current_month and data.get("monthly"):
        leaderboard_text = "🎉 **CONGRATULATIONS TO EVERYONE! MONTHLY FINALS** 🎉\n\n" + generate_leaderboard_post()
        bot.send_message(CHANNEL_ID, leaderboard_text, parse_mode="Markdown")
        
        data["monthly"] = {}
        data["last_reset_month"] = current_month
        save_leaderboard(data)

def main():
    print("Starting Automated Grammar Bot Posting Task...")
    check_and_post_monthly_leaderboard()
    content = get_seo_content_from_gemini()
    create_notebook_image(content["title"], content["concept"])
    
    caption = f"📚 **TODAY'S ADVANCED LESSON: {content['title'].upper()}**\n\n"
    caption += f"📝 **Core Rule:**\n{content['concept']}\n\n"
    caption += f"🔍 *Test your knowledge below with 5 ultra-hard exam level questions!*"
    
    with open("lesson.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=caption, parse_mode="Markdown")
    
    for q in content["questions"]:
        bot.send_poll(
            chat_id=CHANNEL_ID,
            question=f"🔥 [HARD] {q['question']}",
            options=q["options"],
            type="quiz",
            correct_option_id=q["correct_index"],
            is_anonymous=False
        )
        time.sleep(2)
        
    print("All tasks completed successfully!")

if __name__ == "__main__":
    main()
    
