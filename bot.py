import random
import sqlite3
import threading
import time
import requests
from datetime import datetime
from vkbottle.bot import Bot, Message

# ========== НАСТРОЙКИ ==========
TOKEN = "vk1.a.rVUKcQRfGYXtbLF2wuxGFpSo_d2d3HomrqHk4cOGz__3emRBhH4Gp-tKxO_-NcpEG_qNFoZ1bXY3AYa7HeupU8QP08urjcFVa5SJMzpZAqWPSJJpZMb-3SS-9RXZk4DqFYoQElpRRXT7obWrPvLCcewbNEmpBWcEBUUnxJNoOyZ83fPbJ8Qk_3vdxQUyDsl7JmYh7Eu0KG0w-eLmjAvJ_Q"

# Администраторы (твои ID)
ADMIN_IDS = [884626807, 607939625, 716267755]

# Настройки игр
ROULETTE_WIN_CHANCE = 5 / 6
COOLDOWN_SECONDS = 30

# ССЫЛКИ НА КАРТИНКИ (твои, очищенные):
IMG_START = "https://sun9-39.userapi.com/s/v1/ig2/0mNYdxv3UKOI_GIP0ulGo-bsm9Zd2bI_Dag&quot;
IMG_BALANCE = "https://sun9-60.userapi.com/s/v1/ig2/WLpnqkYSrEANY1EYKSh-dpBdLPm94WeCgKBFoc2eq7jo6sgVWvGt0N4HJkGWnakcv1QUBQW4pWr9fETgp-xwmpJs.jpg&quot;
IMG_WIN = "https://sun9-49.userapi.com/s/v1/ig2/8mmIPnFUDW2eHu-Eg3UCYJoZL102gS-TNAyxfxjFlumy1sUVg4kmEQgPiu8-rMEA7FaLvngSOyxkol9VlAUH3_bO.jpg&quot;
IMG_LOSE = "https://sun9-40.userapi.com/s/v1/ig2/OzPVuhqYzDJXmMQ7yMihdVuS7MqD8rxqDcx0Vzm3ZXSFHHUuMkeA0QvT1kS9KkNnq2qCo9IqcaZnfHZ7GH314kv9.jpg&quot;
# =================================

bot = Bot(token=TOKEN)

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("flame.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY,
                flame INTEGER DEFAULT 100,
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
    c.execute("INSERT OR IGNORE INTO users (id, flame) VALUES (?, 100)", (user_id,))
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

# --- КОМАНДЫ БОТА С КАРТИНКАМИ ---
@bot.on.message(text=("!старт", "!start"))
async def start_handler(message: Message):
    user_id = message.peer_id
    register_user(user_id)
    await message.answer(
        "🔥 **Добро пожаловать в игру!**\n\n"
        "Твой стартовый баланс: **100 Пламени**.\n\n"
        "📌 **Команды:**\n"
        "`!баланс` — проверить Пламя\n"
        "`!рулетка <ставка>` — сыграть (шанс 5/6)\n\n"
        "🎲 **Пример:** `!рулетка 25`",
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

@bot.on.message(text=("!рулетка <bet>", "!рулетка"))
async def roulette_handler(message: Message):
    user_id = message.peer_id
    register_user(user_id)

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ Напиши: `!рулетка 50`")
        return

    bet = int(args[1])
    current_flame = get_user(user_id)[0]

    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше 0")
        return
    if bet > current_flame:
        await message.answer(f"❌ У


тебя только {current_flame} Пламени. Не хватает.")
        return
    if not can_bet(user_id):
        await message.answer(f"⏳ Подожди {COOLDOWN_SECONDS} секунд до следующей ставки.")
        return

    win = random.random() < ROULETTE_WIN_CHANCE
    if win:
        update_flame(user_id, bet)
        new_flame = current_flame + bet
        await message.answer(
            f"🎉 **ЩЕЛЧОК! Пусто.**\n\n"
            f"Ты выиграл **+{bet}** Пламени!\n"
            f"🔥 Теперь у тебя **{new_flame}** Пламени.",
            attachment=IMG_WIN
        )
    else:
        update_flame(user_id, -bet)
        new_flame = current_flame - bet
        await message.answer(
            f"💥 **БАХ! Патрон.**\n\n"
            f"Ты потерял **{bet}** Пламени.\n"
            f"🔥 Осталось **{new_flame}** Пламени.",
            attachment=IMG_LOSE
        )
    set_last_bet_time(user_id)

# --- АДМИН-КОМАНДА ---
@bot.on.message(text=("!редакт <user> <amount>", "!редакт"))
async def edit_flame_handler(message: Message):
    if not is_admin(message.from_id):
        await message.answer("❌ Только администратор может редактировать баланс.")
        return

    args = message.text.split()
    if len(args) != 3 or not message.mentions:
        await message.answer("❌ **Формат:** `!редакт @ник +15`\n`!редакт @ник -10`\n`!редакт @ник =50`")
        return

    target_id = message.mentions[0].id
    raw_amount = args[2]

    try:
        if raw_amount.startswith("+"):
            delta = int(raw_amount[1:])
            update_flame(target_id, delta)
            new_balance = get_user(target_id)[0]
            await message.answer(f"✅ **Прибавлено {delta} Пламени** [id{target_id}|].\n🔥 Теперь: {new_balance}")
        elif raw_amount.startswith("-"):
            delta = -int(raw_amount[1:])
            current = get_user(target_id)[0]
            if current + delta < 0:
                await message.answer(f"❌ У игрока только {current} Пламени. Столько не отнять.")
                return
            update_flame(target_id, delta)
            new_balance = get_user(target_id)[0]
            await message.answer(f"✅ **Отнято { -delta } Пламени** у [id{target_id}|].\n🔥 Осталось: {new_balance}")
        elif raw_amount.startswith("="):
            new_value = int(raw_amount[1:])
            if new_value < 0:
                await message.answer("❌ Баланс не может быть отрицательным.")
                return
            current = get_user(target_id)[0]
            delta = new_value - current
            update_flame(target_id, delta)
            await message.answer(f"✅ **Баланс [id{target_id}|] установлен** на {new_value} Пламени.")
        else:
            await message.answer("❌ Используй **+**, **-** или **=**\nПримеры:\n`!редакт @ник +15`\n`!редакт @ник -7`\n`!редакт @ник =40`")
    except ValueError:
        await message.answer("❌ Сумма должна быть числом.")

# --- ЗАПУСК ---
if __name__ == "__main__":
    init_db()
    print("🔥 **Бот 'Пламенная рулетка' успешно запущен!**")
    print(f"✅ Администраторы: {ADMIN_IDS}")
    print("⚙️ Бот работает и готов к приёму команд.")
    bot.run_forever()