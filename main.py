import json
import Vk_api
import os
from dotenv import load_dotenv
from Vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from Vk_api.keyboard import VkKeyboard, VkKeyboardColor
from Vk_api.utils import get_random_id

load_dotenv()
# --- Настройки ---
TOKEN = "BOT_TOKEN"
GROUP_ID = 241613848

EVENT = {
    "id": 1,
    "title": "Python Meetup",
    "date": "25.09.2026",
    "place": "Москва, ул. Тверская, 1",
}

# --- Хранилища ---
USER_STATE = {}       # user_id -> {"step": ..., "data": {...}}
REGISTRATIONS = {}    # user_id -> {"name": ..., "city": ..., "contact": ...}
USER_CACHE = {}       # user_id -> "Имя Фамилия"

# --- Подключение ---
vk_session = Vk_api.VkApi(token=os.getenv("BOT_TOKEN"))
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)


# ---------- Утилиты ----------

def parse_payload(payload):
    if not payload:
        return {}
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return {}
    return payload if isinstance(payload, dict) else {}


def get_user_name(user_id):
    if user_id in USER_CACHE:
        return USER_CACHE[user_id]
    try:
        info = vk.users.get(user_ids=user_id, fields="first_name,last_name")[0]
        name = f"{info['first_name']} {info['last_name']}"
    except Exception:
        name = "друг"
    USER_CACHE[user_id] = name
    return name


def send(peer_id, message, keyboard=None):
    vk.messages.send(
        peer_id=peer_id,
        message=message,
        keyboard=keyboard,
        random_id=get_random_id()
    )


def answer(obj, text):
    vk.messages.send_message_event_answer(
        event_id=obj["event_id"],
        user_id=obj["user_id"],
        peer_id=obj["peer_id"],
        event_data=json.dumps({"type": "show_snackbar", "text": text})
    )


def edit(peer_id, cmid, message, keyboard=None):
    vk.messages.edit(
        peer_id=peer_id,
        conversation_message_id=cmid,
        message=message,
        keyboard=keyboard
    )


# ---------- Клавиатуры ----------

def kb_main():
    kb = VkKeyboard(inline=True)
    kb.add_callback_button("🎫 Записаться", VkKeyboardColor.POSITIVE,
                           {"cmd": "register"})
    kb.add_callback_button("📄 О мероприятии", VkKeyboardColor.SECONDARY,
                           {"cmd": "about"})
    kb.add_line()
    kb.add_callback_button("👤 Моя заявка", VkKeyboardColor.PRIMARY,
                           {"cmd": "my"})
    return kb.get_keyboard()


def kb_cancel():
    kb = VkKeyboard(inline=True)
    kb.add_callback_button("❌ Отмена", VkKeyboardColor.NEGATIVE,
                           {"cmd": "cancel"})
    return kb.get_keyboard()


def kb_confirm():
    kb = VkKeyboard(inline=True)
    kb.add_callback_button("✅ Подтвердить", VkKeyboardColor.POSITIVE,
                           {"cmd": "confirm"})
    kb.add_callback_button("✏️ Изменить", VkKeyboardColor.SECONDARY,
                           {"cmd": "restart"})
    kb.add_line()
    kb.add_callback_button("❌ Отмена", VkKeyboardColor.NEGATIVE,
                           {"cmd": "cancel"})
    return kb.get_keyboard()


def kb_after_reg():
    kb = VkKeyboard(inline=True)
    kb.add_callback_button("❌ Отменить заявку", VkKeyboardColor.NEGATIVE,
                           {"cmd": "unregister"})
    return kb.get_keyboard()


def kb_back():
    kb = VkKeyboard(inline=True)
    kb.add_callback_button("⬅️ Назад", VkKeyboardColor.SECONDARY,
                           {"cmd": "back"})
    return kb.get_keyboard()


# ---------- Тексты ----------

def welcome_text(user_id):
    name = get_user_name(user_id)
    if user_id == 1119423367:
        return (
            f"Привет, {name}! 👋"
        )
    else:
        return (
            f"Привет, {name}! 👋\n\n"
            f"Это бот регистрации на «{EVENT['title']}».\n"
            f"📅 {EVENT['date']}\n"
            f"📍 {EVENT['place']}\n\n"
            "Выберите действие:"
        )


def about_text():
    return (
        f"📌 {EVENT['title']}\n"
        f"🗓 {EVENT['date']}\n"
        f"📍 {EVENT['place']}\n\n"
        "Регистрация занимает 1 минуту. Нужно указать имя, город и контакт."
    )


def my_registration_text(user_id):
    reg = REGISTRATIONS.get(user_id)
    if not reg:
        return "У вас пока нет заявки. Нажмите «🎫 Записаться», чтобы создать."
    return (
        "👤 Ваша заявка:\n\n"
        f"Имя: {reg['name']}\n"
        f"Город: {reg['city']}\n"
        f"Контакт: {reg['contact']}\n\n"
        "Всё верно?"
    )


# ---------- Логика шагов ----------

def start_registration(user_id, peer_id):
    USER_STATE[user_id] = {"step": "await_name", "data": {}}
    send(peer_id, "Шаг 1 из 3. Напишите ваше имя:", kb_cancel())


def on_name(user_id, peer_id, text, state):
    if len(text) < 2 or len(text) > 50:
        send(peer_id, "Имя должно быть от 2 до 50 символов. Попробуйте снова.",
             kb_cancel())
        return
    state["data"]["name"] = text
    state["step"] = "await_city"
    USER_STATE[user_id] = state
    send(peer_id, "Шаг 2 из 3. Напишите ваш город:", kb_cancel())


def on_city(user_id, peer_id, text, state):
    if len(text) < 2 or len(text) > 50:
        send(peer_id, "Название города от 2 до 50 символов. Попробуйте снова.",
             kb_cancel())
        return
    state["data"]["city"] = text
    state["step"] = "await_contact"
    USER_STATE[user_id] = state
    send(peer_id,
         "Шаг 3 из 3. Оставьте контакт для связи (телефон или @username):",
         kb_cancel())


def on_contact(user_id, peer_id, text, state):
    if len(text) < 3 or len(text) > 100:
        send(peer_id, "Контакт слишком короткий или длинный. Попробуйте снова.",
             kb_cancel())
        return
    state["data"]["contact"] = text
    state["step"] = "confirm"
    USER_STATE[user_id] = state

    d = state["data"]
    send(peer_id,
         f"Проверьте данные:\n\n"
         f"Имя: {d['name']}\n"
         f"Город: {d['city']}\n"
         f"Контакт: {d['contact']}\n\n"
         "Всё верно?",
         kb_confirm())


STEP_HANDLERS = {
    "await_name": on_name,
    "await_city": on_city,
    "await_contact": on_contact,
}


# ---------- Обработка сообщений ----------

def handle_message_new(msg):
    user_id = msg["from_id"]
    peer_id = msg["peer_id"]
    text = (msg.get("text") or "").strip()

    # Reply-кнопки (payload — dict)
    payload = parse_payload(msg.get("payload"))
    cmd = payload.get("cmd")

    # FSM: если пользователь в процессе ввода
    state = USER_STATE.get(user_id)
    if state and state.get("step") in STEP_HANDLERS:
        if text.lower() in ("/cancel", "отмена", "назад"):
            USER_STATE.pop(user_id, None)
            send(peer_id, "Отменено.", kb_main())
            return
        STEP_HANDLERS[state["step"]](user_id, peer_id, text, state)
        return

    # Обычные команды
    if text.lower() in ("/start", "начать", "привет", "меню"):
        send(peer_id, welcome_text(user_id), kb_main())
    elif cmd == "about" or text.lower() in ("/about", "о мероприятии"):
        send(peer_id, about_text(), kb_back())
    else:
        send(peer_id, "Не понял 🤔 Напишите /start", kb_main())


# ---------- Обработка callback ----------

def handle_message_event(obj):
    user_id = obj["user_id"]
    peer_id = obj["peer_id"]
    cmid = obj["conversation_message_id"]
    payload = parse_payload(obj.get("payload"))
    cmd = payload.get("cmd")

    # --- Запуск регистрации ---
    if cmd == "register":
        if user_id in REGISTRATIONS:
            answer(obj, "Вы уже записаны")
            edit(peer_id, cmid, my_registration_text(user_id),
                 kb_after_reg())
            return
        answer(obj, "Начинаем регистрацию")
        edit(peer_id, cmid, welcome_text(user_id), kb_back())
        start_registration(user_id, peer_id)

    # --- Подтверждение заявки ---
    elif cmd == "confirm":
        state = USER_STATE.get(user_id)
        if not state or state["step"] != "confirm":
            answer(obj, "Сессия устарела, начните заново")
            return
        REGISTRATIONS[user_id] = state["data"]
        USER_STATE.pop(user_id, None)
        answer(obj, "Заявка принята ✅")
        edit(peer_id, cmid,
             f"🎉 Вы успешно записаны на «{EVENT['title']}»!\n\n"
             f"📅 {EVENT['date']}\n"
             f"📍 {EVENT['place']}\n\n"
             "Ждём вас!",
             kb_after_reg())

    # --- Переделать заявку ---
    elif cmd == "restart":
        answer(obj, "Заполняем заново")
        USER_STATE.pop(user_id, None)
        start_registration(user_id, peer_id)

    # --- Отмена текущего шага ---
    elif cmd == "cancel":
        USER_STATE.pop(user_id, None)
        answer(obj, "Отменено")
        edit(peer_id, cmid, welcome_text(user_id), kb_main())

    # --- Отменить существующую заявку ---
    elif cmd == "unregister":
        if user_id in REGISTRATIONS:
            REGISTRATIONS.pop(user_id)
            answer(obj, "Заявка отменена")
            edit(peer_id, cmid,
                 "Ваша заявка отменена. Если передумаете — нажмите «🎫 Записаться».",
                 kb_main())
        else:
            answer(obj, "У вас нет заявки")

    # --- Моя заявка ---
    elif cmd == "my":
        answer(obj, "Показываю вашу заявку")
        edit(peer_id, cmid, my_registration_text(user_id),
             kb_after_reg() if user_id in REGISTRATIONS else kb_main())

    # --- О мероприятии ---
    elif cmd == "about":
        answer(obj, "О мероприятии")
        edit(peer_id, cmid, about_text(), kb_back())

    # --- Назад ---
    elif cmd == "back":
        answer(obj, "Главное меню")
        edit(peer_id, cmid, welcome_text(user_id), kb_main())


# ---------- Основной цикл ----------

def main():
    print("Бот регистрации запущен...")
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            handle_message_new(event.obj.message)
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            handle_message_event(event.obj)


if __name__ == "__main__":
    main()

