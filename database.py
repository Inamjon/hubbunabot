import sqlite3

conn = sqlite3.connect("myusers.db")
cursor = conn.cursor()

# "channels" jadvalini yaratish
cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT UNIQUE NOT NULL
)
""")

# O‘zgarishlarni saqlash
conn.commit()
conn.close()

print("✅ 'channels' jadvali yaratildi yoki avval mavjud bo‘lsa, o‘zgarmadi.")


def create_tables():
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()

create_tables()


def init_db():
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,  
            full_name TEXT,
            region TEXT,
            age INTEGER,
            phone_number TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            url_link TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


def load_admins():
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM admins")  # id ustuni mavjud ekanligiga ishonch hosil qiling
    admins = [int(row[0]) for row in cursor.fetchall()]  # ID larni butun songa o‘girish
    conn.close()
    print("Adminlar yuklandi:", admins)  # Tekshirish uchun
    return admins



def load_channels_from_db():
    """Database-dan kanallarni yuklash"""
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()

    cursor.execute("SELECT channel_name FROM channels")
    channels = [row[0] for row in cursor.fetchall()]  # Faqat kanal nomlarini olish

    conn.close()
    return channels

CHANNELS = load_channels_from_db()




def add_new_admin(admin_id: int):
    """
    Yangi adminni bazaga qo'shish.
    
    :param admin_id: Yangi adminning Telegram ID-si.
    """
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()
    
    try:
        # Adminni bazaga qo'shish
        cursor.execute("INSERT INTO admins (id) VALUES (?)", (admin_id,))
        conn.commit()
        print(f"✅ Admin qo'shildi: {admin_id}")
    except sqlite3.IntegrityError:
        # Agar admin allaqachon mavjud bo'lsa, xatolikni chiqarish
        print(f"⚠️ Bu admin allaqachon mavjud: {admin_id}")
    finally:
        conn.close()

ADMIN_ID = load_admins()



def load_admins_from_db():
    """Bazadan barcha adminlarni yuklaydi"""
    conn = sqlite3.connect("myusers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM admins")
    admins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return admins

ADMIN_ID = load_admins_from_db()
