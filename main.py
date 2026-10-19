import asyncio
import sqlite3
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

TOKEN = "8931279643:AAEfFxtfC-Jun48iZ0pje2YctIEjmkzryEY"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect("l2_game.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            race TEXT DEFAULT 'Human',
            p_class TEXT DEFAULT 'Warrior',
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 150,
            max_hp INTEGER DEFAULT 150,
            mp INTEGER DEFAULT 80,
            max_mp INTEGER DEFAULT 80,
            p_atk INTEGER DEFAULT 30,
            m_atk INTEGER DEFAULT 15,
            p_def INTEGER DEFAULT 15,
            m_def INTEGER DEFAULT 15,
            adena INTEGER DEFAULT 1000,
            donate_coins INTEGER DEFAULT 10,
            weapon TEXT DEFAULT 'No-Grade Sword',
            armor TEXT DEFAULT 'No-Grade Tunic'
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_player(user_id):
    conn = sqlite3.connect("l2_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def register_player(user_id, username, race, p_class):
    conn = sqlite3.connect("l2_game.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO players 
        (user_id, username, race, p_class, level, exp, hp, max_hp, mp, max_mp, p_atk, m_atk, p_def, m_def, adena, donate_coins)
        VALUES (?, ?, ?, ?, 1, 0, 200, 200, 100, 100, 40, 20, 20, 20, 5000, 10)
    """, (user_id, username, race, p_class))
    conn.commit()
    conn.close()

def update_player(user_id, **kwargs):
    conn = sqlite3.connect("l2_game.db")
    cursor = conn.cursor()
    set_query = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    cursor.execute(f"UPDATE players SET {set_query} WHERE user_id = ?", values)
    conn.commit()
    conn.close()

# --- КЛАВІАТУРИ ---
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚔️ Фарм Локації"), KeyboardButton(text="👑 Епічні Боси")],
            [KeyboardButton(text="👤 Профіль"), KeyboardButton(text="🛒 Магазин (Giran)")],
            [KeyboardButton(text="💎 Донат Шоп")]
        ],
        resize_keyboard=True
    )

# --- START ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    player = get_player(message.from_user.id)
    if player:
        await message.answer(
            f"⚔️ **Ласкаво просимо до Lineage 2 Interlude!**\n\n"
            f"Герой: **{player[1]}**\n"
            f"Раса: **{player[2]}** | Клас: **{player[3]}** ({player[4]} lvl)",
            reply_markup=main_kb(),
            parse_mode="Markdown"
        )
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👨 Human (Люди)", callback_data="race_Human")],
            [InlineKeyboardButton(text="🧝 Elf (Світлі Ельфи)", callback_data="race_Elf")],
            [InlineKeyboardButton(text="🧛 Dark Elf (Темні Ельфи)", callback_data="race_DarkElf")],
            [InlineKeyboardButton(text="👹 Orc (Орки)", callback_data="race_Orc")],
            [InlineKeyboardButton(text="🧔 Dwarf (Гноми)", callback_data="race_Dwarf")]
        ])
        await message.answer("👑 **Створіть вашого персонажа! Оберіть расу:**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("race_"))
async def process_race(call: CallbackQuery):
    race = call.data.split("_")[1]
    classes = {
        "Human": ["Human Warrior", "Human Mystic"],
        "Elf": ["Elven Fighter", "Elven Mystic"],
        "DarkElf": ["Dark Fighter", "Dark Mystic"],
        "Orc": ["Orc Fighter", "Orc Mystic"],
        "Dwarf": ["Dwarf Artisan", "Dwarf Spoiler"]
    }
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c, callback_data=f"class_{race}_{c}")] for c in classes.get(race, [])
    ])
    await call.message.edit_text(f"Раса: **{race}**. Тепер оберіть клас:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("class_"))
async def process_class(call: CallbackQuery):
    parts = call.data.split("_")
    race = parts[1]
    p_class = parts[2]
    
    register_player(call.from_user.id, call.from_user.first_name, race, p_class)
    await call.message.delete()
    await call.message.answer(
        f"🎉 **Персонажа створено!**\n"
        f"Раса: **{race}**\n"
        f"Клас: **{p_class}**\n"
        f"Бонус: 5,000 Adena & 10 CoL!",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

# --- ПРОФІЛЬ ---
@dp.message(F.text == "👤 Профіль")
async def profile_handler(message: Message):
    p = get_player(message.from_user.id)
    if not p:
        await cmd_start(message)
        return
    
    text = (
        f"🛡 **Профіль:** {p[1]}\n"
        f"🏰 Раса: **{p[2]}** | Клас: **{p[3]}**\n"
        f"⭐ Рівень: **{p[4]}** (EXP: {p[5]}/1000)\n"
        f"❤️ HP: {p[6]}/{p[7]} | 🔷 MP: {p[8]}/{p[9]}\n\n"
        f"⚔️ P.Atk: {p[10]} | 🔮 M.Atk: {p[11]}\n"
        f"🛡 P.Def: {p[12]} | 🔮 M.Def: {p[13]}\n\n"
        f"🗡 Зброя: **{p[16]}**\n"
        f"🛡 Броня: **{p[17]}**\n\n"
        f"💰 Adena: **{p[14]:,}**\n"
        f"💎 Donate Coins: **{p[15]}**"
    )
    await message.answer(text, parse_mode="Markdown")

# --- ЛОКАЦІЇ ТА ФАРМ ---
@dp.message(F.text == "⚔️ Фарм Локації")
async def farm_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌴 Talking Island (1-20 lvl)", callback_data="farm_1")],
        [InlineKeyboardButton(text="🏰 Dion Hills (20-40 lvl)", callback_data="farm_2")],
        [InlineKeyboardButton(text="💀 Catacombs (40-60 lvl)", callback_data="farm_3")],
        [InlineKeyboardButton(text="🏛 Imperial Tomb (75-80 lvl)", callback_data="farm_5")]
    ])
    await message.answer("🗺 **Оберіть локацію для фарму:**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("farm_"))
async def process_farm(call: CallbackQuery):
    loc_id = call.data.split("_")[1]
    p = get_player(call.from_user.id)
    if not p: return
    
    locations = {
        "1": ("Talking Island", 20, 100, 300),
        "2": ("Dion Hills", 50, 300, 800),
        "3": ("Catacombs", 100, 800, 2000),
        "5": ("Imperial Tomb", 250, 3000, 10000)
    }
    loc_name, exp_gain, min_a, max_a = locations[loc_id]
    
    adena_drop = random.randint(min_a, max_a)
    new_exp = p[5] + exp_gain
    new_level = p[4]
    
    if new_exp >= 1000:
        new_level += 1
        new_exp = 0
        await call.message.answer(f"🎉 **LEVEL UP! Ви досягли {new_level} рівня!**", parse_mode="Markdown")
        
    update_player(call.from_user.id, exp=new_exp, level=new_level, adena=p[14] + adena_drop)
    await call.answer(f"⚔️ {loc_name}!\n+ {exp_gain} EXP\n+ {adena_drop:,} Adena", show_alert=True)

# --- БОСИ ---
@dp.message(F.text == "👑 Епічні Боси")
async def epic_bosses(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕷 Queen Ant", callback_data="boss_QA")],
        [InlineKeyboardButton(text="⚔️ Zaken", callback_data="boss_Zaken")],
        [InlineKeyboardButton(text="🔥 Valakas", callback_data="boss_Valakas")]
    ])
    await message.answer("👑 **Оберіть Епічного Боса:**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("boss_"))
async def attack_boss(call: CallbackQuery):
    boss = call.data.split("_")[1]
    p = get_player(call.from_user.id)
    
    if random.randint(1, 100) > 30:
        reward_col = random.randint(1, 5)
        reward_adena = random.randint(50000, 200000)
        update_player(call.from_user.id, adena=p[14] + reward_adena, donate_coins=p[15] + reward_col)
        await call.message.answer(f"🏆 **Перемога над {boss}!**\nДроп: **{reward_adena:,} Adena** та **{reward_col} CoL**!", parse_mode="Markdown")
    else:
        await call.message.answer(f"💀 **{boss} виявився сильнішим!** Спробуйте ще раз.", parse_mode="Markdown")
    await call.answer()

# --- МАГАЗИН ---
@dp.message(F.text == "🛒 Магазин (Giran)")
async def shop_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗡 C-Grade Weapon (50,000 Adena)", callback_data="buy_c_wpn")],
        [InlineKeyboardButton(text="⚔️ S-Grade Weapon (2,000,000 Adena)", callback_data="buy_s_wpn")]
    ])
    await message.answer("🏰 **Ласкаво просимо в Магазин Гірану!**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(call: CallbackQuery):
    item = call.data.replace("buy_", "")
    p = get_player(call.from_user.id)
    
    prices = {"c_wpn": 50000, "s_wpn": 2000000}
    names = {"c_wpn": "Homunkulus's Sword", "s_wpn": "Angel Slayer"}
    
    cost = prices.get(item, 0)
    if p[14] < cost:
        await call.answer("❌ Недостатньо Адени!", show_alert=True)
        return
        
    update_player(call.from_user.id, adena=p[14] - cost, weapon=names.get(item), p_atk=p[10] + 150)
    await call.message.answer(f"✅ Ви успішно купили **{names.get(item)}**!", parse_mode="Markdown")
    await call.answer()

# --- ДОНАТ ---
@dp.message(F.text == "💎 Донат Шоп")
async def donate_shop(message: Message):
    await message.answer("💎 **Донат Магазин**\nДонат монети (CoL) вибиваються з епічних босів!", parse_mode="Markdown")

# --- ЗАПУСК ---
async def main():
    print("Бот запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
