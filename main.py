import asyncio
import os
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = AsyncTeleBot(TOKEN)

# Обработка команд /start и /help
@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    text = 'Привет! Я EchoBot.\nПросто напиши что-нибудь, и я повторю.'
    await bot.reply_to(message, text)

# Обработка всех остальных текстовых сообщений
@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    await bot.reply_to(message, message.text)

# Точка входа
if __name__ == "__main__":
    print("Бот запущен...")
    asyncio.run(bot.polling())
