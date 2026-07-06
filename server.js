const express = require('express');
const TelegramBot = require('node-telegram-bot-api');
const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => res.send('Bot is Active'));
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const AD_LINK = process.env.ADSTERRA_LINK;

let monthlyScores = {}; 

bot.on('poll_answer', (answer) => {
    const userId = answer.user.id;
    const name = answer.user.first_name;
    if (!monthlyScores[userId]) monthlyScores[userId] = { name, score: 0 };
    if (answer.option_ids.includes(0)) {
        monthlyScores[userId].score += 1;
    }
});

async function postContent() {
    const model = genAI.getGenerativeModel({ model: "gemini-pro" });
    const guidePrompt = "Write an advanced English Grammar lesson. Use Markdown. Title must be linked to " + AD_LINK + ". Content must be SEO friendly.";
    const guideResult = await model.generateContent(guidePrompt);
    
    await bot.sendMessage(process.env.CHANNEL_ID, `[Click here for Advanced Guide](${AD_LINK})\n\n${guideResult.response.text()}`, { parse_mode: 'Markdown' });

    for (let i = 0; i < 5; i++) {
        const qPrompt = `Generate a hard English grammar MCQ. JSON: {"q": "Question", "o": ["Correct", "Wrong1", "Wrong2", "Wrong3"]}`;
        const qResult = await model.generateContent(qPrompt);
        const data = JSON.parse(qResult.response.text().replace(/```json|```/g, ""));
        
        await bot.sendPoll(process.env.CHANNEL_ID, `[${data.q}](${AD_LINK})`, data.o, {
            type: 'quiz',
            correct_option_id: 0,
            parse_mode: 'Markdown'
        });
    }
}

// প্রতিদিন পোস্ট হবে
setInterval(postContent, 86400000);

