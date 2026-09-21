import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot.asyncio_helper import delete_webhook
import sqlite3

db = sqlite3.connect(DB_PATH)
cur = db.cursor()
cur.execute("""
            CREATE TABLE bot (
                id TEXT
            )
        """)
db.commit()



TOKEN = "7842967942:AAFyiTyIutMaxeKbRnADWLoVOx7Tt-h7bb0"
bot = AsyncTeleBot(TOKEN)

@bot.message_handler(commands=['start'])
async def start_registration(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn1 = types.KeyboardButton("📋 Каталог")
    markup.add(btn1)
    await bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать!\n\nДавай познакомимся. Как тебя зовут?",
        reply_markup=markup
    )
    await process_name(message)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                
            )
        """)
        await db.commit()

async def process_name(message):
    user_data[message.chat.id] = {"name": message.text}
    await bot.send_message(
        message.chat.id,
        f"Отлично, {message.text}!\n\nТеперь отправь свой номер телефона."
    )


async def process_phone(message):
    user_data[message.chat.id]["phone"] = message.text
    await bot.send_message(
        message.chat.id,
        "Спасибо! Укажи, пожалуйста, свой город."
    )


async def process_city(message):
    user_data[message.chat.id]["city"] = message.text
    data = user_data[message.chat.id]

    text = (
        "Проверь, пожалуйста, данные:\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🏙 Город: {data['city']}\n\n"
        "Всё верно? Напиши «Да» или «Нет»."
    )
    await bot.send_message(message.chat.id, text)


async def process_confirm(message):
    answer = message.text.strip().lower()

    if answer in ("да", "yes", "верно", "ага"):
        data = user_data.get(message.chat.id, {})
        await bot.send_message(
            message.chat.id,
            f"✅ Регистрация успешно завершена!\n\nСпасибо, {data.get('name', 'друг')}."
        )
        # Здесь можно сохранить данные в БД
    else:
        await bot.send_message(
            message.chat.id,
            "Хорошо, начнём заново. Напиши /start"
        )
        
async def main():
    await init_db()
    await bot.delete_webhook()
    print("Webhook удалён, запускаем polling...")
    await bot.polling()

if __name__ == "__main__":
    print("Бот запущен...")
    asyncio.run(main())
