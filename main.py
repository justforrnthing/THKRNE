# ============================================
# بوت ذكرني - ملف كامل بجميع الميزات (مصحح)
# ============================================

# ============================================
# القسم 1: المكتبات والإعدادات
# ============================================

import logging
import sqlite3
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz
import aiohttp

# ========== الإعدادات ==========
TOKEN = "8608117977:AAG86A4W-2w15c8MdClr6VTUfqhxNOX5ITc"
OWNER_ID = 8495422765  # ضع معرفك في تليجرام (للوحة التحكم)
TIMEZONE = "Asia/Riyadh"
DB_NAME = "thkrne_users.db"

# أوقات التذكير الثابتة
MORNING_HOUR = 8
MORNING_MINUTE = 0
EVENING_HOUR = 19
EVENING_MINUTE = 0

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# القسم 2: محتوى الأذكار والرسائل
# ============================================

# ========== أذكار الصباح ==========
MORNING_ADHKAR = [
    "🌅 أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ رَبِّ الْعَالَمِينَ",
    "🌅 اللَّهُمَّ بِكَ أَصْبَحْنَا وَبِكَ أَمْسَيْنَا وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ النُّشُورُ",
    "🌅 اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا وَرِزْقًا طَيِّبًا وَعَمَلًا مُتَقَبَّلًا",
    "🌅 سُبْحَانَ اللَّهِ وَبِحَمْدِهِ (100 مرة)",
    "🌅 لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ (10 مرات)",
    "🌅 اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَفْوَ وَالْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ",
    "🌅 رَضِيتُ بِاللَّهِ رَبًّا وَبِالْإِسْلَامِ دِينًا وَبِمُحَمَّدٍ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ نَبِيًّا",
    "🌅 اللَّهُمَّ إِنِّي أَصْبَحْتُ أُشْهِدُكَ وَأُشْهِدُ حَمَلَةَ عَرْشِكَ",
]

# ========== أذكار المساء ==========
EVENING_ADHKAR = [
    "🌙 أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ رَبِّ الْعَالَمِينَ",
    "🌙 اللَّهُمَّ بِكَ أَمْسَيْنَا وَبِكَ أَصْبَحْنَا وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ الْمَصِيرُ",
    "🌙 اللَّهُمَّ إِنِّي أَسْأَلُكَ خَيْرَ هَذِهِ اللَّيْلَةِ وَخَيْرَ مَا بَعْدَهَا",
    "🌙 أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ (3 مرات)",
    "🌙 اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ",
    "🌙 سُبْحَانَ اللَّهِ وَبِحَمْدِهِ (100 مرة)",
    "🌙 اللَّهُمَّ إِنِّي أَمْسَيْتُ أُشْهِدُكَ وَأُشْهِدُ حَمَلَةَ عَرْشِكَ",
    "🌙 لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ",
]

# ========== أعمال اليوم الصالحة ==========
GOOD_DEEDS = [
    "📖 اقرأ ورداً من القرآن (جزء أو حزب)",
    "🤲 ادعُ لأخيك المسلم بظهر الغيب",
    "💧 تصدق ولو بابتسامة",
    "🌿 قل سبحان الله وبحمده 100 مرة",
    "🕌 صلِّ الضحى ركعتين",
    "📿 قل لا إله إلا الله 100 مرة",
    "☪️ صلِّ على النبي ﷺ 10 مرات",
    "💚 استغفر الله 100 مرة",
    "🤲 ادعُ للمسلمين في فلسطين وغزة",
    "📖 اقرأ سورة الكهف يوم الجمعة",
]

# ========== أذكار النوم ==========
SLEEP_ADHKAR = [
    "🌙 بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا",
    "🌙 اللَّهُمَّ قِنِي عَذَابَكَ يَوْمَ تَبْعَثُ عِبَادَكَ (3 مرات)",
    "🌙 آيَةُ الْكُرْسِيِّ (مرة واحدة)",
    "🌙 قُلْ هُوَ اللَّهُ أَحَدٌ (3 مرات)",
    "🌙 قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ (3 مرات)",
    "🌙 قُلْ أَعُوذُ بِرَبِّ النَّاسِ (3 مرات)",
]

# ========== أذكار الاستيقاظ ==========
WAKE_ADHKAR = [
    "☀️ الْحَمْدُ لِلَّهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ",
    "☀️ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ",
    "☀️ سُبْحَانَ اللَّهِ وَبِحَمْدِهِ",
]

# ========== أذكار بعد الصلاة ==========
POST_PRAYER_ADHKAR = [
    "🕌 أَسْتَغْفِرُ اللَّهَ (3 مرات)",
    "🕌 اللَّهُمَّ أَنْتَ السَّلَامُ وَمِنْكَ السَّلَامُ تَبَارَكْتَ يَا ذَا الْجَلَالِ وَالْإِكْرَامِ",
    "🕌 سُبْحَانَ اللَّهِ (33 مرة)",
    "🕌 الْحَمْدُ لِلَّهِ (33 مرة)",
    "🕌 اللَّهُ أَكْبَرُ (33 مرة)",
    "🕌 لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ",
]

# ========== أدعية متنوعة ==========
DAILY_DUA = [
    "🤲 رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
    "🤲 اللَّهُمَّ إِنِّي أَسْأَلُكَ الْهُدَى وَالتُّقَى وَالْعَفَافَ وَالْغِنَى",
    "🤲 اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا وَرِزْقًا طَيِّبًا وَعَمَلًا مُتَقَبَّلًا",
    "🤲 اللَّهُمَّ أَصْلِحْ لِي دِينِي الَّذِي هُوَ عِصْمَةُ أَمْرِي",
    "🤲 اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ",
    "🤲 اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْعَجْزِ وَالْكَسَلِ",
]

# ========== دعاء فلسطين وغزة ==========
PALESTINE_DUAS = [
    "🤲 **اللهم انصر إخواننا في فلسطين وغزة**\n\n"
    "اللهم احفظهم وارحمهم وثبت أقدامهم\n"
    "اللهم انصرهم على من عاداهم\n"
    "اللهم فرج عنهم كربهم وأزل عنهم همهم\n"
    "اللهم اجعل كيد أعدائهم في نحورهم\n"
    "اللهم أرهم في أعدائهم عجائب قدرتك\n\n"
    "🤲 آمين يا رب العالمين",
    
    "🇵🇸 **دعاء لأهل غزة:**\n\n"
    "اللهم اشف جرحاهم وألم جوعهم\n"
    "اللهم احفظ أطفالهم ونسائهم\n"
    "اللهم ارحم شهداءهم وتقبلهم عندك\n"
    "اللهم ثبت قلوبهم على دينك\n"
    "اللهم اجعل لهم فرجاً ومخرجاً\n\n"
    "🤲 اللهم استجب لدعائنا",
    
    "🕌 **تذكير بالدعاء لأهل فلسطين:**\n\n"
    "قال رسول الله ﷺ:\n"
    "«دعوة المسلم لأخيه بظهر الغيب مستجابة»\n\n"
    "ادعوا لإخواننا في غزة وفلسطين\n"
    "فالدعاء سلاح المؤمن\n\n"
    "🤲 اللهم انصرهم وارحمهم",
    
    "💔 **أهلنا في غزة يحتاجون دعواتنا:**\n\n"
    "اللهم اجعلهم في حمايتك ورعايتك\n"
    "اللهم ارفع عنهم البلاء والوباء\n"
    "اللهم امنحهم الصبر والقوة\n"
    "اللهم اكتب لهم النصر والتمكين\n\n"
    "🤲 لا تنسوهم من دعائكم",
]

# ========== رسائل تحفيزية ==========
MOTIVATIONAL_MESSAGES = [
    "💪 ذكر الله يورث القلب طمأنينة",
    "🌹 كل تسبيحة صدقة",
    "⭐ لا تنسَ ذكر الله في كل لحظة",
    "💚 الذكر نور في القلب ونور على الصراط",
    "🤲 الدعاء هو العبادة",
    "🌿 الاستغفار يفتح أبواب الرزق",
    "📖 القرآن شفاء للقلوب",
    "💫 الصلاة عماد الدين",
    "🌙 قيام الليل نور للمؤمن",
    "💝 الإخلاص في العمل من أسباب القبول",
]

# ========== رسائل عشوائية إضافية ==========
RANDOM_MESSAGES = [
    "سبحان الله وبحمده عدد خلقه ورضا نفسه وزنة عرشه ومداد كلماته",
    "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير",
    "اللهم صلِّ وسلم وبارك على سيدنا محمد",
    "الحمد لله الذي هدانا لهذا وما كنا لنهتدي لولا أن هدانا الله",
]

# ============================================
# القسم 3: قائمة المدن
# ============================================

CITIES = {
    "السعودية": {
        "riyadh": "Riyadh",
        "jeddah": "Jeddah",
        "makkah": "Makkah",
        "madinah": "Madinah",
        "dammam": "Dammam",
        "tabuk": "Tabuk",
        "abha": "Abha",
    },
    "مصر": {
        "cairo": "Cairo",
        "alexandria": "Alexandria",
        "giza": "Giza",
        "luxor": "Luxor",
        "aswan": "Aswan",
    },
    "الأردن": {
        "amman": "Amman",
        "zarqa": "Zarqa",
        "irbid": "Irbid",
        "aqaba": "Aqaba",
    },
    "فلسطين": {
        "jerusalem": "Jerusalem",
        "gaza": "Gaza",
        "ramallah": "Ramallah",
        "nablus": "Nablus",
        "hebron": "Hebron",
    },
    "الإمارات": {
        "dubai": "Dubai",
        "abudhabi": "Abu Dhabi",
        "sharjah": "Sharjah",
        "ajman": "Ajman",
    },
    "الكويت": {
        "kuwait": "Kuwait City",
    },
    "قطر": {
        "doha": "Doha",
    },
    "البحرين": {
        "manama": "Manama",
    },
    "سلطنة عمان": {
        "muscat": "Muscat",
    },
    "اليمن": {
        "sanaa": "Sanaa",
        "aden": "Aden",
    },
    "العراق": {
        "baghdad": "Baghdad",
        "basra": "Basra",
        "mosul": "Mosul",
    },
    "سوريا": {
        "damascus": "Damascus",
        "aleppo": "Aleppo",
        "homs": "Homs",
    },
    "لبنان": {
        "beirut": "Beirut",
        "tripoli": "Tripoli",
    },
    "ليبيا": {
        "tripoli_libya": "Tripoli",
        "benghazi": "Benghazi",
    },
    "تونس": {
        "tunis": "Tunis",
    },
    "الجزائر": {
        "algiers": "Algiers",
    },
    "المغرب": {
        "rabat": "Rabat",
        "casablanca": "Casablanca",
    },
    "السودان": {
        "khartoum": "Khartoum",
    },
    "تركيا": {
        "istanbul": "Istanbul",
        "ankara": "Ankara",
    },
}

# ============================================
# القسم 4: قاعدة البيانات
# ============================================

def init_db():
    """إنشاء قاعدة البيانات والجداول"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered_at TEXT,
            active INTEGER DEFAULT 1,
            country TEXT,
            city TEXT,
            receive_morning INTEGER DEFAULT 1,
            receive_evening INTEGER DEFAULT 1,
            receive_random INTEGER DEFAULT 1,
            timezone TEXT DEFAULT 'Asia/Riyadh'
        )
    ''')
    
    # جدول الإحصائيات
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            deed_date TEXT,
            deed_type TEXT,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ قاعدة البيانات جاهزة")

def add_user(user_id, username=None, first_name=None, last_name=None):
    """إضافة مستخدم جديد"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    c.execute('''
        INSERT OR IGNORE INTO users 
        (user_id, username, first_name, last_name, registered_at) 
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, now))
    
    conn.commit()
    conn.close()

def get_all_active_users():
    """الحصول على جميع المستخدمين النشطين"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE active = 1")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_all_users():
    """الحصول على جميع المستخدمين (حتى غير النشطين)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def save_user_city(user_id, country, city):
    """حفظ مدينة المستخدم"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET country = ?, city = ? 
        WHERE user_id = ?
    ''', (country, city, user_id))
    conn.commit()
    conn.close()

def get_user_city(user_id):
    """استرجاع مدينة المستخدم"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT country, city FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (None, None)

def toggle_user_active(user_id, active):
    """تفعيل/إلغاء تفعيل المستخدم"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET active = ? WHERE user_id = ?", (active, user_id))
    conn.commit()
    conn.close()

def get_user_settings(user_id):
    """استرجاع إعدادات المستخدم"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT receive_morning, receive_evening, receive_random 
        FROM users WHERE user_id = ?
    ''', (user_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (1, 1, 1)

# ============================================
# القسم 5: دوال مواقيت الصلاة
# ============================================

async def get_prayer_times(city, country="Saudi Arabia"):
    """جلب مواقيت الصلاة من Aladhan API"""
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=4"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                if data["code"] == 200:
                    timings = data["data"]["timings"]
                    return {
                        "الفجر": timings["Fajr"],
                        "الظهر": timings["Dhuhr"],
                        "العصر": timings["Asr"],
                        "المغرب": timings["Maghrib"],
                        "العشاء": timings["Isha"],
                    }
    except Exception as e:
        logger.error(f"خطأ في جلب المواقيت: {e}")
        return None
    return None

# ============================================
# القسم 6: دوال الأزرار والقوائم
# ============================================

def get_main_keyboard():
    """قائمة الأزرار الرئيسية"""
    keyboard = [
        [InlineKeyboardButton("🌅 أذكار الصباح", callback_data="morning")],
        [InlineKeyboardButton("🌙 أذكار المساء", callback_data="evening")],
        [InlineKeyboardButton("⭐ أعمال اليوم", callback_data="deeds")],
        [InlineKeyboardButton("🌙 أذكار النوم", callback_data="sleep")],
        [InlineKeyboardButton("☀️ أذكار الاستيقاظ", callback_data="wake")],
        [InlineKeyboardButton("🕌 بعد الصلاة", callback_data="post_prayer")],
        [InlineKeyboardButton("🤲 دعاء اليوم", callback_data="dua")],
        [InlineKeyboardButton("🕌 مواقيت الصلاة", callback_data="show_prayer")],
        [InlineKeyboardButton("🌍 اختيار المدينة", callback_data="set_location")],
        [InlineKeyboardButton("🇵🇸 دعاء لفلسطين وغزة", callback_data="palestine")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="stats")],
        [InlineKeyboardButton("❓ مساعدة", callback_data="help")],
        [InlineKeyboardButton("🛠️ لوحة المالك", callback_data="owner_panel")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_countries_keyboard():
    """أزرار اختيار البلد"""
    keyboard = []
    countries = list(CITIES.keys())
    
    for i in range(0, len(countries), 2):
        row = []
        for j in range(i, min(i + 2, len(countries))):
            row.append(InlineKeyboardButton(
                countries[j], 
                callback_data=f"country_{countries[j]}"
            ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def get_cities_keyboard(country):
    """أزرار اختيار المدينة حسب البلد"""
    keyboard = []
    cities = CITIES.get(country, {})
    
    for city_key, city_name in cities.items():
        keyboard.append([InlineKeyboardButton(
            city_name, 
            callback_data=f"city_{country}_{city_key}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع للبلدان", callback_data="back_countries")])
    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back")])
    
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard():
    """قائمة إعدادات المستخدم"""
    keyboard = [
        [InlineKeyboardButton("🔔 تفعيل/إلغاء تذكير الصباح", callback_data="toggle_morning")],
        [InlineKeyboardButton("🔔 تفعيل/إلغاء تذكير المساء", callback_data="toggle_evening")],
        [InlineKeyboardButton("🔔 تفعيل/إلغاء التذكيرات العشوائية", callback_data="toggle_random")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_owner_keyboard():
    """لوحة تحكم المالك"""
    keyboard = [
        [InlineKeyboardButton("📢 إرسال رسالة للجميع", callback_data="broadcast")],
        [InlineKeyboardButton("📊 إحصائيات البوت", callback_data="owner_stats")],
        [InlineKeyboardButton("📋 عرض المستخدمين", callback_data="owner_users")],
        [InlineKeyboardButton("💾 نسخ احتياطي", callback_data="owner_backup")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# القسم 7: معالجات الأوامر والأزرار
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب والقائمة الرئيسية"""
    user = update.effective_user
    add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_text = f"""
☀️ **بسم الله الرحمن الرحيم**

مرحباً بك في بوت **ذكرني**! 🤲

أنا هنا لتذكيرك بأذكارك اليومية وأعمالك الصالحة.

📌 **مميزات البوت:**
• أذكار الصباح والمساء
• أذكار النوم والاستيقاظ
• أعمال يومية صالحة
• مواقيت الصلاة حسب مدينتك
• تذكيرات عشوائية 2-3 مرات يومياً
• دعاء خاص لفلسطين وغزة 🇵🇸

🔔 **أوقات التذكير:**
• الصباح: 8:00 صباحاً
• المساء: 7:00 مساءً
• تذكيرات عشوائية: 2-3 مرات يومياً

**اختر ما تريد من القائمة أدناه:**

بارك الله فيك ونفع بك الإسلام والمسلمين 🌹
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على الأزرار"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # قاموس الأقسام
    sections = {
        "morning": ("🌅 **أذكار الصباح**", MORNING_ADHKAR),
        "evening": ("🌙 **أذكار المساء**", EVENING_ADHKAR),
        "deeds": ("⭐ **أعمال اليوم الصالحة**", GOOD_DEEDS),
        "sleep": ("🌙 **أذكار النوم**", SLEEP_ADHKAR),
        "wake": ("☀️ **أذكار الاستيقاظ**", WAKE_ADHKAR),
        "post_prayer": ("🕌 **أذكار بعد الصلاة**", POST_PRAYER_ADHKAR),
        "dua": ("🤲 **دعاء اليوم**", DAILY_DUA),
        "palestine": ("🇵🇸 **دعاء لفلسطين وغزة**", PALESTINE_DUAS),
    }
    
    if query.data in sections:
        title, content = sections[query.data]
        text = f"{title}\n\n" + "\n\n".join(content)
        text += "\n\n📌 *تذكر: الإخلاص في الدعاء من أسباب الإجابة*"
        await query.edit_message_text(text, parse_mode="Markdown")
        await query.message.reply_text("🔙 اضغط /start للرجوع للقائمة الرئيسية")
    
    elif query.data == "show_prayer":
        # عرض مواقيت الصلاة
        country, city = get_user_city(user_id)
        
        if not city:
            await query.edit_message_text(
                "⚠️ **لم تختر مدينتك بعد!**\n\n"
                "اضغط على زر '🌍 اختيار المدينة' لاختيار مدينتك",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🌍 اختيار المدينة", callback_data="set_location")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        times = await get_prayer_times(city, country)
        
        if not times:
            await query.edit_message_text(
                "❌ عذراً، حدث خطأ في جلب المواقيت.\n"
                "تأكد من اسم المدينة أو حاول مرة أخرى."
            )
            return
        
        text = f"🕌 **مواقيت الصلاة في {city}**\n\n"
        for name, time in times.items():
            text += f"• {name}: {time}\n"
        text += "\n📌 *طريقة الحساب: أم القرى*"
        
        await query.edit_message_text(text, parse_mode="Markdown")
    
    elif query.data == "set_location":
        # عرض قائمة البلدان
        await query.edit_message_text(
            "🌍 **اختر بلدك:**\n\n"
            "سيتم حفظ اختيارك لتذكيرك بمواقيت الصلاة بدقة",
            reply_markup=get_countries_keyboard(),
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("country_"):
        # اختيار البلد
        country = query.data.replace("country_", "")
        context.user_data["temp_country"] = country
        
        await query.edit_message_text(
            f"🏙️ **اختر مدينتك في {country}:**",
            reply_markup=get_cities_keyboard(country),
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("city_"):
        # اختيار المدينة
        parts = query.data.split("_")
        country = parts[1]
        city_key = parts[2]
        city_name = CITIES[country][city_key]
        
        save_user_city(user_id, country, city_name)
        context.user_data["country"] = country
        context.user_data["city"] = city_name
        
        await query.edit_message_text(
            f"✅ **تم حفظ مدينتك بنجاح!**\n\n"
            f"🌍 البلد: {country}\n"
            f"🏙️ المدينة: {city_name}\n\n"
            f"يمكنك الآن استخدام زر 'مواقيت الصلاة' لمعرفة المواقيت",
            parse_mode="Markdown"
        )
    
    elif query.data == "back_countries":
        # رجوع لقائمة البلدان
        await query.edit_message_text(
            "🌍 **اختر بلدك:**",
            reply_markup=get_countries_keyboard(),
            parse_mode="Markdown"
        )
    
    elif query.data == "settings":
        # عرض الإعدادات
        receive_morning, receive_evening, receive_random = get_user_settings(user_id)
        
        morning_status = "✅ مفعل" if receive_morning else "❌ غير مفعل"
        evening_status = "✅ مفعل" if receive_evening else "❌ غير مفعل"
        random_status = "✅ مفعل" if receive_random else "❌ غير مفعل"
        
        settings_text = f"""
⚙️ **إعدادات التذكير**

🔔 تذكير الصباح (8:00 صباحاً): {morning_status}
🔔 تذكير المساء (7:00 مساءً): {evening_status}
🔔 تذكيرات عشوائية: {random_status}

📌 اضغط على الأزرار لتغيير الإعدادات
"""
        await query.edit_message_text(
            settings_text,
            reply_markup=get_settings_keyboard(),
            parse_mode="Markdown"
        )
    
    elif query.data == "toggle_morning":
        # تبديل تذكير الصباح
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT receive_morning FROM users WHERE user_id = ?", (user_id,))
        current = c.fetchone()[0]
        new_value = 0 if current else 1
        c.execute("UPDATE users SET receive_morning = ? WHERE user_id = ?", (new_value, user_id))
        conn.commit()
        conn.close()
        
        status = "مفعل ✅" if new_value else "غير مفعل ❌"
        await query.edit_message_text(
            f"✅ تم تغيير إعداد تذكير الصباح إلى: {status}",
            reply_markup=get_settings_keyboard()
        )
    
    elif query.data == "toggle_evening":
        # تبديل تذكير المساء
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT receive_evening FROM users WHERE user_id = ?", (user_id,))
        current = c.fetchone()[0]
        new_value = 0 if current else 1
        c.execute("UPDATE users SET receive_evening = ? WHERE user_id = ?", (new_value, user_id))
        conn.commit()
        conn.close()
        
        status = "مفعل ✅" if new_value else "غير مفعل ❌"
        await query.edit_message_text(
            f"✅ تم تغيير إعداد تذكير المساء إلى: {status}",
            reply_markup=get_settings_keyboard()
        )
    
    elif query.data == "toggle_random":
        # تبديل التذكيرات العشوائية
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT receive_random FROM users WHERE user_id = ?", (user_id,))
        current = c.fetchone()[0]
        new_value = 0 if current else 1
        c.execute("UPDATE users SET receive_random = ? WHERE user_id = ?", (new_value, user_id))
        conn.commit()
        conn.close()
        
        status = "مفعل ✅" if new_value else "غير مفعل ❌"
        await query.edit_message_text(
            f"✅ تم تغيير إعداد التذكيرات العشوائية إلى: {status}",
            reply_markup=get_settings_keyboard()
        )
    
    elif query.data == "stats":
        # عرض الإحصائيات
        stats_text = """
📊 **إحصائياتك**

📌 عدد الأذكار المنجزة اليوم: 0
📌 عدد الأيام المتتالية: 0
📌 إجمالي الأعمال الصالحة: 0

*استمر في ذكر الله، فالحسنات تزيد!* 💪
"""
        await query.edit_message_text(stats_text, parse_mode="Markdown")
        await query.message.reply_text("🔙 اضغط /start للرجوع")
    
    elif query.data == "help":
        help_text = """
❓ **مساعدة - بوت ذكرني**

📌 **الأوامر المتاحة:**
/start - القائمة الرئيسية
/morning - أذكار الصباح
/evening - أذكار المساء
/deeds - أعمال اليوم
/sleep - أذكار النوم
/wake - أذكار الاستيقاظ
/prayer - أذكار بعد الصلاة
/dua - أدعية متنوعة
/prayertimes - مواقيت الصلاة
/setcity - اختيار المدينة
/stats - إحصائياتي
/stop - إيقاف التذكير
/help - المساعدة
/owner - لوحة المالك

🔔 **أوقات التذكير:**
• الصباح: 8:00 صباحاً
• المساء: 7:00 مساءً
• عشوائية: 2-3 مرات يومياً

🇵🇸 **لا تنسَ الدعاء لإخواننا في فلسطين وغزة**

📞 **مطور البوت:** @IIIEID

**نسأل الله التوفيق والقبول** 🤲
"""
        await query.edit_message_text(help_text, parse_mode="Markdown")
    
    elif query.data == "back":
        await query.edit_message_text(
            "☀️ **القائمة الرئيسية:**",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    elif query.data == "owner_panel":
        # لوحة تحكم المالك
        if user_id != OWNER_ID:
            await query.edit_message_text("⛔ هذا الأمر مخصص للمالك فقط!")
            return
        
        await query.edit_message_text(
            "🛠️ **لوحة تحكم المالك**\n\n"
            "اختر الإجراء الذي تريد القيام به:",
            reply_markup=get_owner_keyboard(),
            parse_mode="Markdown"
        )
    
    elif query.data == "broadcast":
        # لوحة تحكم المالك - بث رسالة
        if user_id != OWNER_ID:
            await query.edit_message_text("⛔ هذا الأمر مخصص للمالك فقط!")
            return
        
        context.user_data["broadcast_mode"] = True
        await query.edit_message_text(
            "📢 **وضع البث الجماعي**\n\n"
            "أرسل الرسالة التي تريد إرسالها لجميع المستخدمين.\n"
            "يمكنك إرسال نص، صورة، فيديو، أو أي نوع من الملفات.\n\n"
            "لإلغاء الأمر، أرسل /cancel"
        )
    
    elif query.data == "owner_stats":
        if user_id != OWNER_ID:
            await query.edit_message_text("⛔ هذا الأمر مخصص للمالك فقط!")
            return
        
        users = get_all_users()
        active_users = get_all_active_users()
        
        # حساب إحصائيات إضافية
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users WHERE receive_morning = 1")
        morning_enabled = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE receive_evening = 1")
        evening_enabled = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE receive_random = 1")
        random_enabled = c.fetchone()[0]
        conn.close()
        
        text = f"""
📊 **إحصائيات البوت**

👥 **المستخدمين:**
• الإجمالي: {len(users)}
• النشطين: {len(active_users)}
• غير النشطين: {len(users) - len(active_users)}

🔔 **التذكيرات:**
• مفعل الصباح: {morning_enabled}
• مفعل المساء: {evening_enabled}
• مفعل العشوائي: {random_enabled}

📅 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await query.edit_message_text(text, parse_mode="Markdown")
    
    elif query.data == "owner_users":
        if user_id != OWNER_ID:
            await query.edit_message_text("⛔ هذا الأمر مخصص للمالك فقط!")
            return
        
        users = get_all_users()
        text = "📋 **قائمة المستخدمين (آخر 20):**\n\n"
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT user_id, username, first_name, registered_at, active FROM users ORDER BY registered_at DESC LIMIT 20")
        results = c.fetchall()
        conn.close()
        
        for i, (uid, username, first_name, reg_date, active) in enumerate(results, 1):
            status = "🟢" if active else "🔴"
            name = first_name or "مستخدم"
            username_str = f"(@{username})" if username else ""
            text += f"{i}. {status} {name} {username_str} - {uid}\n"
        
        if len(results) == 0:
            text += "لا يوجد مستخدمين حتى الآن"
        else:
            text += f"\n📌 إجمالي المستخدمين: {len(users)}"
        
        await query.edit_message_text(text[:4000], parse_mode="Markdown")
    
    elif query.data == "owner_backup":
        # إنشاء نسخة احتياطية
        if user_id != OWNER_ID:
            await query.edit_message_text("⛔ هذا الأمر مخصص للمالك فقط!")
            return
        
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        try:
            conn = sqlite3.connect(DB_NAME)
            with sqlite3.connect(backup_file) as backup:
                conn.backup(backup)
            conn.close()
            
            await query.edit_message_text(
                f"✅ **تم إنشاء النسخة الاحتياطية**\n\n"
                f"📁 الملف: {backup_file}\n"
                f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            await query.edit_message_text(f"❌ فشل إنشاء النسخة الاحتياطية: {e}")

# ============================================
# القسم 8: أوامر البوت المباشرة
# ============================================

async def morning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🌅 **أذكار الصباح**\n\n" + "\n\n".join(MORNING_ADHKAR)
    await update.message.reply_text(text, parse_mode="Markdown")

async def evening_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🌙 **أذكار المساء**\n\n" + "\n\n".join(EVENING_ADHKAR)
    await update.message.reply_text(text, parse_mode="Markdown")

async def deeds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "⭐ **أعمال اليوم الصالحة**\n\n" + "\n\n".join(GOOD_DEEDS)
    await update.message.reply_text(text, parse_mode="Markdown")

async def sleep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🌙 **أذكار النوم**\n\n" + "\n\n".join(SLEEP_ADHKAR)
    await update.message.reply_text(text, parse_mode="Markdown")

async def wake_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "☀️ **أذكار الاستيقاظ**\n\n" + "\n\n".join(WAKE_ADHKAR)
    await update.message.reply_text(text, parse_mode="Markdown")

async def prayer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🕌 **أذكار بعد الصلاة**\n\n" + "\n\n".join(POST_PRAYER_ADHKAR)
    await update.message.reply_text(text, parse_mode="Markdown")

async def dua_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🤲 **دعاء اليوم**\n\n" + "\n\n".join(DAILY_DUA)
    await update.message.reply_text(text, parse_mode="Markdown")

async def prayertimes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    country, city = get_user_city(user_id)
    
    if not city:
        await update.message.reply_text(
            "⚠️ **لم تختر مدينتك بعد!**\n\n"
            "استخدم الأمر /setcity أو اضغط على زر '🌍 اختيار المدينة'",
            parse_mode="Markdown"
        )
        return
    
    times = await get_prayer_times(city, country)
    
    if not times:
        await update.message.reply_text(
            "❌ عذراً، حدث خطأ في جلب المواقيت.\n"
            "تأكد من اسم المدينة أو حاول مرة أخرى."
        )
        return
    
    text = f"🕌 **مواقيت الصلاة في {city}**\n\n"
    for name, time in times.items():
        text += f"• {name}: {time}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def setcity_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار المدينة عن طريق الكتابة"""
    if not context.args:
        await update.message.reply_text(
            "📝 **اختر مدينتك:**\n\n"
            "استخدم الأمر: `/setcity [اسم المدينة] [الدولة]`\n\n"
            "مثال: `/setcity الرياض السعودية`\n"
            "أو اضغط على زر '🌍 اختيار المدينة'",
            parse_mode="Markdown"
        )
        return
    
    if len(context.args) >= 1:
        city = context.args[0]
        country = context.args[1] if len(context.args) > 1 else "Saudi Arabia"
        
        save_user_city(update.effective_user.id, country, city)
        
        await update.message.reply_text(
            f"✅ **تم حفظ مدينتك بنجاح!**\n\n"
            f"🌍 البلد: {country}\n"
            f"🏙️ المدينة: {city}\n\n"
            f"يمكنك استخدام /prayertimes لمعرفة مواقيت الصلاة",
            parse_mode="Markdown"
        )

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT active FROM users WHERE user_id = ?", (user_id,))
    current = c.fetchone()
    
    if current and current[0] == 1:
        toggle_user_active(user_id, 0)
        await update.message.reply_text(
            "✅ **تم إيقاف التذكير مؤقتاً**\n\n"
            "لإعادة التفعيل، اضغط /start مرة أخرى"
        )
    else:
        toggle_user_active(user_id, 1)
        await update.message.reply_text(
            "✅ **تم تفعيل التذكير**\n\n"
            "ستصلك التذكيرات في الأوقات المحددة"
        )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء أي عملية جارية"""
    context.user_data.clear()
    await update.message.reply_text(
        "✅ تم إلغاء العملية",
        reply_markup=get_main_keyboard()
    )

async def owner_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم المالك"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ هذا الأمر مخصص للمالك فقط!")
        return
    
    await update.message.reply_text(
        "🛠️ **لوحة تحكم المالك**\n\n"
        "اختر الإجراء الذي تريد القيام به:",
        reply_markup=get_owner_keyboard(),
        parse_mode="Markdown"
    )

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة البث الجماعي"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("⛔ هذا الأمر مخصص للمالك فقط!")
        return
    
    if not context.user_data.get("broadcast_mode"):
        return
    
    # إلغاء وضع البث
    context.user_data["broadcast_mode"] = False
    
    # الحصول على جميع المستخدمين
    users = get_all_users()
    
    if not users:
        await update.message.reply_text("⚠️ لا يوجد مستخدمين لإرسال الرسالة لهم")
        return
    
    # إرسال رسالة التحميل
    loading_msg = await update.message.reply_text(f"⏳ جاري إرسال الرسالة إلى {len(users)} مستخدم...")
    
    success = 0
    failed = 0
    failed_users = []
    
    # إرسال الرسالة للجميع
    for user_id in users:
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
            success += 1
            await asyncio.sleep(0.05)  # تجنب الحظر
        except Exception as e:
            failed += 1
            failed_users.append(user_id)
            logger.error(f"فشل إرسال الرسالة للمستخدم {user_id}: {e}")
    
    # تحديث رسالة التحميل
    await loading_msg.edit_text(
        f"📢 **تم إرسال البث الجماعي**\n\n"
        f"✅ تم الإرسال بنجاح: {success}\n"
        f"❌ فشل الإرسال: {failed}\n"
        f"👥 إجمالي المستخدمين: {len(users)}\n\n"
        f"📊 نسبة النجاح: {round((success/len(users))*100, 2)}%"
    )
    
    # إذا فشل بعض المستخدمين، أرسل قائمة بهم
    if failed > 0 and failed_users:
        failed_text = f"❌ المستخدمين الذين فشل الإرسال لهم:\n"
        for uid in failed_users[:10]:
            failed_text += f"• {uid}\n"
        if len(failed_users) > 10:
            failed_text += f"\nو {len(failed_users) - 10} مستخدمين آخرين..."
        
        await update.message.reply_text(failed_text[:4000])

async def test_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر اختبار التذكيرات (للمالك فقط)"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ هذا الأمر مخصص للمالك فقط!")
        return
    
    await update.message.reply_text("⏳ جاري إرسال تذكير اختباري...")
    
    # إرسال تذكير الصباح
    await send_morning_reminder(context.bot)
    await asyncio.sleep(1)
    
    # إرسال تذكير المساء
    await send_evening_reminder(context.bot)
    await asyncio.sleep(1)
    
    # إرسال تذكير عشوائي
    await send_random_reminder(context.bot)
    
    await update.message.reply_text("✅ تم إرسال جميع التذكيرات الاختبارية")

# ============================================
# القسم 9: التذكيرات التلقائية (مصححة)
# ============================================

def generate_random_times():
    """توليد 2-3 أوقات عشوائية في اليوم"""
    times = []
    num_times = random.randint(2, 3)
    
    # أوقات محتملة بين 9 صباحاً و 11 مساءً
    possible_hours = list(range(9, 23))
    random.shuffle(possible_hours)
    
    for i in range(num_times):
        hour = possible_hours[i]
        minute = random.randint(0, 59)
        times.append((hour, minute))
    
    return sorted(times)

async def send_morning_reminder(app):
    """إرسال تذكير الصباح"""
    users = get_all_active_users()
    if not users:
        logger.info("⚠️ لا يوجد مستخدمين نشطين لتذكير الصباح")
        return
    
    logger.info(f"🌅 جاري إرسال تذكير الصباح لـ {len(users)} مستخدم")
    
    # التحقق من إعدادات كل مستخدم
    for user_id in users:
        receive_morning, _, _ = get_user_settings(user_id)
        if not receive_morning:
            continue
        
        text = f"""
🌅 **تذكير الصباح - ذكرني**

**☀️ أذكار الصباح:**
{chr(10).join(MORNING_ADHKAR[:5])}

💡 {random.choice(MOTIVATIONAL_MESSAGES)}

🤲 نسأل الله أن يبارك يومك
"""
        try:
            await app.send_message(user_id, text, parse_mode="Markdown")
            await asyncio.sleep(0.1)
            logger.info(f"✅ تم إرسال تذكير الصباح للمستخدم {user_id}")
        except Exception as e:
            logger.error(f"❌ فشل إرسال تذكير الصباح للمستخدم {user_id}: {e}")

async def send_evening_reminder(app):
    """إرسال تذكير المساء"""
    users = get_all_active_users()
    if not users:
        logger.info("⚠️ لا يوجد مستخدمين نشطين لتذكير المساء")
        return
    
    logger.info(f"🌙 جاري إرسال تذكير المساء لـ {len(users)} مستخدم")
    
    for user_id in users:
        _, receive_evening, _ = get_user_settings(user_id)
        if not receive_evening:
            continue
        
        text = f"""
🌙 **تذكير المساء - ذكرني**

**🌙 أذكار المساء:**
{chr(10).join(EVENING_ADHKAR[:5])}

💡 {random.choice(MOTIVATIONAL_MESSAGES)}

🤲 نسأل الله أن يحفظك في ليلك
"""
        try:
            await app.send_message(user_id, text, parse_mode="Markdown")
            await asyncio.sleep(0.1)
            logger.info(f"✅ تم إرسال تذكير المساء للمستخدم {user_id}")
        except Exception as e:
            logger.error(f"❌ فشل إرسال تذكير المساء للمستخدم {user_id}: {e}")

async def send_random_reminder(app):
    """إرسال تذكير عشوائي"""
    users = get_all_active_users()
    if not users:
        return
    
    # اختيار نوع الرسالة العشوائية
    message_type = random.choice(["palestine", "motivation", "deed"])
    
    if message_type == "palestine":
        content = random.choice(PALESTINE_DUAS)
        title = "🇵🇸 تذكير - ذكرني"
    elif message_type == "motivation":
        content = random.choice(MOTIVATIONAL_MESSAGES)
        title = "💚 تذكير - ذكرني"
    else:
        content = random.choice(GOOD_DEEDS)
        title = "⭐ تذكير - ذكرني"
    
    text = f"""
**{title}**

{content}

📌 *لا تنسَ ذكر الله في كل لحظة*
"""
    
    logger.info(f"🎲 جاري إرسال تذكير عشوائي لـ {len(users)} مستخدم (نوع: {message_type})")
    
    for user_id in users:
        _, _, receive_random = get_user_settings(user_id)
        if not receive_random:
            continue
        
        try:
            await app.send_message(user_id, text, parse_mode="Markdown")
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"❌ فشل إرسال تذكير عشوائي للمستخدم {user_id}: {e}")

# ===== وظائف التذكير المتوافقة مع BackgroundScheduler =====
def morning_reminder_job(app):
    """وظيفة متوافقة مع BackgroundScheduler"""
    try:
        # إنشاء event loop جديد في هذا الخيط
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_morning_reminder(app))
        loop.close()
    except Exception as e:
        logger.error(f"❌ خطأ في تذكير الصباح: {e}")

def evening_reminder_job(app):
    """وظيفة متوافقة مع BackgroundScheduler"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_evening_reminder(app))
        loop.close()
    except Exception as e:
        logger.error(f"❌ خطأ في تذكير المساء: {e}")

def random_reminder_job(app):
    """وظيفة متوافقة مع BackgroundScheduler"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_random_reminder(app))
        loop.close()
    except Exception as e:
        logger.error(f"❌ خطأ في التذكير العشوائي: {e}")

def schedule_random_reminders(app):
    """جدولة التذكيرات العشوائية بشكل يومي"""
    # توليد أوقات عشوائية جديدة كل يوم
    random_times = generate_random_times()
    
    scheduler = BackgroundScheduler(timezone=pytz.timezone(TIMEZONE))
    
    # إضافة التذكيرات العشوائية
    for hour, minute in random_times:
        scheduler.add_job(
            random_reminder_job,
            CronTrigger(hour=hour, minute=minute),
            args=[app],
            id=f"random_{hour}_{minute}"
        )
        logger.info(f"⏰ تم جدولة تذكير عشوائي في {hour}:{minute:02d}")
    
    return scheduler

def start_scheduler(app):
    """تشغيل المجدول"""
    # إنشاء المجدول الرئيسي
    scheduler = BackgroundScheduler(timezone=pytz.timezone(TIMEZONE))
    
    # تذكير الصباح
    scheduler.add_job(
        morning_reminder_job,
        CronTrigger(hour=MORNING_HOUR, minute=MORNING_MINUTE),
        args=[app],
        id="morning_reminder"
    )
    logger.info(f"⏰ تذكير الصباح: {MORNING_HOUR}:{MORNING_MINUTE:02d}")
    
    # تذكير المساء
    scheduler.add_job(
        evening_reminder_job,
        CronTrigger(hour=EVENING_HOUR, minute=EVENING_MINUTE),
        args=[app],
        id="evening_reminder"
    )
    logger.info(f"⏰ تذكير المساء: {EVENING_HOUR}:{EVENING_MINUTE:02d}")
    
    # تشغيل المجدول
    scheduler.start()
    
    # جدولة التذكيرات العشوائية (تُجدَّد يومياً)
    random_scheduler = schedule_random_reminders(app)
    random_scheduler.start()
    
    # تجديد التذكيرات العشوائية كل يوم عند منتصف الليل
    scheduler.add_job(
        lambda: refresh_random_reminders(app, random_scheduler),
        CronTrigger(hour=0, minute=1),
        id="refresh_random"
    )
    
    return scheduler

def refresh_random_reminders(app, old_scheduler):
    """تجديد التذكيرات العشوائية كل يوم"""
    logger.info("🔄 تجديد التذكيرات العشوائية...")
    try:
        old_scheduler.shutdown()
    except:
        pass
    new_scheduler = schedule_random_reminders(app)
    new_scheduler.start()
    return new_scheduler

# ============================================
# القسم 10: التشغيل الرئيسي
# ============================================

def main():
    """الوظيفة الرئيسية لتشغيل البوت"""
    # تهيئة قاعدة البيانات
    init_db()
    
    # إنشاء التطبيق
    app = Application.builder().token(TOKEN).build()
    
    # ===== إضافة معالجات الأوامر =====
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("morning", morning_command))
    app.add_handler(CommandHandler("evening", evening_command))
    app.add_handler(CommandHandler("deeds", deeds_command))
    app.add_handler(CommandHandler("sleep", sleep_command))
    app.add_handler(CommandHandler("wake", wake_command))
    app.add_handler(CommandHandler("prayer", prayer_command))
    app.add_handler(CommandHandler("dua", dua_command))
    app.add_handler(CommandHandler("prayertimes", prayertimes_command))
    app.add_handler(CommandHandler("setcity", setcity_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("owner", owner_panel))
    app.add_handler(CommandHandler("test", test_reminder))  # أمر الاختبار
    
    # ===== معالج الأزرار =====
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # ===== معالج البث الجماعي =====
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_broadcast))
    
    # ===== تشغيل المجدول =====
    scheduler = start_scheduler(app.bot)
    
    # ===== تشغيل البوت =====
    logger.info("🤖 بوت ذكرني يعمل الآن...")
    logger.info(f"⏰ أوقات التذكير:")
    logger.info(f"   🌅 الصباح: {MORNING_HOUR}:{MORNING_MINUTE:02d}")
    logger.info(f"   🌙 المساء: {EVENING_HOUR}:{EVENING_MINUTE:02d}")
    logger.info(f"   🎲 عشوائي: 2-3 مرات يومياً")
    logger.info("📢 للاختبار الفوري استخدم الأمر /test")
    
    try:
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("🛑 تم إيقاف البوت")
        scheduler.shutdown()

if __name__ == "__main__":
    main()
