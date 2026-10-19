import asyncio
import sqlite3
import random
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8931279643:AAEfFxtfC-Jun48iZ0pje2YctIEjmkzryEY"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# --- БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect("l2_interlude.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            race TEXT,
            p_class TEXT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            mp INTEGER DEFAULT 50,
            max_mp INTEGER DEFAULT 50,
            p_atk INTEGER DEFAULT 15,
            m_atk INTEGER DEFAULT 15,
            p_def INTEGER DEFAULT 10,
            m_def INTEGER DEFAULT 10,
            adena INTEGER DEFAULT 500,
            donate_coins INTEGER DEFAULT 0,
            weapon TEXT DEFAULT 'None',
            armor TEXT DEFAULT 'None',
            is_premium INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_player(user_id):
    conn = sqlite3.connect("l2_interlude.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def register_player(user_id, username, race, p_class):
    conn = sqlite3.connect("l2_interlude.db")
    cursor = conn.cursor()
    # Базові характеристики за класами
    p_atk = 30 if "Knight" in p_class or "Warrior" in p_class or "Orc" in race else 15
    m_atk = 35 if "Mage" in p_class or "Mystic" in p_class else 10
    
    cursor.execute("""
        INSERT OR REPLACE INTO players 
        (user_id, username, race, p_class, level, exp, hp, max_hp, mp, max_mp, p_atk, m_atk, p_def, m_def, adena, donate_coins)
        VALUES (?, ?, ?, ?, 1, 0, 150, 150, 80, 80, ?, ?, 15, 15, 1000, 10)
    """, (user_id, username, race, p_class, p_atk, m_atk))
    conn.commit()
    conn.close()

def update_player(user_id, **kwargs):
    conn = sqlite3.connect("l2_interlude.db")
    cursor = conn.cursor()
    set_query = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    cursor.execute(f"UPDATE players SET {set_query} WHERE user_id = ?", values)
    conn.commit()
    conn.close()

# --- СТАНЫ FSM ---
class Registration(StatesGroup):
    race = State()
    p_class = State()

# --- КЛАВІАТУРИ ---
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚔️ Фарм Локації"), KeyboardButton(text="👑 Епічні Боси")],
            [KeyboardButton(text="👤 Профіль"), KeyboardButton(text="🎒 Інвентар")],
            [KeyboardButton(text="🛒 Магазин (Giran)"), KeyboardButton(text="💎 Донат Шоп")]
        ],
        resize_keyboard=True
    )

# --- START / РЕЄСТРАЦІЯ ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    player = get_player(message.from_user.id)
    if player:
        await message.answer_photo(
            photo="https://i.ibb.co/3sSfZ4M/l2-main.jpg",
            caption=f"⚔️ **Ласкаво просимо до Lineage 2 Interlude!**\nВаш герой: **{player[3]}** ({player[4]} lvl)",
            reply_markup=main_kb()
        )
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👨 Human (Люди)", callback_data="race_Human")],
            [InlineKeyboardButton(text="🧝 Elf (Світлі Ельфи)", callback_data="race_Elf")],
            [InlineKeyboardButton(text="🧛 Dark Elf (Темні Ельфи)", callback_data="race_DarkElf")],
            [InlineKeyboardButton(text="👹 Orc (Орки)", callback_data="race_Orc")],
            [InlineKeyboardButton(text="🧔 Dwarf (Гноми)", callback_data="race_Dwarf")]
        ])
        await message.answer("👑 **Створіть вашого персонажа! Оберіть расу:**", reply_markup=kb)
        await state.set_state(Registration.race)

@router.callback_query(F.data.startswith("race_"), Registration.race)
async def process_race(call: CallbackQuery, state: FSMContext):
    race = call.data.split("_")[1]
    await state.update_data(race=race)
    
    classes = {
        "Human": ["Human Warrior", "Human Mystic"],
        "Elf": ["Elven Fighter", "Elven Mystic"],
        "DarkElf": ["Dark Fighter", "Dark Mystic"],
        "Orc": ["Orc Fighter", "Orc Mystic"],
        "Dwarf": ["Dwarf Artisan", "Dwarf Spoiler"]
    }
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c, callback_data=f"class_{c}")] for c in classes.get(race, [])
    ])
    await call.message.edit_text(f"Ви обрали расу: **{race}**. Тепер оберіть стартовий клас:", reply_markup=kb)
    await state.set_state(Registration.p_class)

@router.callback_query(F.data.startswith("class_"), Registration.p_class)
async def process_class(call: CallbackQuery, state: FSMContext):
    p_class = call.data.split("_")[1]
    data = await state.get_data()
    race = data["race"]
    
    register_player(call.from_user.id, call.from_user.first_name, race, p_class)
    await state.clear()
    
    await call.message.delete()
    await call.message.answer_photo(
        photo="https://i.ibb.co/3sSfZ4M/l2-main.jpg",
        caption=f"🎉 **Вітаємо! Персонаж створений!**\nРаса: **{race}**\nКлас: **{p_class}**\nОтримано: 1,000 Adena, 10 Donate Coins!",
        reply_markup=main_kb()
    )

# --- ПРОФІЛЬ ---
@router.message(F.text == "👤 Профіль")
async def profile_handler(message: Message):
    p = get_player(message.from_user.id)
    if not p: return
    
    hp_bar = "🟩" * int(p[6]/p[7] * 5) + "⬜" * (5 - int(p[6]/p[7] * 5))
    mp_bar = "🟦" * int(p[8]/p[9] * 5) + "⬜" * (5 - int(p[8]/p[9] * 5))
    
    text = (
        f"🛡 **Профіль Персонажа:** {p[1]}\n"
        f"🏰 Раса: **{p[2]}** | Клас: **{p[3]}**\n"
        f"⭐ Рівень: **{p[4]}** (EXP: {p[5]}/1000)\n"
        f"❤️ HP: {hp_bar} {p[6]}/{p[7]}\n"
        f"🔷 MP: {mp_bar} {p[8]}/{p[9]}\n\n"
        f"⚔️ P.Atk: {p[10]} | 🔮 M.Atk: {p[11]}\n"
        f"🛡 P.Def: {p[12]} | 🔮 M.Def: {p[13]}\n\n"
        f"🗡 Зброя: **{p[16]}**\n"
        f"🛡 Броня: **{p[17]}**\n\n"
        f"💰 Adena: **{p[14]:,}**\n"
        f"💎 Donate Coins: **{p[15]}**"
    )
    await message.answer(text, parse_mode="Markdown")

# --- ЛОКАЦІЇ ТА ФАРМ ---
@router.message(F.text == "⚔️ Фарм Локації")
async def farm_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌴 Talking Island (1-20 lvl)", callback_data="farm_1")],
        [InlineKeyboardButton(text="🏰 Dion Hills (20-40 lvl)", callback_data="farm_2")],
        [InlineKeyboardButton(text="💀 Catacombs (40-60 lvl)", callback_data="farm_3")],
        [InlineKeyboardButton(text="🔥 Valley of Saints (60-75 lvl)", callback_data="farm_4")],
        [InlineKeyboardButton(text="🏛 Imperial Tomb (75-80 lvl)", callback_data="farm_5")]
    ])
    await message.answer("🗺 **Оберіть локацію для фарму:**", reply_markup=kb)

@router.callback_query(F.data.startswith("farm_"))
async def process_farm(call: CallbackQuery):
    loc_id = call.data.split("_")[1]
    p = get_player(call.from_user.id)
    
    locations = {
        "1": ("Talking Island", 10, 50, 100),
        "2": ("Dion Hills", 25, 120, 300),
        "3": ("Catacombs", 50, 300, 800),
        "4": ("Valley of Saints", 100, 700, 2000),
        "5": ("Imperial Tomb", 200, 1500, 5000)
    }
    loc_name, exp_gain, min_adena, max_adena = locations[loc_id]
    
    adena_drop = random.randint(min_adena, max_adena)
    if p[18] == 1: adena_drop = int(adena_drop * 1.5) # Преміум бонус
    
    new_exp = p[5] + exp_gain
    new_level = p[4]
    if new_exp >= 1000:
        new_level += 1
        new_exp = 0
        await call.message.answer(f"🎉 **LEVEL UP! Ви досягли {new_level} рівня!**")
        
    update_player(call.from_user.id, exp=new_exp, level=new_level, adena=p[14] + adena_drop)
    
    await call.answer(f"⚔️ Пофармили в {loc_name}!\n+ {exp_gain} EXP\n+ {adena_drop} Adena", show_alert=True)

# --- ЕПІЧНІ БОСИ ---
@router.message(F.text == "👑 Епічні Боси")
async def epic_bosses(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕷 Queen Ant (40 lvl)", callback_data="boss_QA")],
        [InlineKeyboardButton(text="⚔️ Zaken (60 lvl)", callback_data="boss_Zaken")],
        [InlineKeyboardButton(text="🐉 Baium (75 lvl)", callback_data="boss_Baium")],
        [InlineKeyboardButton(text="🔥 Valakas (80 lvl)", callback_data="boss_Valakas")]
    ])
    await message.answer_photo(
        photo="https://i.ibb.co/C06Mpx7/valakas.jpg",
        caption="👑 **Епічні Боси Interlude!**\nЗберіться з силами, щоб отримати епічну біжутерію!",
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("boss_"))
async def attack_boss(call: CallbackQuery):
    boss = call.data.split("_")[1]
    p = get_player(call.from_user.id)
    
    if p[4] < 40:
        await call.answer("❌ Ваш рівень занадто низький для Босів! (Потрібен 40+ lvl)", show_alert=True)
        return
        
    chance = random.randint(1, 100)
    if chance > 40:
        reward_col = random.randint(1, 5)
        reward_adena = random.randint(50000, 200000)
        update_player(call.from_user.id, adena=p[14] + reward_adena, donate_coins=p[15] + reward_col)
        await call.message.answer(f"🏆 **Перемога над {boss}!**\nДроп: **{reward_adena:,} Adena** та **{reward_col} Donate Coins**!")
    else:
        await call.message.answer(f"💀 **{boss} розгромив вашу паті!** Спробуйте ще раз пізніше.")
    await call.answer()

# --- МАГАЗИН GIRAN ---
@router.message(F.text == "🛒 Магазин (Giran)")
async def shop_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗡 C-Grade Weapon (50,000 Adena)", callback_data="buy_c_wpn")],
        [InlineKeyboardButton(text="🛡 A-Grade Armor Set (500,000 Adena)", callback_data="buy_a_arm")],
        [InlineKeyboardButton(text="⚔️ S-Grade Weapon (2,000,000 Adena)", callback_data="buy_s_wpn")]
    ])
    await message.answer("🏰 **Ласкаво просимо в Магазин Гірану!**", reply_markup=kb)

@router.callback_query(F.data.startswith("buy_"))
async def process_buy(call: CallbackQuery):
    item = call.data.split("_")[1] + "_" + call.data.split("_")[2]
    p = get_player(call.from_user.id)
    
    prices = {"c_wpn": 50000, "a_arm": 500000, "s_wpn": 2000000}
    names = {"c_wpn": "Homunkulus's Sword", "a_arm": "Dark Crystal Set", "s_wpn": "Angel Slayer"}
    
    cost = prices.get(item, 0)
    if p[14] < cost:
        await call.answer("❌ У вас недостатньо Адени!", show_alert=True)
        return
        
    update_player(call.from_user.id, adena=p[14] - cost, weapon=names.get(item, p[16]), p_atk=p[10] + 100)
    await call.message.answer(f"✅ Ви успішно купили **{names.get(item)}**!")
    await call.answer()

# --- ДОНАТ ШОП ---
@router.message(F.text == "💎 Донат Шоп")
async def donate_shop(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Premium Account (10 CoL)", callback_data="buy_pa")],
        [InlineKeyboardButton(text="🗡 Valakas Dragon Slayer (50 CoL)", callback_data="buy_don_wpn")]
    ])
    await message.answer("💎 **Донат Магазин**\nВикористовуйте Donate Coins для підсилення:", reply_markup=kb)

@router.callback_query(F.data == "buy_pa")
async def buy_pa(call: CallbackQuery):
    p = get_player(call.from_user.id)
    if p[15] < 10:
        await call.answer("❌ Недостатньо Donate Coins!", show_alert=True)
        return
    update_player(call.from_user.id, donate_coins=p[15] - 10, is_premium=1)
    await call.message.answer("🎉 **Преміум-акаунт успішно активовано! (+50% до фарму)**")
    await call.answer()

# --- ЗАПУСК ---
async def main():
    print("🚀 Бот Lineage 2 Interlude успішно запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
