import os
import json
import logging
import asyncio
from quart import Quart, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

# === НАСТРОЙКИ ===
BOT_TOKEN = "7299798795:AAENrfSLJwygoVbVIh0pFWDKfwZ-RFuaEhI"
DEEPSEEK_API_KEY = "sk-e975193325004dde8ebc9a588258724f"
WEBHOOK_URL = f"https://YOUR_RENDER_URL/webhook/{BOT_TOKEN}"

# === ИНИЦИАЛИЗАЦИЯ ===
app = Quart(__name__)
application = Application.builder().token(BOT_TOKEN).build()
logging.basicConfig(level=logging.INFO)

# === OpenAI SDK с DeepSeek API ===
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# === DeepSeek вызов ===
async def call_deepseek_stream(prompt: str) -> str:
    try:
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"DeepSeek API error: {e}")
        return "Не удалось получить ответ от DeepSeek."

# === ХЕНДЛЕРЫ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "*👋 Привет\\!*\n\n"
        "Я — 🤖 *AI бот на базе DeepSeek*\\.\n\n"
        "*Мой создатель:* \\[@jumpscare1\\]\n\n"
        "*📌 Что я умею:*\n"
        "• Отвечать на любые вопросы\n"
        "• Объяснять сложные темы\n"
        "• Помогать с кодом и не только\n\n"
        "_Просто напиши сообщение, и я отвечу\\!_ ✨"
    )
    await update.message.reply_text(welcome, parse_mode="MarkdownV2")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    reply = await call_deepseek_stream(user_message)
    await update.message.reply_text(reply)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === ВЕБХУК ===
f"/webhook/{BOT_TOKEN}"
async def webhook():
    try:
        data = await request.get_json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logging.error(f"Exception in webhook: {e}")
    return "", 200

# === MAIN ===
async def main():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(url=WEBHOOK_URL)

    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    config = Config()
    config.bind = [f"0.0.0.0:{os.environ.get('PORT', '10000')}"]
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())
