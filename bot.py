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
COOLDOWN_SECONDS = 30

# ========== КАРТИНКИ ==========
IMG_START = "https://i.ibb.co/2YPV3h36/a-DO9m6e-OC17rv-KQC833pr-BQHLm-Xc-Dor2-Hdb-EDfa8z-MOTZFit7-ADKs-VBFC9-Xi-O0xii71-AJFj3-Lm6r81-WQm-XR80lo.jpg"
IMG_BALANCE = "https://i.ibb.co/M5BrJCsv/Rz6-Nh-TQENLz97if-Gk-Fg-OYh-Pnq6-JQ4-SRVvaj-Iehk-Pu-GCVKqa-ME4e-UQx-DFfu-QAa9g-Ue6-S7-Ytoj2w67-DUk-Rt-Ir-Z.jpg"
IMG_WIN_150 = "https://i.ibb.co/Hjtkyfm/t6wq-NR9-tl-OCHm-S05jz-WUy-NMUENTz-Tp14h5x8-bd4q-Dy-CDI-I6kn-RQFMr-Fhs-BMmm-YUB0-Jf-Uq7746-UDb-RILPgp.jpg"
IMG_LOSE = "https://i.ibb.co/bjWTr3RN/JImh3-Aofv-Nh-VWb9-BQk6cc-G5xsc5j-OSX53q-Gzzot-RLhu-X2np-Kb-H3ou-Osq2-JA3xy7-Tj9-GBo7-7m-Fsax6ozsar8cfwl.jpg"
IMG_WIN_75 = "https://i.ibb.co/j09Q7Vj/z-Xrq-Mj-LDs-Fwqv-K8o8-Sne-WOpt-Ci-BSK4-DP-UJo-JNr-PZaqd-Eq-ZBNNo298-ZDDCOIwsf-A0-VCv-Yg5o-CApsb-F2-C7-Bf.jpg"
IMG_REFUND = "https://i.ibb.co/234bqhQY/D1d-Sz0-Rtumy-Z4-6-XD8ve72-B4-Jb-Gg-SOX-t-OCCoh-FUo-ZIFi7-WXQv-Zi-Jyf8j-Cc3-GUNI-IEriu7-HZ4y-Nmlhaw6xca-XG9.jpg"
IMG_JACKPOT = "https://i.ibb.co/MdNkYLC/d-Dahz-X8ztpg-OCBVb-pt-P4-XNrxk-Oz-Zpu7-KG8-JMQk-Ozl-SKXM3-T31qti-I5-Dc-Zf-Zx4xx-Wvc-Vaa-DKCKp-3388z-Bx-L.jpg"
# =================================

bot = Bot(token=TOKEN)

# --- БАЗА ДАННЫХ ---
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

# ========== КОМАНДЫ ДЛЯ ИГРОКОВ ==========
@bot.on.message(text=("!старт", "!start"))
async def start_handler(message: Message):
    user_id = message.peer_id
    register_user(user_id)
    await message.answer(
        "🔥 **Добро пожаловать в игру!**\n\n"
        "Твой стартовый баланс: **20 Пламени**.\n\n"
        "📌 **Команды:**\n"
        "`!баланс` — проверить Пламя\n"
        "`!рулетка <ставка>` — сыграть (шансы как в казино)\n"
        "`!шансы` — узнать вероятности\n"
        "`!топ` — топ игроков\n"
        "`!команды` — список всех команд\n\n"
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
        "💥 **Крупный проигрыш (0%)** — 45%\n"
        "😐 **Возврат 50%** — 20%\n"
        "🎉 **Выигрыш 75%** — 20%\n"
        "🔥 **Выигрыш 150%** — 10%\n"
        "🐉 **ДЖЕКПОТ 300%** — 5%\n\n"
        "Удачи! 🍀"
    )

@bot.on.message(text="!топ")
async def top_handler(message: Message):
    user_id = message.peer_id
    register_user(user_id)
    
    conn = sqlite3.connect("flame.db")
    c = conn.cursor()
    c.execute("SELECT id, flame FROM users ORDER BY flame DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        await message.answer("📊 Пока нет участников. Напиши !старт, чтобы начать!")
        return
    
    top_text = "🏆 **ТОП ИГРОКОВ ПО ПЛАМЕНИ** 🏆\n\n"
    for i, (uid, flame) in enumerate(rows, 1):
        top_text += f"{i}. [id{uid}|] — **{flame}** 🔥\n"
    
    await message.answer(top_text)

@bot.on.message(text=("!команды", "!help"))
async def commands_handler(message: Message):
    await message.answer(
        "📜 **СПИСОК КОМАНД** 📜\n\n"
        "👤 **Для всех игроков:**\n"
        "`!старт` — регистрация и стартовый баланс 20 Пламени\n"
        "`!баланс` — показать своё Пламя\n"
        "`!рулетка <ставка>` — сыграть в рулетку (шансы как в казино)\n"
        "`!шансы` — показать вероятности выигрыша\n"
        "`!топ` — рейтинг игроков по Пламени\n"
        "`!команды` или `!help` — показать этот список\n\n"
        "👑 **Для администраторов:**\n"
        "• `!редакт @ник +15` — добавить Пламя (по упоминанию)\n"
        "• **Ответь на сообщение игрока и напиши:** `+10`, `-5` или `=50`\n\n"
        "🐉 **Удачи в игре!**"
    )

@bot.on.message(text=("!рулетка <bet>", "!рулетка"))
async def roulette_handler(message: Message):
    user_id = message.peer_id
    register_user(user_id)

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ Напиши: `!рулетка 10`")
        return

    bet = int(args[1])
    current_flame = get_user(user_id)[0]

    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше 0")
        return
    if bet > current_flame:
        await message.answer(f"❌ У тебя только {current_flame} Пламени. Не хватает.")
        return
    if not can_bet(user_id):
        await message.answer(f"⏳ Подожди {COOLDOWN_SECONDS} секунд до следующей ставки.")
        return

    rand = random.random()
    
    if rand < 0.45:
        update_flame(user_id, -bet)
        new_flame = current_flame - bet
        result_text = f"💥 **КРУПНЫЙ ПРОИГРЫШ!**\n\nТы потерял **{bet}** Пламени.\n🎰 Удача не на твоей стороне..."
        attachment = IMG_LOSE
    elif rand < 0.65:
        refund = int(bet * 0.5)
        update_flame(user_id, -bet + refund)
        new_flame = current_flame - bet + refund
        result_text = f"😐 **ШЬЮТ...**\n\nТы вернул {refund} Пламени (50% ставки).\n🎲 Почти, но не сегодня."
        attachment = IMG_REFUND
    elif rand < 0.85:
        win_amount = int(bet * 0.75)
        update_flame(user_id, win_amount)
        new_flame = current_flame + win_amount
        result_text = f"🎉 **МАЛЕНЬКИЙ ВЫИГРЫШ!**\n\nТы выиграл +{win_amount} Пламени!\n✨ Неплохо, но можно больше."
        attachment = IMG_WIN_75
    elif rand < 0.95:
        win_amount = int(bet * 1.5)
        update_flame(user_id, win_amount)
        new_flame = current_flame + win_amount
        result_text = f"🔥 **СРЕДНИЙ ВЫИГРЫШ!**\n\nТы выиграл +{win_amount} Пламени (x1.5)!\n🎰 Дракон замечает тебя."
        attachment = IMG_WIN_150
    else:
        win_amount = int(bet * 3)
        update_flame(user_id, win_amount)
        new_flame = current_flame + win_amount
        result_text = f"🐉 **ДЖЕКПОТ! ДРАКОН НАГРАЖДАЕТ!**\n\nТы выиграл +{win_amount} Пламени (x3)!\n🔥🔥🔥 ТЫ В ФАВОРЕ У ДРАКОНА!"
        attachment = IMG_JACKPOT
    
    await message.answer(
        f"{result_text}\n\n🔥 **Теперь у тебя {new_flame} Пламени.**",
        attachment=attachment
    )
    set_last_bet_time(user_id)

# ========== АДМИН-КОМАНДЫ ==========
# 1. Старая команда (по упоминанию)
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

# 2. Новая команда (ответь на сообщение и напиши +10, -5 или =50)
@bot.on.message(text=("+<amount>", "-<amount>", "=<amount>"))
async def quick_edit_handler(message: Message):
    if not is_admin(message.from_id):
        await message.answer("❌ Только администратор может менять баланс.")
        return

    if not message.reply_message:
        await message.answer("❌ **Как использовать:** Ответь на сообщение игрока, а потом напиши +10, -5 или =50")
        return

    target_id = message.reply_message.from_id
    raw_amount = message.text.strip()

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
            await message.answer("❌ Используй +10, -5 или =50")
    except ValueError:
        await message.answer("❌ Сумма должна быть целым числом.")

# --- ЗАПУСК ---
if __name__ == "__main__":
    init_db()
    print("🔥 Бот 'Пламенная рулетка' успешно запущен!")
    print(f"✅ Администраторы: {ADMIN_IDS}")
    bot.run_forever()
