import asyncio
import os
from telebot.async_telebot import AsyncTeleBot

TOKEN = "7842967942:AAHrHAIabZNZBWEnBfEHzxjhLKR5ar4e994"

bot = AsyncTeleBot(token=TOKEN)

# Обработка команд /start и /help
@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    text = 'Здравствуйте, {}!\nПриглашаем вас принять участие в {}, которое состоится {} в {}.'.format(message.from_user.first_name, "ДогиСтаил", 18, 30)
    await bot.reply_to(message, text)

# Обработка всех остальных текстовых сообщений
@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    await bot.reply_to(message, message.text)

# Точка входа
if __name__ == "__main__":
    print("Бот запущен...")
    asyncio.run(bot.polling())
