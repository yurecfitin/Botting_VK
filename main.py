import telebot
from telebot import types

bot = telebot.TeleBot('ТВОЙ_ТОКЕН')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Начать диалог'))
    bot.send_message(message.chat.id, 'Привет! Нажми кнопку.', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Начать диалог')
def start_dialog(message):
    # Убираем reply-клавиатуру, чтобы не мешала
    msg = bot.send_message(message.chat.id, 'Как тебя зовут?', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_name)

def process_name(message):
    name = message.text
    msg = bot.send_message(message.chat.id, 'Сколько тебе лет?')
    bot.register_next_step_handler(msg, process_age, name)

def process_age(message, name):
    age = message.text
    bot.send_message(message.chat.id, f'Приятно познакомиться, {name}! Тебе {age} лет.')

bot.polling(none_stop=True)
