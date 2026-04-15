

import asyncio
import uuid

from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================== CONFIG ==================
import os

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 5166861495

USTALAR = [
    7092355120,
]

# ================== INIT ==================
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

buyurtmalar = {}

# ================== HELPER ==================
def user_info(user):
    if user.username:
        return f"@{user.username}"
    else:
        return f'<a href="tg://user?id={user.id}">{user.full_name}</a>'

async def get_user_photo(user_id):
    photos = await bot.get_user_profile_photos(user_id)
    if photos.total_count > 0:
        return photos.photos[0][-1].file_id
    return None

# ================== STATE ==================
class Buyurtma(StatesGroup):
    muammo = State()
    manzil = State()
    telefon = State()

# ================== MENU ==================
menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔧 Usta chaqirish")]],
    resize_keyboard=True
)

# ================== START ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🔌 Elektr muammo bormi?\n\n👇 Tugmani bosing",
        reply_markup=menu
    )

# ================== BUYURTMA ==================
@dp.message(lambda msg: msg.text == "🔧 Usta chaqirish")
async def start_buyurtma(message: types.Message, state: FSMContext):
    await message.answer("🔧 Muammo turini yozing:")
    await state.set_state(Buyurtma.muammo)

@dp.message(Buyurtma.muammo)
async def get_muammo(message: types.Message, state: FSMContext):
    await state.update_data(muammo=message.text)
    await message.answer("📍 Manzilingizni yozing:")
    await state.set_state(Buyurtma.manzil)

@dp.message(Buyurtma.manzil)
async def get_manzil(message: types.Message, state: FSMContext):
    await state.update_data(manzil=message.text)
    await message.answer("📞 Telefon raqamingizni yozing:")
    await state.set_state(Buyurtma.telefon)

@dp.message(Buyurtma.telefon)
async def get_telefon(message: types.Message, state: FSMContext):
    data = await state.get_data()

    buyurtma_id = str(uuid.uuid4())[:8]

    text = f"""
📥 BUYURTMA #{buyurtma_id}

🔧 {data['muammo']}
📍 {data['manzil']}
📞 {message.text}
"""

    # saqlash
    buyurtmalar[buyurtma_id] = {
        "olindi": False,
        "user_id": message.from_user.id,
        "telefon": message.text,
        "muammo": data['muammo'],
        "manzil": data['manzil']
    }

    btn = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Olaman",
                callback_data=f"olaman_{buyurtma_id}"
            )
        ]]
    )

    # ustalarga yuborish
    for usta_id in USTALAR:
        await bot.send_message(usta_id, text, reply_markup=btn)

    # admin
    await bot.send_message(ADMIN_ID, text)

    await message.answer("✅ Buyurtma qabul qilindi!")
    await state.clear()

# ================== USTA QABUL ==================
@dp.callback_query(lambda c: c.data.startswith("olaman_"))
async def usta_qabul(callback: types.CallbackQuery):
    buyurtma_id = callback.data.split("_")[1]
    buyurtma = buyurtmalar.get(buyurtma_id)

    if not buyurtma:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return

    if buyurtma["olindi"]:
        await callback.answer("❌ Allaqachon olingan", show_alert=True)
        return

    # LOCK
    buyurtma["olindi"] = True
    buyurtma["usta_id"] = callback.from_user.id

    await callback.message.answer("✅ Siz buyurtmani oldingiz!")

    # usta info
    usta = user_info(callback.from_user)
    usta_id = callback.from_user.id

    # profil rasmi
    photo = await get_user_photo(usta_id)

    # ustaga info
    await bot.send_message(
        usta_id,
        f"""
📞 Mijoz: {buyurtma['telefon']}
📍 {buyurtma['manzil']}
🔧 {buyurtma['muammo']}
"""
    )

    # userga yuborish (rasm bilan)
    if photo:
        await bot.send_photo(
            buyurtma["user_id"],
            photo,
            caption=f"""
🧑‍🔧 Usta topildi!

👤 Usta: {usta}

📞 Tez orada siz bilan bog‘lanadi
""",
            parse_mode="HTML"
        )
    else:
        await bot.send_message(
            buyurtma["user_id"],
            f"""
🧑‍🔧 Usta topildi!

👤 Usta: {usta}

📞 Tez orada siz bilan bog‘lanadi
""",
            parse_mode="HTML"
        )

    # admin
    await bot.send_message(
        ADMIN_ID,
        f"""
🧑‍🔧 <b>OLINDI</b>

👤 Usta: {usta}
📦 #{buyurtma_id}
""",
        parse_mode="HTML"
    )

    await callback.answer()

# ================== RUN ==================
async def main():
    print("Bot ishga tushdi 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
