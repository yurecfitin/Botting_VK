import asyncio
import csv
import io
import os
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import aiosqlite
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [6113518001]  # ID админов, кому присылать уведомления

MANAGER_URL = "https://t.me/bolotovvyacheslav"
REVIEWS_URL = "https://t.me/otzyvy_bolotov"

LESSON_TITLE = "Этика в консультировании"
LESSON_DATE = "00.00.2026"
LESSON_TIME = "00:00"

# ВАЖНО: укажите реальную дату и время урока для напоминаний
LESSON_DT = datetime(2026, 1, 1, 0, 0, tzinfo=ZoneInfo("Europe/Moscow"))
LESSON_LINK = "https://t.me/..."  # ссылка на онлайн-трансляцию

DB_PATH = "bot.db"

# ================== ТЕКСТЫ ==================
MSG1 = (
    "👋 <b>Добро пожаловать в бота Школы практической астрологии!</b>\n"
    "Хочешь заглянуть в мир звёзд и понять, как планеты влияют на твою жизнь?\n"
    "У нас есть:\n"
    "✨ <b>Бесплатный урок</b> — чтобы почувствовать стиль обучения и увидеть реальные разборы.\n"
    "🗣 <b>Консультация с астрологом</b> — разберём твой запрос и дадим персональные рекомендации.\n"
    "📚 <b>Обучение с практикой</b> — от основ до уверенной работы с картами."
)

MSG2 = (
    f"Я помогу зарегистрироваться на бесплатный онлайн урок "
    f"«{LESSON_TITLE}», который пройдет {LESSON_DATE} г. в {LESSON_TIME} часов "
    f"по московскому времени."
)

MSG3 = "Введите Вашу фамилию и нажмите «Далее»"
MSG4 = "Введите ваше имя и нажмите «Далее»"
MSG5 = "Введите ваш номер телефона и нажмите «Далее»"
MSG6 = "Расскажите о вашей квалификации в астрологии"

MSG7 = (
    f"<b>Поздравляю!🔥</b> Вы зарегистрировались на бесплатный онлайн урок "
    f"«{LESSON_TITLE}», который пройдет {LESSON_DATE} г. в {LESSON_TIME} часов "
    f"по московскому времени. За 10 минут до начала урока я пришлю Вам ссылку "
    f"на онлайн трансляцию."
)

MSG_WHAT_LESSON = (
    f"💎<b>Бесплатный онлайн урок {LESSON_DATE} г. в {LESSON_TIME} часов по московскому времени "
    f"«{LESSON_TITLE}»</b>\n\n"
    "✨<b>Тема, о которой вспоминают редко.</b> Об этике говорят мало. Повышают экспертность, "
    "осваивают инструменты, а вопрос «как себя вести с человеком, который вам доверился» "
    "часто остаётся без ответа. А потом начинается: клиент ушёл в тревогу после консультации, "
    "консультант выгорел, границы размыты, деньги обсуждать неловко, а «а можно я просто "
    "дружески подскажу» превращается в проблему для обоих.\n\n"
    "❇️<b>Этика — это не мораль и не набор запретов. Это то, что защищает и клиента, и вас.</b>\n\n"
    "✅<b>Разберём на уроке:</b>\n"
    "• где заканчивается ваша ответственность и начинается ответственность клиента;\n"
    "• как говорить о сложном, не пугая человека;\n"
    "• границы: время, деньги, личное общение, соцсети;\n"
    "• когда консультацию нужно остановить или передать другому специалисту;\n"
    "• как не забирать чужие проблемы себе.\n\n"
    "👥<b>Кому будет полезно?</b> Всем, кто работает с людьми: астрологам, психологам, "
    "коучам, тренерам, консультантам, тарологам, нутрициологам, HR-специалистам, "
    "наставникам, преподавателям — и тем, кто только планирует консультировать.\n\n"
    "📑<b>Ведёт урок Вячеслав Болотов</b> — сертифицированный бизнес-тренер, "
    "профессиональный астролог, основатель Школы практической астрологии.\n\n"
    "🎉<b>Участие БЕСПЛАТНОЕ, предварительная регистрация ОБЯЗАТЕЛЬНА.</b>"
)

# ================== КЛАВИАТУРЫ ==================
def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Стать астрологом", callback_data="become_astrologer")
    builder.button(text="🔥 Бесплатный урок", callback_data="free_lesson")
    builder.button(text="✨ Получить консультацию", callback_data="consult")
    builder.button(text="❓ Задать вопрос", callback_data="question")
    builder.button(text="📝 Отзывы", url=REVIEWS_URL)
    builder.adjust(1)
    return builder.as_markup()


def lesson_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Регистрируюсь!", callback_data="register_start")
    builder.button(text="❓ Что за урок?", callback_data="what_lesson")
    builder.button(text="⏪ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def what_lesson_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Регистрируюсь!", callback_data="register_start")
    builder.button(text="⏪ Назад", callback_data="free_lesson")
    builder.adjust(1)
    return builder.as_markup()


def form_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="⏩ Далее", callback_data="form_next")
    builder.button(text="⏪ Назад", callback_data="form_back")
    builder.adjust(1)
    return builder.as_markup()


def qual_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="😎 Разбираюсь, профи", callback_data="qual_pro")
    builder.button(text="🤔 Интересуюсь", callback_data="qual_interest")
    builder.button(text="🤩 Хочу изучать", callback_data="qual_learn")
    builder.adjust(1)
    return builder.as_markup()

# ================== БАЗА ДАННЫХ ==================
async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                last_name TEXT,
                first_name TEXT,
                phone TEXT,
                qualification TEXT,
                registered_at TEXT,
                sent_24h INTEGER DEFAULT 0,
                sent_10m INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def save_registration(user_id, username, last_name, first_name, phone, qualification):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO registrations
            (user_id, username, last_name, first_name, phone, qualification, registered_at, sent_24h, sent_10m)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
        """, (user_id, username, last_name, first_name, phone, qualification, datetime.now().isoformat()))
        await db.commit()


async def get_users_for_reminder(field: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(f"SELECT user_id FROM registrations WHERE {field}=0")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def mark_sent(field: str, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE registrations SET {field}=1 WHERE user_id=?", (user_id,))
        await db.commit()


async def get_all_registrations():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id, username, last_name, first_name, phone, qualification, registered_at FROM registrations"
        )
        return await cursor.fetchall()
print(get_all_registrations())

# ================== СОСТОЯНИЯ ==================
class Form(StatesGroup):
    last_name = State()
    first_name = State()
    phone = State()

# ================== РОУТЕР ==================
router = Router()

# ---------- Старт и главное меню ----------
@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(MSG1, reply_markup=main_menu_kb())


@router.callback_query(F.data == "main_menu")
async def main_menu_cb(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(MSG1, reply_markup=main_menu_kb())
    await cb.answer()


# ---------- Бесплатный урок ----------
@router.callback_query(F.data == "free_lesson")
async def free_lesson_cb(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(MSG2, reply_markup=lesson_kb())
    await cb.answer()


@router.callback_query(F.data == "what_lesson")
async def what_lesson_cb(cb: CallbackQuery):
    await cb.message.edit_text(MSG_WHAT_LESSON, reply_markup=what_lesson_kb())
    await cb.answer()


# ---------- Регистрация ----------
@router.callback_query(F.data == "register_start")
async def register_start_cb(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.last_name)
    await state.update_data(last_name=None, first_name=None, phone=None)
    await cb.message.edit_text(MSG3, reply_markup=form_kb())
    await cb.answer()


# Фамилия
@router.message(StateFilter(Form.last_name))
async def last_name_input(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())


@router.callback_query(StateFilter(Form.last_name), F.data == "form_next")
async def last_name_next(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("last_name"):
        await cb.answer("Сначала введите фамилию", show_alert=True)
        return
    await state.set_state(Form.first_name)
    await cb.message.edit_text(MSG4, reply_markup=form_kb())
    await cb.answer()


@router.callback_query(StateFilter(Form.last_name), F.data == "form_back")
async def last_name_back(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(MSG2, reply_markup=lesson_kb())
    await cb.answer()


# Имя
@router.message(StateFilter(Form.first_name))
async def first_name_input(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text.strip())


@router.callback_query(StateFilter(Form.first_name), F.data == "form_next")
async def first_name_next(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("first_name"):
        await cb.answer("Сначала введите имя", show_alert=True)
        return
    await state.set_state(Form.phone)
    await cb.message.edit_text(MSG5, reply_markup=form_kb())
    await cb.answer()


@router.callback_query(StateFilter(Form.first_name), F.data == "form_back")
async def first_name_back(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.last_name)
    await cb.message.edit_text(MSG3, reply_markup=form_kb())
    await cb.answer()


# Телефон
@router.message(StateFilter(Form.phone))
async def phone_input(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())


@router.callback_query(StateFilter(Form.phone), F.data == "form_next")
async def phone_next(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("phone"):
        await cb.answer("Сначала введите телефон", show_alert=True)
        return
    await state.set_state(None)
    await cb.message.edit_text(MSG6, reply_markup=qual_kb())
    await cb.answer()


@router.callback_query(StateFilter(Form.phone), F.data == "form_back")
async def phone_back(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.first_name)
    await cb.message.edit_text(MSG4, reply_markup=form_kb())
    await cb.answer()


# Квалификация
@router.callback_query(F.data.startswith("qual_"))
async def qualification_cb(cb: CallbackQuery, state: FSMContext):
    qual_map = {
        "qual_pro": "Разбираюсь, профи",
        "qual_interest": "Интересуюсь",
        "qual_learn": "Хочу изучать",
    }
    qualification = qual_map.get(cb.data)
    if not qualification:
        await cb.answer("Неизвестный вариант", show_alert=True)
        return

    data = await state.get_data()
    user = cb.from_user

    if not all([data.get("last_name"), data.get("first_name"), data.get("phone")]):
        await cb.answer("Не все данные заполнены. Начните регистрацию заново.", show_alert=True)
        await state.clear()
        return

    await save_registration(
        user_id=user.id,
        username=user.username,
        last_name=data.get("last_name"),
        first_name=data.get("first_name"),
        phone=data.get("phone"),
        qualification=qualification,
    )
    await state.clear()

    await cb.message.edit_text(MSG7, reply_markup=main_menu_kb())
    await cb.answer()

    admin_text = (
        f"🔥 <b>Новая регистрация на урок</b>\n"
        f"Имя: {data.get('first_name')} {data.get('last_name')}\n"
        f"Телефон: {data.get('phone')}\n"
        f"Квалификация: {qualification}\n"
        f"Username: @{user.username if user.username else 'нет'}\n"
        f"ID: {user.id}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await cb.bot.send_message(admin_id, admin_text)
        except Exception:
            pass


# ---------- Кнопки связи ----------
@router.callback_query(F.data == "become_astrologer")
async def become_astrologer_cb(cb: CallbackQuery):
    await cb.answer()
    await cb.message.answer(
        f"Ссылка для связи: {MANAGER_URL}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Написать", url=MANAGER_URL)]]
        ),
    )
    for admin_id in ADMIN_IDS:
        try:
            await cb.bot.send_message(
                admin_id,
                f"Пользователь @{cb.from_user.username} ({cb.from_user.id}) нажал «Стать астрологом»"
            )
        except Exception:
            pass


@router.callback_query(F.data == "consult")
async def consult_cb(cb: CallbackQuery):
    await cb.answer()
    await cb.message.answer(
        f"Ссылка для связи: {MANAGER_URL}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Написать", url=MANAGER_URL)]]
        ),
    )
    for admin_id in ADMIN_IDS:
        try:
            await cb.bot.send_message(
                admin_id,
                f"Пользователь @{cb.from_user.username} ({cb.from_user.id}) нажал «Получить консультацию»"
            )
        except Exception:
            pass


@router.callback_query(F.data == "question")
async def question_cb(cb: CallbackQuery):
    await cb.answer()
    await cb.message.answer(
        f"Ссылка для связи: {MANAGER_URL}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Написать", url=MANAGER_URL)]]
        ),
    )
    for admin_id in ADMIN_IDS:
        try:
            await cb.bot.send_message(
                admin_id,
                f"Пользователь @{cb.from_user.username} ({cb.from_user.id}) нажал «Задать вопрос»"
            )
        except Exception:
            pass


# ---------- Экспорт CSV ----------
@router.message(Command("export"))
async def export_cmd(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Нет доступа.")
        return

    rows = await get_all_registrations()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["user_id", "username", "last_name", "first_name", "phone", "qualification", "registered_at"])
    writer.writerows(rows)
    output.seek(0)

    file = BufferedInputFile(output.getvalue().encode("utf-8-sig"), filename="registrations.csv")
    await message.answer_document(file)

# ================== НАПОМИНАНИЯ ==================
async def reminder_loop(bot: Bot):
    while True:
        try:
            now = datetime.now(ZoneInfo("Europe/Moscow"))

            # За 24 часа
            if LESSON_DT - timedelta(hours=24) <= now < LESSON_DT:
                users = await get_users_for_reminder("sent_24h")
                for user_id in users:
                    try:
                        await bot.send_message(
                            user_id,
                            f"⏰ Напоминание: завтра в {LESSON_TIME} МСК состоится бесплатный урок «{LESSON_TITLE}».\n"
                            f"Не забудьте подключиться!"
                        )
                        await mark_sent("sent_24h", user_id)
                    except Exception:
                        pass

            # За 10 минут
            if LESSON_DT - timedelta(minutes=10) <= now < LESSON_DT + timedelta(hours=2):
                users = await get_users_for_reminder("sent_10m")
                for user_id in users:
                    try:
                        await bot.send_message(
                            user_id,
                            f"🚀 Урок начнется через 10 минут!\n"
                            f"Ссылка на трансляцию: {LESSON_LINK}"
                        )
                        await mark_sent("sent_10m", user_id)
                    except Exception:
                        pass

        except Exception:
            logging.exception("Ошибка в reminder_loop")

        await asyncio.sleep(60)

# ================== ЗАПУСК ==================
async def main():
    logging.basicConfig(level=logging.INFO)
    await db_init()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    asyncio.create_task(reminder_loop(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
