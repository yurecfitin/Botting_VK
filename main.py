import asyncio
import os
from telebot.async_telebot import AsyncTeleBot
from telebot import types

TOKEN = "7842967942:AAHrHAIabZNZBWEnBfEHzxjhLKR5ar4e994"

bot = AsyncTeleBot(token=TOKEN)
# Обработка команд /start и /help
@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    #markup = types.InlineKeyboardMarkup()
    #btn = types.InlineKeyboardButton('Начать диалог', callback_data='start_dialog')
    #markup.add(btn)
    text = "Здравствуйте, {}!\nПриглашаем вас принять участие в {}, которое состоится {} в {}.".format(message.from_user.first_name, "ДогиСтаил", 18, 30)
    await bot.send_message(message, text)

# Обработка всех остальных текстовых сообщений
@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    await bot.reply_to(message, message.text)

# Точка входа
if __name__ == "__main__":
    print("Бот запущен...")
    asyncio.run(bot.polling())
