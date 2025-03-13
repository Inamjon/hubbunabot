import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import TOKEN
from database import *


bot = Bot(token=TOKEN)
dp = Dispatcher()


class UserState(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_region = State()
    waiting_for_age = State()
    waiting_for_phone_number = State()


async def check_subscription(user_id):
    """Foydalanuvchini barcha kanallarga a'zo ekanligini tekshirish"""
    CHANNELS = load_channels_from_db()  # Kanallarni har safar yangilash

    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False  # Agar a'zo bo'lmasa
        except Exception:
            return False  # Kanal mavjud bo'lmasa yoki xatolik bo‘lsa
    return True  # Agar barcha kanallarga a’zo bo‘lsa




@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # 🔹 **Foydalanuvchini bazadan tekshirish**
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        await message.answer("✅ Siz allaqachon ro‘yxatdan o‘tgansiz! Botdan foydalanishingiz mumkin.")
        return
    
    # 🔹 **Obunani tekshirish**
    is_subscribed = await check_subscription(user_id)

    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()

    # Malumotlarni olish
    cursor.execute("SELECT * FROM channels")  # "users" jadvalidagi barcha ma'lumotlar
    rows = cursor.fetchall()

    if not is_subscribed:

        global keyboard 
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📢 {channel.replace('@', '')}", url=f"https://t.me/{channel.replace('@', '')}")] for channel in rows
        ])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")])

        await message.answer("❌ Botdan foydalanish uchun quyidagi kanallarga a’zo bo‘lishingiz kerak:", reply_markup=keyboard)
        return

    await message.answer("Iltimos, ismingizni yozing:")
    await state.set_state(UserState.waiting_for_full_name)

@dp.message(Command("help"))
async def help_command(message: Message):

    text = ("📌 *Bot Yordam Bo‘limi*\n\n"
            "Botdan foydalanish uchun quyidagi qadamlarni bajaring👇\n"
            "1. Botdan foydalanish uchun /start bosib ro'yxatdan o'ting❗️\n"
            "2. Kanallarga a'zo bo'ling❗️\n"
            "3. Xabar yuboring va agar adminlar xabarni o'qisa sizga bu haqida aytiladi✅\n\n"
            "✅ *Mavjud buyruqlar:*\n"
            "/start - Botni ishga tushirish\n"
            "/help - Yordam olish\n\n" )

    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("info"))
async def info_command(message: Message):

    text = ("Bot dasturchisi: @inam0810")

    await message.answer(text, parse_mode="Markdown")

# 🔹 **Ism-familiyani qabul qilish**
@dp.message(UserState.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text #.strip()
    # if " " not in full_name:
    #     await message.answer("Iltimos, to‘liq ismingizni Ism Familiya shaklida kiriting!")
    #     return
    await state.update_data(full_name=full_name)

    regions = [
    "Toshkent shahri",
    "Toshkent viloyati",
    "Andijon viloyati",
    "Buxoro viloyati",
    "Farg‘ona viloyati",
    "Jizzax viloyati",
    "Xorazm viloyati",
    "Namangan viloyati",
    "Navoiy viloyati",
    "Qashqadaryo viloyati",
    "Samarqand viloyati",
    "Sirdaryo viloyati",
    "Surxondaryo viloyati",
    "Qoraqalpog‘iston Respublikasi"
]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=region, callback_data=f"region_{region}")] for region in regions])

    await message.answer("Qayerdansiz? Viloyatingizni tanlang:", reply_markup=keyboard)
    await state.set_state(UserState.waiting_for_region)

# 🔹 **Viloyat tanlanganda**
@dp.callback_query(F.data.startswith("region_"))
async def process_region(call: CallbackQuery, state: FSMContext):
    region = call.data.split("_")[1]
    await state.update_data(region=region)
    await call.message.answer("Tug'ilgan yilingizni kiriting:")
    await state.set_state(UserState.waiting_for_age)

# 🔹 **Yoshni qabul qilish**
@dp.message(UserState.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, Tug'ilgan kuniningizni kiriting.")
        return
    await state.update_data(age=int(message.text))

    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Telefon raqamingizni yuboring:", reply_markup=keyboard)
    await state.set_state(UserState.waiting_for_phone_number)

# 🔹 **Telefon raqamini qabul qilish va bazaga yozish**
@dp.message(UserState.waiting_for_phone_number, F.contact)
async def process_phone_number(message: Message, state: FSMContext):
    phone_number = message.contact.phone_number
    await state.update_data(phone_number=phone_number)

    # **Barcha ma’lumotlarni olish**
    data = await state.get_data()
    user_id = message.from_user.id

    # **Bazaga saqlash**
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (id, full_name, region, age, phone_number) VALUES (?, ?, ?, ?, ?)",
        (user_id, data['full_name'], data['region'], data['age'], phone_number)
    )
    conn.commit()
    conn.close()

    # **Admin ga xabar yuborish**
    #await bot.send_message(ADMIN_ID, f"🆕 Yangi foydalanuvchi: {data['full_name']}\n📍 {data['region']}\n🎂 {data['age']}\n📞 {phone_number}")

    await message.answer("✅ Ro‘yxatdan o‘tdingiz!", reply_markup=types.ReplyKeyboardRemove())
    await message.answer("Endi xabar yo'lashingiz mumkin!")
    await state.clear()


    
# Admin panel tugmalari
@dp.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id in ADMIN_ID:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kanal qo‘shish", callback_data="add_channel")],
            [InlineKeyboardButton(text="➖ Kanal o‘chirish", callback_data="remove_channel")],
            [InlineKeyboardButton(text="👤 Admin qo‘shish", callback_data="add_admin")],
            [InlineKeyboardButton(text="🚫 Admin o‘chirish", callback_data="remove_admin")]
        ])
        await message.answer("👑 Admin paneliga xush kelibsiz!", reply_markup=keyboard)
    else:
        await message.answer("❌ Siz admin emassiz!")



@dp.callback_query(F.data == "add_channel")
async def add_channel(call: CallbackQuery):
    await call.message.answer("📢 Kanalni @channel shaklida yuboring:")

# Kanal nomini qabul qilish
@dp.message(F.text.startswith("@"))
async def process_channel_addition(message: Message):
    if message.from_user.id not in ADMIN_ID:
        await message.answer("🚫 Sizda kanal qo‘shish huquqi yo‘q!")
        return

    channel_name = message.text.strip()

    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()

    # Avval kanal bor yoki yo‘qligini tekshiramiz
    cursor.execute("SELECT * FROM channels WHERE channel_name = ?", (channel_name,))
    existing_channel = cursor.fetchone()

    if existing_channel:
        await message.answer("⚠️ Bu kanal avval qo‘shilgan!")
    else:
        cursor.execute("INSERT INTO channels (channel_name) VALUES (?)", (channel_name,))
        conn.commit()
        await message.answer(f"✅ Kanal qo‘shildi: {channel_name}")

    conn.close()

@dp.callback_query(F.data == "remove_channel")
async def remove_channel(call: CallbackQuery):
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()

    cursor.execute("SELECT channel_name FROM channels")
    channels = cursor.fetchall()
    conn.close()

    if not channels:
        await call.message.answer("🚫 Hech qanday kanal mavjud emas!")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ch[0], callback_data=f"del_channel_{ch[0]}")] for ch in channels
    ])

    await call.message.answer("🗑 O‘chiriladigan kanalni tanlang:", reply_markup=keyboard)


# Kanalni bazadan o‘chirish
@dp.callback_query(F.data.startswith("del_channel_"))
async def delete_channel(call: CallbackQuery):
    channel_name = call.data.split("del_channel_")[1]

    # Bazadan o‘chirish
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE channel_name = ?", (channel_name,))
    conn.commit()
    conn.close()

    await call.message.answer(f"❌ Kanal o‘chirildi: {channel_name}")
@dp.callback_query(F.data == "remove_admin")
async def remove_admin(call: CallbackQuery):
    global ADMIN_ID
    ADMIN_ID = load_admins_from_db()  # Adminlarni yangilash

    if not ADMIN_ID:
        await call.message.answer("🚫 Hech qanday admin yo‘q!")
        return

    # Agar faqat 1 ta admin bo‘lsa, o‘chirishga ruxsat berilmaydi
    if len(ADMIN_ID) == 1:
        await call.message.answer("🚫 Kamida bitta admin qolishi kerak!")
        return

    keyboard_buttons = []
    for admin_id in ADMIN_ID:
        user = await bot.get_chat(admin_id)  # Foydalanuvchi ma'lumotlarini olish
        admin_name = user.username if user.username else f"{user.first_name} {user.last_name or ''}".strip()
        
        keyboard_buttons.append([
            InlineKeyboardButton(text=admin_name, callback_data=f"del_admin_{admin_id}")
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await call.message.answer("👤 O‘chiriladigan adminni tanlang:", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("del_admin_"))
async def confirm_admin_removal(call: CallbackQuery):
    global ADMIN_ID
    admin_id_str = call.data.replace("del_admin_", "")
    
    if not admin_id_str.isdigit():
        await call.message.answer("⚠️ Xatolik! Noto‘g‘ri admin ID.")
        return
    
    admin_id = int(admin_id_str)

    # Adminlar ro‘yxatini yana tekshiramiz
    ADMIN_ID = load_admins_from_db()
    
    # Agar faqat 1 ta admin qolgan bo‘lsa, o‘chirishga ruxsat berilmaydi
    if len(ADMIN_ID) == 1:
        await call.message.answer("🚫 Kamida bitta admin qolishi kerak!")
        return
    
    try:
        user = await bot.get_chat(admin_id)
        full_name = user.first_name
    except Exception:
        await call.message.answer("⚠️ Bu admin topilmadi!")
        return

    if admin_id in ADMIN_ID:
        conn = sqlite3.connect("myusers.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM admins WHERE id=?", (admin_id,))
        conn.commit()
        conn.close()

        ADMIN_ID.remove(admin_id)  # Ro‘yxatdan ham o‘chirish
        await call.message.answer(f"✅ Admin o‘chirildi: {full_name}")
    else:
        await call.message.answer("⚠️ Bu admin allaqachon o‘chirilgan yoki topilmadi!")


@dp.callback_query(F.data == "add_admin")
async def add_admin(call: CallbackQuery):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Admin Tanlang", request_user={"request_id": 1, "user_is_bot": False,}, request_user_id=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    await call.message.answer("👤 Iltimos, admin sifatida qo‘shiladigan foydalanuvchini tanlang:", reply_markup=keyboard)

@dp.message(F.text == "❌ Bekor qilish")
async def cancel_admin_selection(message: Message):
    await message.answer("❌ Admin tanlash bekor qilindi.", reply_markup=ReplyKeyboardRemove())

@dp.message(F.user_shared)
async def handle_chosen_user(message: Message):
    user_id = message.user_shared.user_id

    try:
        user = await bot.get_chat(user_id)  # Foydalanuvchi ma'lumotlarini olish
        username = user.first_name  # Foydalanuvchi ismini olish

        if user_id not in ADMIN_ID:  # Takroriy qo‘shilishni oldini olish
            add_new_admin(user_id)  # Bazaga qo‘shish funksiyasini chaqirish

            await message.answer(
                f"✅ {username} admin sifatida qo‘shildi!",
                reply_markup=ReplyKeyboardRemove()  # Tugmani o‘chirish
            )
        else:
            await message.answer("⚠️ Bu foydalanuvchi allaqachon admin!")
    except Exception as e:
        await message.answer(f"⚠ Xatolik yuz berdi: {e}")


@dp.message(F.text.isdigit())
async def process_admin_addition(message: Message):
    if message.from_user.id in ADMIN_ID:
        new_admin = int(message.text)
        
        if new_admin in ADMIN_ID:
            await message.answer("⚠️ Bu foydalanuvchi allaqachon admin!")
            return
        
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()
    cursor.execute(
    "INSERT INTO users (id) VALUES (?, ?, ?, ?, ?)",
    (id))
    conn.commit()
    conn.close()


        # Admin ro‘yxatiga qo‘shish
    ADMIN_ID.append(new_admin)

        # Adminning ismini olish
    user_info = await bot.get_chat(new_admin)

    await message.answer(f"✅ {user_info.full_name} (ID: {new_admin}) admin sifatida bazaga qo‘shildi!")


messages_data = {} 

@dp.message()
async def send_msg_to_admin(message: Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)
    if user_id in ADMIN_ID:
        await message.answer("Adminlar xabar yubora olmaydi!")
        return
    if not is_subscribed:
        CHANNELS = load_channels_from_db()  # Har safar yangilangan ro‘yxat
        if not CHANNELS:
            await message.answer("❌ Kanallar ro‘yxati bo‘sh! Admin bilan bog‘laning.")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📢 {channel.replace('@', '')}", url=f"https://t.me/{channel.replace('@', '')}")] for channel in CHANNELS
        ])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")])

        await message.answer("❌ Botdan foydalanish uchun quyidagi kanallarga a’zo bo‘lishingiz kerak:", reply_markup=keyboard)
        return

    # Agar foydalanuvchi obuna bo'lsa, xabar adminlarga yuboriladi
    if len(message.text) > 820:
        await message.answer("❌ Xabaringiz juda uzun! Iltimos, 820 belgidan kamroq yozing.")
    else:
        text = (f"👤 Xabar yuboruvchi: {message.from_user.full_name}\n"
                f"📩 Xabar holati: ❌ O‘QILMAGAN\n\n"
                f"💬 Xabar:\n{message.text}")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ O‘qildi", callback_data=f"read_{message.message_id}")]
        ])

        messages_data[message.message_id] = {"user_id": user_id, "admins": {}}

        for admin in ADMIN_ID:
            sent_msg = await bot.send_message(admin, text, reply_markup=keyboard)
            messages_data[message.message_id]["admins"][admin] = sent_msg.message_id

        # ✅ **Foydalanuvchiga xabar yuborilganini bildiruvchi xabar**
        await message.answer("✅ Xabaringiz yuborildi! Agar admin o‘qisa, sizga xabar beramiz.")


@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(call: CallbackQuery):
    user_id = call.from_user.id
    is_subscribed = await check_subscription(user_id)

    if is_subscribed:
        await call.message.edit_text("✅ Obunani muvaffaqiyatli tekshirdik! Endi botdan foydalanishingiz mumkin.")
    else:
        await call.answer("🚫 Hali ham kanallarga obuna bo‘lmagansiz!", show_alert=True)


@dp.callback_query(F.data.startswith("read_"))
async def mark_message_as_read(call: CallbackQuery):
    """Xabarni o‘qilgan deb belgilaydi, barcha adminlarga yangilaydi va userga xabar yuboradi"""
    msg_id = int(call.data.split("_")[1])  # Xabar ID-sini olish
    new_text = call.message.text.replace("❌ O‘QILMAGAN", "✅ O‘QILGAN")

    if msg_id in messages_data:
        user_id = messages_data[msg_id]["user_id"]  # Xabar yuborgan user ID

        # Barcha adminlarda xabarni o‘qilgan deb yangilash
        for admin, sent_msg_id in messages_data[msg_id]["admins"].items():
            try:
                await bot.edit_message_text(new_text, chat_id=admin, message_id=sent_msg_id)
            except Exception as e:
                print(f"Admin {admin} uchun xabar yangilanmadi: {e}")

        # Userga xabar yuborish
        try:
            await bot.send_message(chat_id=user_id, text="📩 Sizning xabaringiz admin tomonidan o‘qildi!")
        except Exception as e:
            print(f"Foydalanuvchiga xabar yuborilmadi: {e}")

async def on_startup():
    global CHANNELS
    CHANNELS = load_channels_from_db()
    print("🔄 Kanallar yangilandi:", CHANNELS)

dp.startup.register(on_startup)  
        

# 🔹 **Botni ishga tushirish**
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
 