import random
import sqlite3
from datetime import datetime
from vkbottle.bot import Bot, Message

TOKEN = "vk1.a.rVUKcQRfGYXtbLF2wuxGFpSo_d2d3HomrqHk4cOGz__3emRBhH4Gp-tKxO_-NcpEG_qNFoZ1bXY3AYa7HeupU8QP08urjcFVa5SJMzpZAqWPSJJpZMb-3SS-9RXZk4DqFYoQElpRRXT7obWrPvLCcewbNEmpBWcEBUUnxJNoOyZ83fPbJ8Qk_3vdxQUyDsl7JmYh7Eu0KG0w-eLmjAvJ_Q"

ADMIN_IDS = [884626807, 607939625, 716267755]

COOLDOWN_SECONDS = 30

bot = Bot(token=TOKEN)

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

def is_admin(user_id):
    return user_id in ADMIN_IDS

@bot.on.message(text=("!старт", "!start"))
async def start_handler(message: Message):
    user_id = message.from_id
    register_user(user_id)
    await message.answer(
        "🔥 **Добро пожаловать в игру!**\n\n"
        "Твой стартовый баланс: **20 Пламени**.\n\n"
        "📌 **Команды:**\n"
        "`!баланс` — проверить Пламя\n"
        "`!рулетка <ставка>` — сыграть\n"
        "`!шансы` — вероятности\n"
        "`!топ` — таблица лидеров\n\n"
        "🎲 **Пример:** `!рулетка 10`"
    )

@bot.on.message(text="!баланс")
async def balance_handler(message: Message):
    user_id = message.from_id
    register_user(user_id)
    flame = get_user(user_id)[0]
    await message.answer(f"💎 **Твоё Пламя:** {flame} 🔥")

@bot.on.message(text="!шансы")
async def chances_handler(message: Message):
    await message.answer(
        "🎲 **ВЕРОЯТНОСТИ** 🎲\n\n"
        "• Полный проигрыш (0%) — 45%\n"
        "• Возврат 50% — 20%\n"
        "• Выигрыш 75% — 20%\n"
        "• Выигрыш 150% — 10%\n"
        "• ДЖЕКПОТ 300% — 5%"
    )

@bot.on.message(text="!топ")
async def top_handler(message: Message):
    conn = sqlite3.connect("flame.db")
    c = conn.cursor()
    c.execute("SELECT id, flame FROM users ORDER BY flame DESC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await message.answer("Пока нет игроков. Напиши !старт!")
        return

    text = "🏆 **ТОП ИГРОКОВ** 🏆\n\n"
    for i, (uid, flame) in enumerate(rows, 1):
        text += f"{i}. [id{uid}|] — {flame} 🔥\n"
    await message.answer(text)

@bot.on.message(text=("!рулетка <bet>", "!рулетка"))
async def roulette_handler(message: Message):
    user_id = message.from_id
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
        result = f"💥 **ПРОИГРЫШ!** -{bet}\n🔥 Осталось: {new_flame}"
    elif rand < 0.65:
        refund = int(bet * 0.5)
        update_flame(user_id, -bet + refund)
        new_flame = current_flame - bet + refund
        result = f"😐 **ВОЗВРАТ 50%** +{refund}\n🔥 Теперь: {new_flame}"
    elif rand < 0.85:
        win = int(bet * 0.75)
        update_flame(user_id, win)
        new_flame = current_flame + win
        result = f"🎉 **ВЫИГРЫШ 75%** +{win}\n🔥 Теперь: {new_flame}"
    elif rand < 0.95:
        win = int(bet * 1.5)
        update_flame(user_id, win)
        new_flame = current_flame + win
        result = f"🔥 **ВЫИГРЫШ 150%** +{win}\n🔥 Теперь: {new_flame}"
    else:
        win = int(bet * 3)
        update_flame(user_id, win)
        new_flame = current_flame + win
        result = f"🐉 **ДЖЕКПОТ 300%!** +{win}\n🔥 Теперь: {new_flame}"

    await message.answer(result)
    set_last_bet_time(user_id)

@bot.on.message(text=("!редакт <user> <amount>", "!редакт"))
async def edit_flame_handler(message: Message):
    if not is_admin(message.from_id):
        await message.answer("❌ Нет прав")
        return

    args = message.text.split()
    if len(args) != 3 or not message.mentions:
        await message.answer("Формат: !редакт @ник +10")
        return

    target_id = message.mentions[0].id
    raw = args[2]

    try:
        if raw.startswith("+"):
            delta = int(raw[1:])
            update_flame(target_id, delta)
            new_balance = get_user(target_id)[0]
            await message.answer(f"✅ +{delta} [id{target_id}|].\n🔥 Теперь: {new_balance}")
        elif raw.startswith("-"):
            delta = int(raw[1:])
            current = get_user(target_id)[0]
            if current < delta:
                await message.answer(f"❌ У игрока только {current} Пламени")
                return
            update_flame(target_id, -delta)
            new_balance = get_user(target_id)[0]
            await message.answer(f"✅ -{delta} [id{target_id}|].\n🔥 Осталось: {new_balance}")
        else:
            await message.answer("Используй + или -")
    except:
        await message.answer("Ошибка в сумме")

if __name__ == "__main__":
    init_db()
    print("Бот запущен")
    bot.run_forever()
