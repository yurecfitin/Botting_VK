import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import delete_webhook

TOKEN = "7842967942:AAEPT42rR5gHdx1qCyjvZ35PqAbFQFdWg9E"
bot = AsyncTeleBot(TOKEN)

# Временное хранилище (в реальном проекте — БД)
user_data = {}


@bot.message_handler(commands=['start'])
async def start_registration(message):
    await bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать!\n\nДавай познакомимся. Как тебя зовут?"
    )
    await process_name()


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
    # Удаляем webhook перед запуском polling
    await bot.delete_webhook()
    print("Webhook удалён, запускаем polling...")
    await bot.polling()

if __name__ == "__main__":
    print("Бот запущен...")
    asyncio.run(main())
