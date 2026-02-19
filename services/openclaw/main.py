import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from config import settings
from agent import OpenClawAgent
import uvicorn
from fastapi import FastAPI
import threading

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = FastAPI()
agent = OpenClawAgent()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "openclaw"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="🦅 OpenClaw Online. Waiting for commands."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    response = await agent.process_message(user_id, text)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response
    )

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)

if __name__ == '__main__':
    # Start Health Check API in a separate thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Start Telegram Bot
    if not settings.TELEGRAM_BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN is missing. Bot cannot start.")
    else:
        application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
        
        start_handler = CommandHandler('start', start)
        message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
        
        application.add_handler(start_handler)
        application.add_handler(message_handler)
        
        logging.info("Starting OpenClaw Polling...")
        application.run_polling()
