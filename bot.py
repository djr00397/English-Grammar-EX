import os
import time
import telebot
import google.generativeai as genai
from PIL import Image, ImageDraw

# GitHub Secrets থেকে ডেটা রিড
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)

# লেটেস্ট গুগল মডেল
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def get_seo_content_from_gemini():
    """Generates High-Quality Advanced Grammar Content (3 Questions & SEO Caption)"""
    prompt = """
    Create an advanced English Grammar Lesson. Topic must be highly challenging (e.g., Inversion, Subjunctive, Participle Clauses).
    Output MUST be valid JSON only. Do not include markdown wrappers like ```json.
    
    {
      "topic": "Advanced Inversion",
      "formula": "Write the exact core grammar rule/formula here like a study note. Keep it concise.",
      "seo_caption": "Write a 2-sentence highly engaging caption. Include 5-7 trending SEO hashtags.",
      "questions": [
        {
          "question": "Difficult Multiple Choice Question?",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "correct_index": 0,
          "explanation": "Why this is correct."
        }
      ]
    }
    Generate exactly 3 such difficult questions.
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        return json.loads(response.text.strip())
    except Exception as e:
        print("API Error:", e)
        # ব্যাকআপ ডেটা
        return {
            "topic": "Advanced Inversion",
            "formula": "Rule: Negative Adverb + Auxiliary Verb + Subject + Main Verb.\nExample: Rarely do we see such a phenomenon.",
            "seo_caption": "Master the art of Advanced English Grammar! 🚀 Test your skills below.\n\n#EnglishGrammar #LearnEnglish #IELTS #AdvancedEnglish",
            "questions": [
                {"question": "Hardly _______ the room when the phone rang.", "options": ["had he entered", "he had entered", "entered he", "has he entered"], "correct_index": 0, "explanation": "Inversion is required."}
            ] * 3
        }

def create_notebook_image(topic, formula):
    """Creates a professional grammar notebook style image."""
    img = Image.new('RGB', (800, 800), color='#F9F6EE')
    draw = ImageDraw.Draw(img)
    
    # খাতার দাগ ও মার্জিন
    for y in range(120, 800, 50):
        draw.line([(0, y), (800, y)], fill="#B0C4DE", width=2)
    draw.line([(100, 0), (100, 800)], fill="#FA8072", width=3)
    
    # টেক্সট ড্রয়িং
    draw.text((120, 50), f"GRAMMAR LESSON: {topic.upper()}", fill="#B22222", font_size=28)
    draw.text((120, 130), "📌 FORMULA & RULES:", fill="#000080", font_size=24)
    
    # ফর্মুলা ফরম্যাটিং
    y_offset = 180
    for line in formula.split('\n'):
        draw.text((120, y_offset), line, fill="#333333", font_size=22)
        y_offset += 50
        
    img.save("lesson.png")

def main():
    print("Starting Automated Grammar Bot...")
    
    content = get_seo_content_from_gemini()
    create_notebook_image(content["topic"], content["formula"])
    
    caption = f"📘 **Topic:** {content['topic']}\n\n{content['seo_caption']}"
    
    with open("lesson.png", "rb") as photo:
        bot.send_photo(CHANNEL_ID, photo, caption=caption, parse_mode="Markdown")
    
    for index, q in enumerate(content["questions"], start=1):
        bot.send_poll(
            chat_id=CHANNEL_ID,
            question=f"{index}. {q['question']}",
            options=q["options"],
            type="quiz",
            correct_option_id=q["correct_index"],
            explanation=q.get("explanation", "Correct Answer"),
            is_anonymous=True
        )
        time.sleep(3)
        
    print("Post sent successfully!")

if __name__ == "__main__":
    main()
    
