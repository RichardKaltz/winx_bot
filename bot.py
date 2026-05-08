import random
import sqlite3
import json
import os
from datetime import datetime
from vkbottle.bot import Bot, Message

TOKEN = "vk1.a.rVUKcQRfGYXtbLF2wuxGFpSo_d2d3HomrqHk4cOGz__3emRBhH4Gp-tKxO_-NcpEG_qNFoZ1bXY3AYa7HeupU8QP08urjcFVa5SJMzpZAqWPSJJpZMb-3SS-9RXZk4DqFYoQElpRRXT7obWrPvLCcewbNEmpBWcEBUUnxJNoOyZ83fPbJ8Qk_3vdxQUyDsl7JmYh7Eu0KG0w-eLmjAvJ_Q"

GLOBAL_ADMINS = [884626807, 607939625, 716267755]

COOLDOWN_SECONDS = 30

IMG_START = "https://i.postimg.cc/65JSmKmK/start.jpg"
IMG_BALANCE = "https://i.postimg.cc/5yx4BzLd/balance.jpg"
IMG_WIN_150 = "https://i.postimg.cc/8kBBTVCS/win.jpg"
IMG_LOSE = "https://i.postimg.cc/Vk5j9rW5/lose.jpg"
IMG_WIN_75 = "https://i.postimg.cc/mkNSnvPy/miniwin.jpg"
IMG_REFUND = "https://i.postimg.cc/qqCPCMZr/balfive.jpg"
IMG_JACKPOT = "https://i.postimg.cc/zfsSGzWH/jackpot.jpg"

bot = Bot(token=TOKEN)

def get_user_link(uid):
    try:
        user = bot.api.users.get(user_ids=uid)[0]
        name = user.first_name if user.first_name else "Игрок"
        if user.last_name:
            name += " " + user.last_name
        return f"[id{uid}|{name}]"
    except:
        return f"[id{uid}|Игрок]"

ADMINS_FILE = "chat_admins.json"

def load_chat_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_chat_admins(data):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_chat_admins(chat_id):
    data = load_chat_admins()
    return data.get(str(chat_id), [])

def add_chat_admin(chat_id, user_id):
    data = load_chat_admins()
    key = str(chat_id)
    if key not in data:
        data[key] = []
    if user_id not in data[key]:
        data[key].append(user_id)
        save_chat_admins(data)
        return True
    return False

def remove_chat_admin(chat_id, user_id):
    data = load_chat_admins()
    key = str(chat_id)
    if key in data and user_id in data[key]:
        data[key].remove(user_id)
        save_chat_admins(data)
        return True
    return False

def is_chat_admin(chat_id, user_id):
    return user_id in get_chat_admins(chat_id)

def is_chat_owner(message):
    try:
        chat_info = bot.api.messages.get_conversations_by_id(peer_ids=message.peer_id)
        if chat_info.items and chat_info.items[0].chat_settings:
            owner_id = chat_info.items[0].chat_settings.owner_id
            return message.from_id == owner_id
    except:
        pass
    return False

def is_admin_in_context(message):
    user_id = message.from_id
    chat_id = message.peer_id
    if user_id in GLOBAL_ADMINS:
        return True
    return is_chat_admin(chat_id, user_id)

def init_db():
    conn = sqlite3.connect("flame.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY,
                flame INTEGER DEFAULT 20,
                last_bet_time TEXT)''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("flame.db")
    c = conn.cursor()
    c.execute("SELECT flame, last_bet_time FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def register_user(user_id):
    conn = sqlite3.connect("flame.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, flame) VALUES (?, 20)", (user_id,))
    conn.commit()
    conn.close()

def update_flame(user_id, delta):
    conn = sqlite3.connect("flame.db")
    c = conn.cursor()
    c.execute("UPDATE users SET flame = flame + ? WHERE id = ?", (delta, user_id))
    conn.commit()
    conn.close()

def set_last_bet_time(user_id):
    conn = sqlite3.connect("flame.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_bet_time = ? WHERE id = ?", (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def can_bet(user_id):
    row = get_user(user_id)
    if not row or not row[1]:
        return True
    last_time = row[1]
    if not last_time:
        return True
    last = datetime.fromisoformat(last_time)
    return (datetime.now() - last).total_seconds() >= COOLDOWN_SECONDS

@bot.on.message(text=("!старт", "!start"))
async def start_handler(message: Message):
    user_id = message.peer_id
    register_user(user_id)
    await message.answer(
        "🔥 **Добро пожаловать в игру!**\n\n"
        "Твой стартовый баланс: **20 Пламени**.\n\n"
        "📌 **Команды:**\n"
        "`!баланс` — проверить Пламя\n"
        "`!рулетка <ставка>` — сыграть\n"
        "`!шансы` — узнать вероятности\n"
        "`!топ` — все игроки\n"
        "`!команды` — список команд\n\n"
        "🎲 **Пример:** `!рулетка 10`",
        attachment=IMG_START
    )

@bot.on.message(text="!баланс")
async def balance_handler(message: Message):
    user_id = message.peer_id
    register_user(user_id)
    flame = get_user(user_id)[0]
    await message.answer(
        f"💎 **Твоё Пламя:** {flame} 🔥",
        attachment=IMG_BALANCE
    )

@bot.on.message(text="!шансы")
async def chances_handler(message: Message):
    await message.answer(
        "🎲 **ВЕРОЯТНОСТИ В РУЛЕТКЕ** 🎲\n\n"
        "💥 Полный проигрыш (0%) — 45%\n"
        "😐 Возврат 50% — 20%\n"
        "🎉 Выигрыш 75% — 20%\n"
        "🔥 Выигрыш 150% — 10%\n"
        "🐉 ДЖЕКПОТ 300% — 5%\n\n"
        "Удачи! 🍀"
    )

@bot.on.message(text="!топ")
async def top_handler(message: Message):
    user_id = message.peer_id
    register_user(user_id)

    conn = sqlite3.connect("flame.db")
    c = conn.cursor()
    c.execute("SELECT id, flame FROM users ORDER BY flame DESC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await message.answer("Пока нет участников. Напиши !старт, чтобы начать!")
        return

    top_text = "🏆 **ВСЕ ИГРОКИ ПО ПЛАМЕНИ** 🏆\n\n"
    for i, (uid, flame) in enumerate(rows, 1):
        user_link = get_user_link(uid)
        line = f"{i}. {user_link} — {flame} 🔥\n"
        if len(top_text) + len(line) > 4000:
            await message.answer(top_text)
            top_text = line
        else:
            top_text += line

    if top_text:
        await message.answer(top_text)

@bot.on.message(text=("!команды", "!help"))
async def commands_handler(message: Message):
    await message.answer(
        "📜 **СПИСОК КОМАНД** 📜\n\n"
        "👤 **Для всех:**\n"
        "!старт — регистрация, баланс 20\n"
        "!баланс — показать Пламя\n"
        "!рулетка <ставка> — сыграть\n"
        "!шансы — вероятности\n"
        "!топ — все игроки\n"
        "!команды — этот список\n\n"
        "👑 **Администраторам:**\n"
        "• !редакт @ник +15 — изменить баланс\n"
        "• Ответь на сообщение игрока и напиши +10 / -5 / =50\n\n"
        "🔧 **Владельцу чата:**\n"
        "• !добавить_админа @ник — назначить админа бота\n"
        "• !удалить_админа @ник — удалить админа\n"
        "• !список_админов — показать админов\n\n"
        "🐉 Удачи!"
    )

@bot.on.message(text=("!рулетка <bet>", "!рулетка"))
async def roulette_handler(message: Message):
    user_id = message.peer_id
    register_user(user_id)

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("Напиши: !рулетка 10")
        return

    bet = int(args[1])
    current_flame = get_user(user_id)[0]

    if bet <= 0:
        await message.answer("Ставка должна быть больше 0")
        return
    if bet > current_flame:
        await message.answer(f"У тебя только {current_flame} Пламени")
        return
    if not can_bet(user_id):
        await message.answer(f"Подожди {COOLDOWN_SECONDS} секунд")
        return

    rand = random.random()

    if rand < 0.45:
        update_flame(user_id, -bet)
        new_flame = current_flame - bet
        text = f"💥 **ПРОИГРЫШ!**\n\nТы потерял {bet} Пламени."
        img = IMG_LOSE
    elif rand < 0.65:
        refund = int(bet * 0.5)
        update_flame(user_id, -bet + refund)
        new_flame = current_flame - bet + refund
        text = f"😐 **ВОЗВРАТ 50%**\n\nТы вернул {refund} Пламени."
        img = IMG_REFUND
    elif rand < 0.85:
        win_amount = int(bet * 0.75)
        update_flame(user_id, win_amount)
        new_flame = current_flame + win_amount
        text = f"🎉 **ВЫИГРЫШ 75%**\n\nТы выиграл +{win_amount} Пламени."
        img = IMG_WIN_75
    elif rand < 0.95:
        win_amount = int(bet * 1.5)
        update_flame(user_id, win_amount)
        new_flame = current_flame + win_amount
        text = f"🔥 **ВЫИГРЫШ 150%**\n\nТы выиграл +{win_amount} Пламени (x1.5)!"
        img = IMG_WIN_150
    else:
        win_amount = int(bet * 3)
        update_flame(user_id, win_amount)
        new_flame = current_flame + win_amount
        text = f"🐉 **ДЖЕКПОТ x3!**\n\nТы выиграл +{win_amount} Пламени!"
        img = IMG_JACKPOT

    await message.answer(f"{text}\n\n🔥 Теперь у тебя {new_flame} Пламени.", attachment=img)
    set_last_bet_time(user_id)

@bot.on.message(text=("!редакт <user> <amount>", "!редакт"))
async def edit_flame_handler(message: Message):
    if not is_admin_in_context(message):
        await message.answer("❌ Только администратор бота может редактировать баланс.")
        return

    args = message.text.split()
    if len(args) != 3 or not message.mentions:
        await message.answer("Формат: !редакт @ник +15")
        return

    target_id = message.mentions[0].id
    raw = args[2]

    try:
        if raw.startswith("+"):
            delta = int(raw[1:])
            update_flame(target_id, delta)
            new_balance = get_user(target_id)[0]
            await message.answer(f"✅ +{delta} Пламени [id{target_id}|].\n🔥 Теперь: {new_balance}")
        elif raw.startswith("-"):
            delta = -int(raw[1:])
            current = get_user(target_id)[0]
            if current + delta < 0:
                await message.answer(f"❌ У игрока только {current} Пламени")
                return
            update_flame(target_id, delta)
            new_balance = get_user(target_id)[0]
            await message.answer(f"✅ -{ -delta } Пламени у [id{target_id}|].\n🔥 Осталось: {new_balance}")
        elif raw.startswith("="):
            new_value = int(raw[1:])
            if new_value < 0:
                await message.answer("❌ Баланс не может быть отрицательным")
                return
            current = get_user(target_id)[0]
            delta = new_value - current
            update_flame(target_id, delta)
            await message.answer(f"✅ Баланс [id{target_id}|] установлен на {new_value}")
        else:
            await message.answer("Используй +, - или =")
    except:
        await message.answer("Ошибка в сумме")

@bot.on.message(text=("+<amount>", "-<amount>", "=<amount>"))
async def quick_edit_handler(message: Message):
    if not is_admin_in_context(message):
        return

    if not message.reply_message:
        await message.answer("❌ Ответь на сообщение игрока, потом +10 / -5 / =50")
        return

    target_id = message.reply_message.from_id
    raw = message.text.strip()

    try:
        if raw.startswith("+"):
            delta = int(raw[1:])
            update_flame(target_id, delta)
            new_balance = get_user(target_id)[0]
            await message.answer(f"✅ +{delta} Пламени [id{target_id}|].\n🔥 Теперь: {new_balance}")
        elif raw.startswith("-"):
            delta = -int(raw[1:])
            current = get_user(target_id)[0]
            if current + delta < 0:
                await message.answer(f"❌ У игрока только {current} Пламени")
                return
            update_flame(target_id, delta)
            new_balance = get_user(target_id)[0]
            await message.answer(f"✅ -{ -delta } Пламени у [id{target_id}|].\n🔥 Осталось: {new_balance}")
        elif raw.startswith("="):
            new_value = int(raw[1:])
            if new_value < 0:
                await message.answer("❌ Баланс не может быть отрицательным")
                return
            current = get_user(target_id)[0]
            delta = new_value - current
            update_flame(target_id, delta)
            await message.answer(f"✅ Баланс [id{target_id}|] установлен на {new_value}")
        else:
            await message.answer("Используй +10, -5 или =50")
    except ValueError:
        await message.answer("❌ Сумма должна быть целым числом")

@bot.on.message(text=("!добавить_админа <user>", "!добавить_админа"))
async def add_admin_handler(message: Message):
    if not is_chat_owner(message):
        await message.answer("❌ Только создатель беседы может назначать админов бота.")
        return

    if not message.mentions:
        await message.answer("❌ Упомяни игрока: !добавить_админа @имя")
        return

    target_id = message.mentions[0].id
    chat_id = message.peer_id

    if add_chat_admin(chat_id, target_id):
        await message.answer(f"✅ [id{target_id}|] теперь администратор бота в этой беседе.")
    else:
        await message.answer(f"❌ [id{target_id}|] уже в списке администраторов.")

@bot.on.message(text=("!удалить_админа <user>", "!удалить_админа"))
async def remove_admin_handler(message: Message):
    if not is_chat_owner(message):
        await message.answer("❌ Только создатель беседы может удалять админов бота.")
        return

    if not message.mentions:
        await message.answer("❌ Упомяни игрока: !удалить_админа @имя")
        return

    target_id = message.mentions[0].id
    chat_id = message.peer_id

    if remove_chat_admin(chat_id, target_id):
        await message.answer(f"✅ [id{target_id}|] больше не администратор бота.")
    else:
        await message.answer(f"❌ [id{target_id}|] не был в списке администраторов.")

@bot.on.message(text="!список_админов")
async def list_admins_handler(message: Message):
    chat_id = message.peer_id
    admins = get_chat_admins(chat_id)

    text = "👑 **Администраторы бота в этой беседе:**\n\n"
    if admins:
        for uid in admins:
            text += f"• [id{uid}|]\n"
    else:
        text += "• Нет назначенных администраторов.\n"

    if GLOBAL_ADMINS:
        text += "\n🔧 **Глобальные администраторы (из кода):**\n"
        for uid in GLOBAL_ADMINS:
            text += f"• [id{uid}|]\n"

    await message.answer(text)

if __name__ == "__main__":
    init_db()
    print("🔥 Бот 'Пламенная рулетка' успешно запущен!")
    print(f"✅ Глобальные администраторы: {GLOBAL_ADMINS}")
    bot.run_forever()
