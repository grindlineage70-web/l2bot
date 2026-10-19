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
    conn = sqlite3.connect("l2_adeos.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            race TEXT DEFAULT 'Human',
            p_class TEXT DEFAULT 'Fighter',
            prof_stage INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 200,
            max_hp INTEGER DEFAULT 200,
            mp INTEGER DEFAULT 100,
            max_mp INTEGER DEFAULT 100,
            p_atk INTEGER DEFAULT 50,
            m_atk INTEGER DEFAULT 20,
            p_def INTEGER DEFAULT 30,
            m_def INTEGER DEFAULT 20,
            adena INTEGER DEFAULT 10000,
            donate_coins INTEGER DEFAULT 10,
            weapon TEXT DEFAULT 'Short Sword',
            weapon_enchant INTEGER DEFAULT 0,
            armor TEXT DEFAULT 'Wooden Set',
            soulshots INTEGER DEFAULT 100,
            iron_ore INTEGER DEFAULT 0,
            varnish INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_player(user_id):
    conn = sqlite3.connect("l2_adeos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def register_player(user_id, username, race, p_class):
    conn = sqlite3.connect("l2_adeos.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO players 
        (user_id, username, race, p_class, level, exp, hp, max_hp, mp, max_mp, p_atk, m_atk, p_def, m_def, adena, donate_coins)
        VALUES (?, ?, ?, ?, 1, 0, 250, 250, 120, 120, 60, 30, 40, 30, 15000, 10)
    """, (user_id, username, race, p_class))
    conn.commit()
    conn.close()

def update_player(user_id, **kwargs):
    conn = sqlite3.connect("l2_adeos.db")
    cursor = conn.cursor()
    set_query = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    cursor.execute(f"UPDATE players SET {set_query} WHERE user_id = ?", values)
    conn.commit()
    conn.close()

# --- ГОЛОВНЕ МЕНЮ ---
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚔️ Фарм & Спойл"), KeyboardButton(text="✨ Заточка (+1..16)")],
            [KeyboardButton(text="📜 Професії & Квести"), KeyboardButton(text="🛠 Крафт & Соски")],
            [KeyboardButton(text="🏟 PvP Арена"), KeyboardButton(text="👤 Профіль")]
        ],
        resize_keyboard=True
    )

# --- START ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    player = get_player(message.from_user.id)
    if player:
        await message.answer_photo(
            photo="https://images.wallpapersden.com/image/download/lineage-2-interlude_bGptbm6UmZqaraWkpJRmZmdlrWJnZWU.jpg",
            caption=f"⚔️ **Adeos Mobile Lineage 2**\nВітаємо, **{player[1]}**!\nКлас: **{player[3]}** | Рівень: **{player[5]}**",
            reply_markup=main_kb(),
            parse_mode="Markdown"
        )
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👨 Human", callback_data="race_Human"), InlineKeyboardButton(text="🧝 Elf", callback_data="race_Elf")],
            [InlineKeyboardButton(text="🧛 Dark Elf", callback_data="race_DarkElf"), InlineKeyboardButton(text="👹 Orc", callback_data="race_Orc")],
            [InlineKeyboardButton(text="🧔 Dwarf", callback_data="race_Dwarf")]
        ])
        await message.answer_photo(
            photo="https://images.wallpapersden.com/image/download/lineage-2-interlude_bGptbm6UmZqaraWkpJRmZmdlrWJnZWU.jpg",
            caption="👑 **Створення персонажа в Adeos L2:**\nОберіть расу вашого героя:",
            reply_markup=kb,
            parse_mode="Markdown"
        )

@dp.callback_query(F.data.startswith("race_"))
async def process_race(call: CallbackQuery):
    race = call.data.split("_")[1]
    classes = {
        "Human": ["Human Fighter", "Human Mystic"],
        "Elf": ["Elven Fighter", "Elven Mystic"],
        "DarkElf": ["Dark Fighter", "Dark Mystic"],
        "Orc": ["Orc Fighter", "Orc Mystic"],
        "Dwarf": ["Dwarf Fighter"]
    }
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c, callback_data=f"class_{race}_{c}")] for c in classes.get(race, [])
    ])
    await call.message.edit_caption(caption=f"Раса: **{race}**. Оберіть початковий фах:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("class_"))
async def process_class(call: CallbackQuery):
    parts = call.data.split("_")
    race, p_class = parts[1], parts[2]
    register_player(call.from_user.id, call.from_user.first_name, race, p_class)
    await call.message.delete()
    await call.message.answer_photo(
        photo="https://images.wallpapersden.com/image/download/lineage-2-interlude_bGptbm6UmZqaraWkpJRmZmdlrWJnZWU.jpg",
        caption=f"🎉 **Персонажа створено!**\nРаса: **{race}**\nКлас: **{p_class}**\nСтартовий бонус: 15,000 Adena & 100 Soulshots!",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

# --- 1. ФАРМ ТА СПОЙЛ ---
@dp.message(F.text == "⚔️ Фарм & Спойл")
async def farm_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌾 Gludin Outskirts (1-20)", callback_data="farm_1")],
        [InlineKeyboardButton(text="💀 Death Pass (20-40)", callback_data="farm_2")],
        [InlineKeyboardButton(text="🔥 Dragon Valley (40-76)", callback_data="farm_3")]
    ])
    await message.answer_photo(
        photo="https://wallpapercave.com/wp/wp1946059.jpg",
        caption="⚔️ **Локації Фарму & Спойлу Adeos:**\nОбирайте зону по своєму рівню:",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("farm_"))
async def process_farm(call: CallbackQuery):
    loc_id = call.data.split("_")[1]
    p = get_player(call.from_user.id)
    if not p: return

    shots = p[20]
    bonus_dmg = 1.5 if shots > 0 else 1.0
    if shots > 0:
        update_player(call.from_user.id, soulshots=shots - 1)

    exp_g = int(30 * int(loc_id) * bonus_dmg)
    adena_g = random.randint(500 * int(loc_id), 2000 * int(loc_id))
    iron_g = random.randint(1, 3) if random.random() < 0.6 else 0
    varnish_g = random.randint(1, 2) if random.random() < 0.4 else 0

    new_exp = p[6] + exp_g
    new_lvl = p[5]
    if new_exp >= 1000:
        new_lvl += 1
        new_exp = 0
        await call.message.answer(f"🎉 **LEVEL UP! Ваш рівень піднявся до {new_lvl}!**")

    update_player(
        call.from_user.id, 
        exp=new_exp, 
        level=new_lvl, 
        adena=p[15] + adena_g, 
        iron_ore=p[21] + iron_g, 
        varnish=p[22] + varnish_g
    )

    shot_text = "⚡ *(Використано Soulshot x1)*" if shots > 0 else "⚠️ *(Без сосок)*"
    spoil_text = f"\n📦 Спойл: +{iron_g} Iron Ore, +{varnish_g} Varnish" if (iron_g or varnish_g) else ""
    await call.answer(f"⚔️ Пофармили! {shot_text}\n+ {exp_g} EXP | + {adena_g:,} Adena{spoil_text}", show_alert=True)

# --- 2. ЗАТОЧКА СУВОРКА (+1..+16) ---
@dp.message(F.text == "✨ Заточка (+1..16)")
async def enchant_menu(message: Message):
    p = get_player(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Заточити Weapon Scroll (10,000 Adena)", callback_data="enchant_wpn")]
    ])
    await message.answer_photo(
        photo="https://i.ytimg.com/vi/3yS6X8V9Svw/maxresdefault.jpg",
        caption=(
            f"✨ **Заточка Зброї Adeos:**\n"
            f"Поточна зброя: **{p[17]} (+{p[18]})**\n"
            f"Атака (P.Atk): **{p[11]}**\n\n"
            f"⚠️ *Шанс заточки: +1..+3 (100%), далі — 66%. При фейлі заточка скидається до +0!*"
        ),
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "enchant_wpn")
async def process_enchant(call: CallbackQuery):
    p = get_player(call.from_user.id)
    if p[15] < 10000:
        await call.answer("❌ Недостатньо Адени (потрібно 10,000 Adena)!", show_alert=True)
        return

    cur_enc = p[18]
    if cur_enc >= 16:
        await call.answer("👑 Ваша зброя вже максимально заточена (+16)!", show_alert=True)
        return

    chance = 1.0 if cur_enc < 3 else 0.66
    if random.random() <= chance:
        new_enc = cur_enc + 1
        new_atk = p[11] + 25
        update_player(call.from_user.id, adena=p[15] - 10000, weapon_enchant=new_enc, p_atk=new_atk)
        await call.message.answer(f"🎉 **УСПІХ!** Зброя заточена на **+{new_enc}**! P.Atk: {new_atk}")
    else:
        update_player(call.from_user.id, adena=p[15] - 10000, weapon_enchant=0, p_atk=p[11] - (cur_enc * 25))
        await call.message.answer(f"💥 **ФЕЙЛ!** Зброя зламалася і скинулася до **+0**!")
    await call.answer()

# --- 3. КРАФТ ТА СОСКИ ---
@dp.message(F.text == "🛠 Крафт & Соски")
async def craft_menu(message: Message):
    p = get_player(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Зкрафтити 100 Soulshots (5 Iron + 5 Varnish)", callback_data="craft_shots")],
        [InlineKeyboardButton(text="🗡 Зкрафтити Dual Swords (50 Iron + 50 Varnish)", callback_data="craft_duals")]
    ])
    await message.answer_photo(
        photo="https://wallpapercave.com/wp/wp3261763.jpg",
        caption=(
            f"🛠 **Кузня та Крафт Adeos:**\n"
            f"Ваші ресурси:\n"
            f"🪵 Iron Ore: **{p[21]}** шт.\n"
            f"🧪 Varnish: **{p[22]}** шт.\n"
            f"⚡ Soulshots: **{p[20]}** шт."
        ),
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("craft_"))
async def process_craft(call: CallbackQuery):
    item = call.data.split("_")[1]
    p = get_player(call.from_user.id)

    if item == "shots":
        if p[21] < 5 or p[22] < 5:
            await call.answer("❌ Недостатньо ресурсів для крафту сосок!", show_alert=True)
            return
        update_player(call.from_user.id, iron_ore=p[21] - 5, varnish=p[22] - 5, soulshots=p[20] + 100)
        await call.message.answer("⚡ **Успішний крафт!** Отримано **100 Soulshots**!")
    elif item == "duals":
        if p[21] < 50 or p[22] < 50:
            await call.answer("❌ Недостатньо ресурсів для Dual Swords!", show_alert=True)
            return
        update_player(call.from_user.id, iron_ore=p[21] - 50, varnish=p[22] - 50, weapon="Keshanberk*Keshanberk", p_atk=p[11] + 150)
        await call.message.answer("🗡 **Успішний крафт!** Створено **Dual Swords Keshanberk**!")
    await call.answer()

# --- 4. ПРОФЕСІЇ ТА КВЕСТИ ---
@dp.message(F.text == "📜 Професії & Квести")
async def quest_menu(message: Message):
    p = get_player(message.from_user.id)
    lvl = p[5]
    stage = p[4]

    text = f"📜 **Зміна Професії (Class Transfer):**\nВаш рівень: **{lvl}**\nПоточна профа: Stage **{stage}**\n\n"
    kb_list = []

    if lvl >= 20 and stage == 0:
        text += "✅ Вам доступна **1-ша Професія**!"
        kb_list.append([InlineKeyboardButton(text="🎓 Отримати 1-шу Профу", callback_data="prof_1")])
    elif lvl >= 40 and stage == 1:
        text += "✅ Вам доступна **2-га Професія**!"
        kb_list.append([InlineKeyboardButton(text="👑 Отримати 2-гу Профу", callback_data="prof_2")])
    elif lvl >= 76 and stage == 2:
        text += "✅ Вам доступна **3-тя Професія (Noblesse)**!"
        kb_list.append([InlineKeyboardButton(text="🔥 Отримати 3-тю Профу", callback_data="prof_3")])
    else:
        text += "⏳ Продовжуйте качати рівень, щоб відкрити наступну профу!"

    kb = InlineKeyboardMarkup(inline_keyboard=kb_list) if kb_list else None
    await message.answer_photo(
        photo="https://images.wallpapersden.com/image/download/lineage-2-interlude_bGptbm6UmZqaraWkpJRmZmdlrWJnZWU.jpg",
        caption=text,
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("prof_"))
async def process_prof(call: CallbackQuery):
    st = int(call.data.split("_")[1])
    p = get_player(call.from_user.id)

    prof_names = {1: "Knight / Wizard", 2: "Paladin / Sorcerer", 3: "Phoenix Knight / Archmage"}
    new_title = f"{p[3]} -> {prof_names.get(st, 'Hero')}"

    update_player(call.from_user.id, prof_stage=st, p_class=new_title, p_atk=p[11] + 100, m_atk=p[12] + 100)
    await call.message.answer(f"🎉 **ВІТАЄМО!** Ви змінили професію на **{new_title}**! Характеристики підвищено!")
    await call.answer()

# --- 5. PVP АРЕНА ---
@dp.message(F.text == "🏟 PvP Арена")
async def pvp_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Викликати Гладиатора (NPC)", callback_data="pvp_npc")],
        [InlineKeyboardButton(text="🏆 Великий Турнір Олімпіади", callback_data="pvp_olympiad")]
    ])
    await message.answer_photo(
        photo="https://wallpapercave.com/wp/wp1946075.jpg",
        caption="🏟 **Колізей та PvP Арена Adeos:**\nЗмагайтеся за звання Героя та очки слави!",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("pvp_"))
async def process_pvp(call: CallbackQuery):
    p = get_player(call.from_user.id)
    if random.random() < 0.55:
        reward = random.randint(10000, 50000)
        update_player(call.from_user.id, adena=p[15] + reward)
        await call.message.answer(f"⚔️ **ПЕРЕМОГА НА АРЕНІ!** Ви здолали суперника та забрали **{reward:,} Adena**!")
    else:
        await call.message.answer("💀 **ПОРАЗКА!** Суперник виявився спритнішим. Підкачайте шмот та заточку!")
    await call.answer()

# --- ПРОФІЛЬ ---
@dp.message(F.text == "👤 Профіль")
async def profile_handler(message: Message):
    p = get_player(message.from_user.id)
    if not p: return

    enc_str = f" (+{p[18]})" if p[18] > 0 else ""
    text = (
        f"🛡 **Профіль:** {p[1]}\n"
        f"🏰 Раса: **{p[2]}** | Профа Stage: **{p[4]}**\n"
        f"⚔️ Клас: **{p[3]}**\n"
        f"⭐ Рівень: **{p[5]}** (EXP: {p[6]}/1000)\n\n"
        f"🗡 Зброя: **{p[17]}{enc_str}**\n"
        f"⚔️ P.Atk: **{p[11]}** | 🔮 M.Atk: **{p[12]}**\n"
        f"🛡 P.Def: **{p[13]}** | 🔮 M.Def: **{p[14]}**\n\n"
        f"⚡ Soulshots: **{p[20]}** шт.\n"
        f"🪵 Iron Ore: **{p[21]}** | 🧪 Varnish: **{p[22]}**\n"
        f"💰 Adena: **{p[15]:,}**"
    )
    await message.answer_photo(
        photo="https://wallpapercave.com/wp/wp1946059.jpg",
        caption=text,
        parse_mode="Markdown"
    )

async def main():
    print("🚀 Adeos Lineage 2 Bot Запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
