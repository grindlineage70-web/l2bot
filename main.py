import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

TOKEN = "8931279643:AAEfFxtfC-Jun48iZ0pje2YctIEjmkzryEY"

def init_db():
    conn = sqlite3.connect("l2_game.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            class_name TEXT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            adena INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()
router = Router()

class Registration(StatesGroup):
    waiting_for_class = State()

def get_classes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Воїн (Gladiator)", callback_data="class_warrior")],
        [InlineKeyboardButton(text="🔮 Маг (Archmage)", callback_data="class_mage")],
        [InlineKeyboardButton(text="🏹 Лучник (Moonlight)", callback_data="class_archer")]
    ])

def get_game_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Фарм (Catacombs)", callback_data="action_farm")],
        [InlineKeyboardButton(text="📊 Персонаж", callback_data="action_profile")]
    ])

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    conn = sqlite3.connect("l2_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        await message.answer("Ласкаво просимо в **L2 Interlude**!", reply_markup=get_game_menu_kb(), parse_mode="Markdown")
    else:
        await message.answer("Обери свій початковий клас:", reply_markup=get_classes_kb())
        await state.set_state(Registration.waiting_for_class)

@router.callback_query(Registration.waiting_for_class, F.data.startswith("class_"))
async def process_class_choice(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Warrior"
    class_map = {"class_warrior": "Воїн", "class_mage": "Маг", "class_archer": "Лучник"}
    chosen_class = class_map.get(callback.data, "Воїн")

    conn = sqlite3.connect("l2_game.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, 1, 0, 100)", (user_id, username, chosen_class))
    conn.commit()
    conn.close()

    await state.clear()
    await callback.message.edit_text(f"✅ Клас обрано: **{chosen_class}**!\nСтарт: 100 Адени.", reply_markup=get_game_menu_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "action_profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("l2_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT class_name, level, exp, adena FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        class_name, level, exp, adena = user
        await callback.message.edit_text(f"🛡 **Профіль**\n👤 Клас: {class_name}\n📈 Рівень: {level}\n✨ Досвід: {exp}\n💰 Адена: {adena}", reply_markup=get_game_menu_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "action_farm")
async def action_farm(callback: CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("l2_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT level, exp, adena FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user: return

    level, exp, adena = user
    exp += 35
    adena += 150
    cursor.execute("UPDATE users SET level = ?, exp = ?, adena = ? WHERE user_id = ?", (level, exp, adena, user_id))
    conn.commit()
    conn.close()

    await callback.message.edit_text(f"⚔️ Ви пофармили в катакомбах!\n+35 EXP\n+150 Adena 💰", reply_markup=get_game_menu_kb(), parse_mode="Markdown")

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
