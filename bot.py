from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

import sqlite3
import random
from datetime import datetime

# =====================================
# تنظیمات
# =====================================

TOKEN = "8681136841:AAHTqbHehB5DwCrRQ17CwRa-YqAIxYL5OUo"

ADMIN_ID = 8422742448

CARD_NUMBER = "6219861991961367"
CARD_NAME = "زینت ترکی انار"

SUPPORT_ID = "@Sso_R_rY"

CHANNEL_USERNAME = "@AKZ_off"

# =====================================
# دیتابیس
# =====================================

db = sqlite3.connect(
    "vpn_bot.db",
    check_same_thread=False
)

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    join_date TEXT,
    is_agent INTEGER DEFAULT 0
)
""")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_agent INTEGER DEFAULT 0")
except:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT,
    user_id INTEGER,
    order_type TEXT,
    users_count INTEGER,
    months INTEGER,
    qty INTEGER DEFAULT 1,
    price INTEGER,
    status TEXT,
    link TEXT,
    created_at TEXT
)
""")

try:
    cursor.execute("ALTER TABLE orders ADD COLUMN order_code TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE orders ADD COLUMN qty INTEGER DEFAULT 1")
except:
    pass

try:
    cursor.execute("ALTER TABLE orders ADD COLUMN users_count INTEGER")
except:
    pass

try:
    cursor.execute("ALTER TABLE orders ADD COLUMN months INTEGER")
except:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")
cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('shop_status', 'open')")

db.commit()

# =====================================
# توابع کمکی دیتابیس
# =====================================

def is_shop_open():
    cursor.execute("SELECT value FROM settings WHERE key = 'shop_status'")
    result = cursor.fetchone()
    return True if result and result[0] == 'open' else False

def is_agent(uid):
    cursor.execute("SELECT is_agent FROM users WHERE user_id = ?", (uid,))
    result = cursor.fetchone()
    return True if result and result[0] == 1 else False

# =====================================
# سیستم قیمت‌گذاری جدید
# =====================================

def calculate_price(service_type, is_agent_user, users_count, months):
    """
    محاسبه قیمت بر اساس:
    - service_type: "normal" یا "vip"
    - is_agent_user: True/False
    - users_count: تعداد کاربر (هر عددی)
    - months: تعداد ماه (هر عددی)
    
    قیمت برای تانل عادی (بدون نمایندگی):
    - 1 کاربر: 360,000 (1ماه), 580,000 (2ماه), 810,000 (3ماه)
    - 2 کاربر: 590,000 (1ماه), 1,100,000 (2ماه), 1,500,000 (3ماه)
    
    قیمت برای تانل VIP (بدون نمایندگی):
    - 1 کاربر: 460,000 (1ماه), 790,000 (2ماه)
    - 2 کاربر: 790,000 (1ماه), 1,410,000 (2ماه)
    
    قیمت برای تانل عادی (نمایندگی):
    - 1 کاربر: 285,000 (1ماه), 515,000 (2ماه), 735,000 (3ماه)
    - 2 کاربر: 515,000 (1ماه), 935,000 (2ماه), 1,425,000 (3ماه)
    
    قیمت برای تانل VIP (نمایندگی):
    - 1 کاربر: 385,000 (1ماه), 715,000 (2ماه)
    - 2 کاربر: 715,000 (1ماه), 1,335,000 (2ماه)
    """
    
    # تانل عادی (بدون نمایندگی)
    if service_type == "normal" and not is_agent_user:
        if users_count == 1:
            if months == 1: return 360000
            elif months == 2: return 580000
            elif months == 3: return 810000
            # محاسبه دلخواه برای 1 کاربر عادی
            # قیمت پایه: 360,000 برای 1 ماه
            else:
                base_per_month = 360000
                return base_per_month * months
        elif users_count == 2:
            if months == 1: return 590000
            elif months == 2: return 1100000
            elif months == 3: return 1500000
            # محاسبه دلخواه برای 2 کاربر عادی
            # قیمت پایه: 590,000 برای 1 ماه
            else:
                base_per_month = 590000
                return base_per_month * months
        else:
            # برای تعداد کاربر دلخواه (بیش از 2)
            # قیمت برای کاربر اول: 360,000 برای 1 ماه
            # قیمت برای هر کاربر اضافی: 230,000 برای 1 ماه (590,000 - 360,000 = 230,000)
            price_first_user = 360000
            price_additional_user = 230000
            base_per_month = price_first_user + (price_additional_user * (users_count - 1))
            return base_per_month * months
    
    # تانل VIP (بدون نمایندگی)
    elif service_type == "vip" and not is_agent_user:
        if users_count == 1:
            if months == 1: return 460000
            elif months == 2: return 790000
            # محاسبه دلخواه برای 1 کاربر VIP
            else:
                base_per_month = 460000
                return base_per_month * months
        elif users_count == 2:
            if months == 1: return 790000
            elif months == 2: return 1410000
            # محاسبه دلخواه برای 2 کاربر VIP
            else:
                base_per_month = 790000
                return base_per_month * months
        else:
            # برای تعداد کاربر دلخواه (بیش از 2)
            # قیمت برای کاربر اول: 460,000 برای 1 ماه
            # قیمت برای هر کاربر اضافی: 330,000 برای 1 ماه (790,000 - 460,000 = 330,000)
            price_first_user = 460000
            price_additional_user = 330000
            base_per_month = price_first_user + (price_additional_user * (users_count - 1))
            return base_per_month * months
    
    # تانل عادی (نمایندگی)
    elif service_type == "normal" and is_agent_user:
        if users_count == 1:
            if months == 1: return 285000
            elif months == 2: return 515000
            # محاسبه دلخواه برای 1 کاربر عادی (نمایندگی)
            else:
                base_per_month = 285000
                return base_per_month * months
        elif users_count == 2:
            if months == 1: return 515000
            elif months == 2: return 935000
            # محاسبه دلخواه برای 2 کاربر عادی (نمایندگی)
            else:
                base_per_month = 515000
                return base_per_month * months
        else:
            # برای تعداد کاربر دلخواه (بیش از 2)
            # قیمت برای کاربر اول: 285,000 برای 1 ماه
            # قیمت برای هر کاربر اضافی: 230,000 برای 1 ماه (515,000 - 285,000 = 230,000)
            price_first_user = 285000
            price_additional_user = 230000
            base_per_month = price_first_user + (price_additional_user * (users_count - 1))
            return base_per_month * months
    
    # تانل VIP (نمایندگی)
    elif service_type == "vip" and is_agent_user:
        if users_count == 1:
            if months == 1: return 385000
            elif months == 2: return 715000
            # محاسبه دلخواه برای 1 کاربر VIP (نمایندگی)
            else:
                base_per_month = 385000
                return base_per_month * months
        elif users_count == 2:
            if months == 1: return 715000
            elif months == 2: return 1335000
            # محاسبه دلخواه برای 2 کاربر VIP (نمایندگی)
            else:
                base_per_month = 715000
                return base_per_month * months
        else:
            # برای تعداد کاربر دلخواه (بیش از 2)
            # قیمت برای کاربر اول: 385,000 برای 1 ماه
            # قیمت برای هر کاربر اضافی: 330,000 برای 1 ماه (715,000 - 385,000 = 330,000)
            price_first_user = 385000
            price_additional_user = 330000
            base_per_month = price_first_user + (price_additional_user * (users_count - 1))
            return base_per_month * months
    
    return 0

# =====================================
# حافظه موقت
# =====================================

user_state = {}
user_data = {}
admin_state = {}

# سیستم ارسال چند مرحله ای برای ادمین
admin_multi_delivery = {} 

# =====================================
# کیبورد ها
# =====================================

main_keyboard = ReplyKeyboardMarkup(
    [
        ["♻️ تمدید", "💰 خرید"],
        ["👤 حساب من", "🤝 درخواست نمایندگی"],
        ["📞 پشتیبانی"]
    ],
    resize_keyboard=True
)

admin_keyboard = ReplyKeyboardMarkup(
    [
        ["📦 فروش تا این لحظه", "♻️ تمدید تا این لحظه"],
        ["👤 کاربران بدون خرید"],
        ["🔴 بستن فروش", "🟢 باز کردن فروش"]
    ],
    resize_keyboard=True
)

# =====================================
# فرمت مبلغ
# =====================================

def format_price(amount):
    amount = int(amount)
    if amount >= 1000000:
        million = amount // 1000000
        thousand = (amount % 1000000) // 1000
        if thousand == 0:
            return f"{million} میلیون تومان"
        return f"{million} میلیون و {thousand} هزار تومان"

    if amount >= 1000:
        thousand = amount // 1000
        remain = amount % 1000
        if remain == 0:
            return f"{thousand} هزار تومان"
        return f"{thousand} هزار و {remain} تومان"

    return f"{amount} تومان"

def generate_order_code():
    now = datetime.now().strftime("%Y%m%d")
    rand = random.randint(1000, 9999)
    return f"AKZ-{now}-{rand}"

# =====================================
# عضویت کانال
# =====================================

async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except:
        return False

def register_user(uid):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, join_date, is_agent) VALUES (?, ?, ?)",
            (uid, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0))
        db.commit()

# =====================================
# آمار و گزارشات
# =====================================

def customer_analysis(uid):
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND status = 'success'", (uid,))
    success = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND status = 'reject'", (uid,))
    reject = cursor.fetchone()[0]
    return f"👤 آنالیز مشتری\n\n🆔 آیدی:\n{uid}\n\n✅ سفارش موفق:\n{success}\n\n❌ سفارش رد شده:\n{reject}"

def sales_stats():
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(price),0) FROM orders WHERE order_type = 'buy' AND status = 'success'")
    data = cursor.fetchone()
    return f"📦 آمار فروش\n\n✅ تعداد فروش موفق:\n{data[0]}\n\n💰 مجموع فروش:\n{format_price(data[1])}"

def renew_stats():
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(price),0) FROM orders WHERE order_type = 'renew' AND status = 'success'")
    data = cursor.fetchone()
    return f"♻️ آمار تمدید\n\n✅ تعداد تمدید موفق:\n{data[0]}\n\n💰 مجموع تمدید:\n{format_price(data[1])}"

def users_without_orders():
    cursor.execute("SELECT user_id FROM users WHERE user_id NOT IN (SELECT DISTINCT user_id FROM orders)")
    users = cursor.fetchall()
    if not users: return "✅ همه کاربران خرید یا تمدید داشتن"
    text = "👤 کاربران بدون خرید:\n\n"
    for user in users: text += f"{user[0]}\n"
    return text

# =====================================
# کیبوردهای سازنده بخش خرید
# =====================================

def get_service_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 تانل عادی", callback_data="buy_srv_normal")],
        [InlineKeyboardButton("👑 تانل VIP", callback_data="buy_srv_vip")],
        [InlineKeyboardButton("💎 نمایندگی فروش", callback_data="buy_srv_agent")],
        [InlineKeyboardButton("❌ انصراف از خرید", callback_data="cancel_buy")]
    ])

def get_paytype_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 پرداخت نقدی", callback_data="buy_payt_cash")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_srv")],
        [InlineKeyboardButton("❌ انصراف از خرید", callback_data="cancel_buy")]
    ])

def get_paymethod_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 کارت به کارت", callback_data="buy_paym_card")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_payt")],
        [InlineKeyboardButton("❌ انصراف از خرید", callback_data="cancel_buy")]
    ])

def get_discount_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏷 بدون کد تخفیف", callback_data="buy_disc_no")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_paym")],
        [InlineKeyboardButton("❌ انصراف از خرید", callback_data="cancel_buy")]
    ])

def get_users_count_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ یک کاربر", callback_data="buy_users_1")],
        [InlineKeyboardButton("2️⃣ دو کاربر", callback_data="buy_users_2")],
        [InlineKeyboardButton("📦 تعداد دلخواه", callback_data="buy_custom_users")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_disc")],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_buy")]
    ])

def get_months_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ یک ماهه", callback_data="buy_months_1")],
        [InlineKeyboardButton("2️⃣ دو ماهه", callback_data="buy_months_2")],
        [InlineKeyboardButton("3️⃣ سه ماهه", callback_data="buy_months_3")],
        [InlineKeyboardButton("📦 ماه دلخواه", callback_data="buy_custom_months")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_users")],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_buy")]
    ])

def get_invoice_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید و ادامه", callback_data="buy_confirm")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_months")],
        [InlineKeyboardButton("❌ انصراف از خرید", callback_data="cancel_buy")]
    ])

# =====================================
# استارت و بخش های اصلی
# =====================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    register_user(uid)
    member = await check_membership(uid, context)

    if not member:
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
            [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_join")]
        ]
        return await update.message.reply_text("❌ ابتدا داخل کانال عضو شو سپس روی بررسی عضویت بزن", reply_markup=InlineKeyboardMarkup(keyboard))

    user_state[uid] = "MENU"
    user_data.pop(uid, None)

    if uid == ADMIN_ID:
        return await update.message.reply_text("👑 پنل مدیریت فعال شد", reply_markup=admin_keyboard)

    await update.message.reply_text("سلام 😄\nبه Akz VPN خوش اومدی\n\nاز منوی پایین انتخاب کن 👇", reply_markup=main_keyboard)

async def start_buy_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, from_query=False):
    uid = update.effective_user.id
    user_data[uid] = {"type": "buy", "service": None, "users_count": 0, "months": 0, "discount": "ندارد", "price": 0}
    text = "🛍 بخش خرید\n\nلطفاً نوع سرویس مورد نظر خود را انتخاب کنید:"
    
    if from_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_service_menu())
    else:
        await update.message.reply_text(text, reply_markup=get_service_menu())

# =====================================
# دکمه های شیشه ای (مسیر خرید)
# =====================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    # --- متفرقه ---
    if data == "check_join":
        member = await check_membership(uid, context)
        if member: return await query.message.reply_text("✅ عضویت تایید شد", reply_markup=admin_keyboard if uid == ADMIN_ID else main_keyboard)
        return await query.message.reply_text("❌ هنوز عضو کانال نشدی")

    if data == "cancel_all" or data == "cancel_buy":
        user_state[uid] = "MENU"
        user_data.pop(uid, None)
        return await query.edit_message_text("❌ عملیات لغو شد.")

    # =================================
    # مسیر خرید
    # =================================
    if uid not in user_data:
        user_data[uid] = {"type": "buy", "discount": "ندارد"}

    # 1. انتخاب سرویس
    if data == "back_to_srv":
        await query.edit_message_text("🛍 بخش خرید\n\nلطفاً نوع سرویس مورد نظر خود را انتخاب کنید:", reply_markup=get_service_menu())
        return

    if data == "buy_srv_vip":
        user_data[uid]["service"] = "vip"
        await query.edit_message_text("👑 سرویس انتخابی: تانل VIP\n🌟 جوابگویی روی تمامی نت ها\n\nنوع پرداخت رو انتخاب کنید:", reply_markup=get_paytype_menu())
        return

    if data == "buy_srv_agent":
        if not is_agent(uid):
            return await query.answer(text="❌ شما نماینده نیستید! ابتدا از منوی اصلی درخواست نمایندگی دهید.", show_alert=True)
        user_data[uid]["service"] = "agent"
        await query.edit_message_text("💎 سرویس انتخابی: نمایندگی فروش\n\nنوع پرداخت رو انتخاب کنید:", reply_markup=get_paytype_menu())
        return

    if data == "buy_srv_normal":
        user_data[uid]["service"] = "normal"
        await query.edit_message_text("🌐 سرویس انتخابی: تانل عادی\n\nنوع پرداخت رو انتخاب کنید:", reply_markup=get_paytype_menu())
        return

    # 2. نوع پرداخت
    if data == "back_to_payt":
        srv_map = {"normal": "تانل عادی 🌐", "vip": "تانل VIP 👑", "agent": "نمایندگی فروش 💎"}
        srv = srv_map.get(user_data[uid].get("service"), "")
        await query.edit_message_text(f"سرویس انتخابی: {srv}\n\nنوع پرداخت رو انتخاب کنید:", reply_markup=get_paytype_menu())
        return

    if data == "buy_payt_cash":
        await query.edit_message_text("💵 نوع پرداخت: نقدی\n\nروش پرداخت رو انتخاب کنید:", reply_markup=get_paymethod_menu())
        return

    # 3. روش پرداخت
    if data == "back_to_paym":
        await query.edit_message_text("💵 نوع پرداخت: نقدی\n\nروش پرداخت رو انتخاب کنید:", reply_markup=get_paymethod_menu())
        return

    if data == "buy_paym_card":
        user_state[uid] = "WAIT_BUY_DISCOUNT"
        await query.edit_message_text("💳 روش پرداخت: کارت به کارت\n\nاگر کد تخفیف دارید آن را بفرستید، در غیر این صورت روی 'بدون کد تخفیف' بزنید:", reply_markup=get_discount_menu())
        return

    # 4. کد تخفیف
    if data == "back_to_disc":
        user_state[uid] = "WAIT_BUY_DISCOUNT"
        await query.edit_message_text("💳 روش پرداخت: کارت به کارت\n\nاگر کد تخفیف دارید آن را بفرستید، در غیر این صورت روی 'بدون کد تخفیف' بزنید:", reply_markup=get_discount_menu())
        return

    if data == "buy_disc_no":
        user_data[uid]["discount"] = "ندارد"
        await query.edit_message_text("👤 تعداد کاربر رو انتخاب کنید:", reply_markup=get_users_count_menu())
        return

    # 5. تعداد کاربر
    if data == "back_to_users":
        await query.edit_message_text("👤 تعداد کاربر رو انتخاب کنید:", reply_markup=get_users_count_menu())
        return

    if data == "buy_custom_users":
        user_state[uid] = "WAIT_CUSTOM_USERS"
        await query.edit_message_text("📦 تعداد کاربر دلخواه رو بفرستید:\n\nمثال: 5")
        return

    if data.startswith("buy_users_"):
        users_count = int(data.split("_")[2])
        user_data[uid]["users_count"] = users_count
        await query.edit_message_text(f"⏱ مدت اشتراک رو انتخاب کنید:", reply_markup=get_months_menu())
        return

    # 6. مدت اشتراک
    if data == "back_to_months":
        # بازگشت به مرحله انتخاب تعداد کاربر
        await query.edit_message_text("👤 تعداد کاربر رو انتخاب کنید:", reply_markup=get_users_count_menu())
        return

    if data == "buy_custom_months":
        user_state[uid] = "WAIT_CUSTOM_MONTHS"
        await query.edit_message_text("📦 تعداد ماه دلخواه رو بفرستید:\n\nمثال: 3")
        return

    if data.startswith("buy_months_"):
        months = int(data.split("_")[2])
        user_data[uid]["months"] = months
        await generate_and_send_invoice(query, uid)
        return

    # 7. فاکتور و تایید
    if data == "buy_confirm":
        user_state[uid] = "WAIT_BUY_RECEIPT"
        
        text = f"""
✅ سفارش تایید شد. لطفاً مبلغ زیر را واریز کنید:

💳 شماره کارت:
`{CARD_NUMBER}`

👤 صاحب کارت:
{CARD_NAME}

💰 مبلغ قابل پرداخت:
`{format_price(user_data[uid]['price'])}`

📸 بعد از پرداخت، تصویر رسید (فیش) رو همینجا ارسال کن 😄
"""
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="cancel_buy")]]))
        return

    # =================================
    # مسیر تمدید
    # =================================
    if data == "back_renew":
        keyboard = [
            [InlineKeyboardButton("1️⃣ یک ماهه", callback_data="renew_1"), InlineKeyboardButton("2️⃣ دو ماهه", callback_data="renew_2")],
            [InlineKeyboardButton("3️⃣ سه ماهه", callback_data="renew_3")],
            [InlineKeyboardButton("📦 ماه دلخواه", callback_data="custom_renew")],
            [InlineKeyboardButton("❌ لغو سفارش", callback_data="cancel_all")]
        ]
        await query.edit_message_text("📦 مدت تمدید رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "custom_renew":
        user_state[uid] = "WAIT_CUSTOM_RENEW"
        await query.edit_message_text("📦 تعداد ماه دلخواه رو بفرستید\n\nمثال: 3")
        return

    if data.startswith("renew_"):
        months = int(data.split("_")[1])
        # برای تمدید از قیمت تک کاربر استفاده می‌کنیم (پیش‌فرض)
        pr = calculate_price("normal", is_agent(uid), 1, months)
        if uid not in user_data: user_data[uid] = {}
        user_data[uid]["type"] = "renew"
        user_data[uid]["months"] = months
        user_data[uid]["users_count"] = 1
        user_data[uid]["price"] = pr
        user_state[uid] = "WAIT_RENEW_RECEIPT"
        
        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_renew")], [InlineKeyboardButton("❌ لغو سفارش", callback_data="cancel_all")]]
        text = f"✅ تمدید انتخاب شد\n\n⏱ مدت:\n`{months} ماه`\n\n💰 مبلغ:\n`{format_price(pr)}`\n\n💳 شماره کارت:\n`{CARD_NUMBER}`\n👤 صاحب کارت:\n{CARD_NAME}\n\n📸 بعد از پرداخت، رسید رو ارسال کن 😄"
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # --- پنل مدیریت ---
    if data.startswith("approve_agent_"):
        target_uid = int(data.split("_")[2])
        cursor.execute("UPDATE users SET is_agent = 1 WHERE user_id = ?", (target_uid,))
        db.commit()
        await context.bot.send_message(chat_id=target_uid, text="🎉 درخواست نمایندگی شما تایید شد!")
        await query.edit_message_text(f"✅ نمایندگی کاربر {target_uid} تایید شد.")
        return

    if data.startswith("reject_agent_req_"):
        target_uid = int(data.split("_")[3])
        await context.bot.send_message(chat_id=target_uid, text="❌ متاسفانه درخواست نمایندگی شما رد شد.")
        await query.edit_message_text(f"❌ درخواست نمایندگی کاربر {target_uid} رد شد.")
        return

    if data.startswith("analysis_"):
        target = int(data.split("_")[1])
        await query.message.reply_text(customer_analysis(target))
        return

    if data.startswith("reject_"):
        target = int(data.split("_")[1])
        admin_state[uid] = {"action": "reject", "target": target}
        await query.message.reply_text("✍ متن رد سفارش رو ارسال کن:")
        return

# =====================================
# تابع سازنده پیش فاکتور
# =====================================
async def generate_and_send_invoice(query_or_msg, uid):
    data = user_data[uid]
    users_count = data.get("users_count", 1)
    months = data.get("months", 1)
    service = data.get("service", "normal")
    is_agent_user = is_agent(uid)
    
    # محاسبه قیمت
    total_price = calculate_price(service, is_agent_user, users_count, months)
    if total_price == 0:
        await query_or_msg.answer(text="❌ این ترکیب قیمتی موجود نیست!", show_alert=True)
        return
    
    user_data[uid]["price"] = total_price
    
    service_map = {
        "normal": "تانل عادی 🌐",
        "vip": "تانل VIP 👑",
        "agent": "نمایندگی فروش 💎"
    }
    service_name = service_map.get(service, "نامشخص")
    
    vip_badge = "\n🌟 جوابگویی روی تمامی نت ها" if service == "vip" else ""
    
    text = f"""
🧾 پیش فاکتور شما:

🔸 نوع سرویس: {service_name}{vip_badge}
🔸 تعداد کاربر: {users_count}
🔸 مدت اشتراک: {months} ماه
🔸 روش پرداخت: نقدی (کارت به کارت)
🔸 کد تخفیف: {data.get("discount", "ندارد")}
    
💰 قیمت نهایی: {format_price(total_price)}

✅ در صورت اطمینان، روی تایید و ادامه کلیک کنید."""

    reply_markup = get_invoice_menu()
    
    try:
        await query_or_msg.edit_message_text(text, reply_markup=reply_markup)
    except:
        await query_or_msg.reply_text(text, reply_markup=reply_markup)

# =====================================
# هندلر متون (Text Handler)
# =====================================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    state = user_state.get(uid, "MENU")

    if uid == ADMIN_ID:
        admin_action = admin_state.get(uid)
        if admin_action and admin_action["action"] == "reject":
            target = admin_action["target"]
            await context.bot.send_message(chat_id=target, text=f"❌ سفارش شما رد شد\n\n{text}")
            cursor.execute("UPDATE orders SET status = 'reject' WHERE user_id = ? AND status = 'pending'", (target,))
            db.commit()
            admin_state.pop(uid)
            return await update.message.reply_text("✅ پیام رد ارسال شد")

        if text == "📦 فروش تا این لحظه": return await update.message.reply_text(sales_stats())
        if text == "♻️ تمدید تا این لحظه": return await update.message.reply_text(renew_stats())
        if text == "👤 کاربران بدون خرید": return await update.message.reply_text(users_without_orders())
        if text == "🔴 بستن فروش":
            cursor.execute("UPDATE settings SET value = 'closed' WHERE key = 'shop_status'")
            db.commit()
            return await update.message.reply_text("🔴 فروش موقتاً بسته شد.")
        if text == "🟢 باز کردن فروش":
            cursor.execute("UPDATE settings SET value = 'open' WHERE key = 'shop_status'")
            db.commit()
            return await update.message.reply_text("🟢 فروش مجدداً باز شد.")

    if text == "💰 خرید":
        if not is_shop_open(): return await update.message.reply_text("⛔️ فروش موقتاً بسته است. لطفاً بعداً مجدداً تلاش کنید.")
        return await start_buy_flow(update, context, from_query=False)

    if text == "♻️ تمدید":
        if not is_shop_open(): return await update.message.reply_text("⛔️ فروش موقتاً بسته است.")
        user_state[uid] = "WAIT_RENEW_LINK"
        keyboard = [[InlineKeyboardButton("❌ لغو سفارش", callback_data="cancel_all")]]
        return await update.message.reply_text("🔗 لینک یا کانفیگ قبلی رو ارسال کن 😄", reply_markup=InlineKeyboardMarkup(keyboard))

    if text == "📞 پشتیبانی":
        return await update.message.reply_text(f"🆔 پشتیبانی:\n{SUPPORT_ID}")

    if text == "👤 حساب من":
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(price),0) FROM orders WHERE user_id = ? AND status = 'success'", (uid,))
        data = cursor.fetchone()
        agent_status = "فعال 💎" if is_agent(uid) else "عادی 👤"
        msg = f"👤 اطلاعات حساب شما:\n\nآیدی: {uid}\nوضعیت نمایندگی: {agent_status}\n\n✅ خریدهای موفق: {data[0]}\n💰 مجموع پرداخت: {format_price(data[1])}"
        return await update.message.reply_text(msg)

    if text == "🤝 درخواست نمایندگی":
        if is_agent(uid): return await update.message.reply_text("✅ شما در حال حاضر نماینده هستید!")
        user_state[uid] = "WAIT_AGENT_REQ"
        msg = "لطفاً اطلاعات زیر را ارسال کنید:\n- میزان فروش معمول\n- کانال یا پیج فروش\n- آیدی پشتیبانی"
        return await update.message.reply_text(msg)

    if state == "WAIT_AGENT_REQ":
        admin_text = f"🤝 درخواست نمایندگی جدید\n\n👤 کاربر: {uid}\n\n📝 توضیحات:\n{text}"
        keyboard = [[InlineKeyboardButton("✅ تایید", callback_data=f"approve_agent_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"reject_agent_req_{uid}")]]
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard))
        user_state[uid] = "MENU"
        return await update.message.reply_text("✅ درخواست شما برای مدیریت ارسال شد.", reply_markup=main_keyboard)

    # دریافت دستی کد تخفیف
    if state == "WAIT_BUY_DISCOUNT":
        user_data[uid]["discount"] = text
        await update.message.reply_text("✅ کد تخفیف اعمال شد.\n\n👤 تعداد کاربر رو انتخاب کنید:", reply_markup=get_users_count_menu())
        return

    # دریافت دستی تعداد کاربر
    if state == "WAIT_CUSTOM_USERS":
        if not text.isdigit(): return await update.message.reply_text("❌ فقط عدد انگلیسی ارسال کن")
        users_count = int(text)
        if users_count < 1: return await update.message.reply_text("❌ تعداد کاربر باید حداقل 1 باشد")
        
        user_data[uid]["users_count"] = users_count
        await update.message.reply_text(f"⏱ مدت اشتراک رو انتخاب کنید:", reply_markup=get_months_menu())
        return

    # دریافت دستی تعداد ماه
    if state == "WAIT_CUSTOM_MONTHS":
        if not text.isdigit(): return await update.message.reply_text("❌ فقط عدد انگلیسی ارسال کن")
        months = int(text)
        if months < 1: return await update.message.reply_text("❌ تعداد ماه باید حداقل 1 باشد")
        
        user_data[uid]["months"] = months
        await generate_and_send_invoice(update.message, uid)
        return

    # دریافت لینک برای تمدید
    if state == "WAIT_RENEW_LINK":
        user_data[uid] = {"type": "renew", "link": text}
        keyboard = [
            [InlineKeyboardButton("1️⃣ یک ماهه", callback_data="renew_1"), InlineKeyboardButton("2️⃣ دو ماهه", callback_data="renew_2")],
            [InlineKeyboardButton("3️⃣ سه ماهه", callback_data="renew_3")],
            [InlineKeyboardButton("📦 ماه دلخواه", callback_data="custom_renew")],
            [InlineKeyboardButton("❌ لغو سفارش", callback_data="cancel_all")]
        ]
        user_state[uid] = "WAIT_RENEW_GB"
        return await update.message.reply_text("📦 مدت تمدید رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

    if state == "WAIT_CUSTOM_RENEW":
        if not text.isdigit(): return await update.message.reply_text("❌ فقط عدد ارسال کن")
        months = int(text)
        if months < 1: return await update.message.reply_text("❌ تعداد ماه باید حداقل 1 باشد")
        
        pr = calculate_price("normal", is_agent(uid), 1, months)
        if pr == 0:
            return await update.message.reply_text("❌ این تعداد ماه موجود نیست")
        user_data[uid]["months"] = months
        user_data[uid]["price"] = pr
        user_state[uid] = "WAIT_RENEW_RECEIPT"
        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_renew")], [InlineKeyboardButton("❌ لغو سفارش", callback_data="cancel_all")]]
        text_msg = f"✅ تمدید انتخاب شد\n\n⏱ مدت:\n`{months} ماه`\n\n💰 مبلغ:\n`{format_price(pr)}`\n\n💳 شماره کارت:\n`{CARD_NUMBER}`\n👤 صاحب کارت:\n{CARD_NAME}\n\n📸 بعد از پرداخت، رسید رو ارسال کن 😄"
        return await update.message.reply_text(text_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# =====================================
# رسید و عکس
# =====================================

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = user_state.get(uid)

    if state not in ["WAIT_BUY_RECEIPT", "WAIT_RENEW_RECEIPT"]: return

    if update.message.photo: file_id = update.message.photo[-1].file_id
    elif update.message.document: file_id = update.message.document.file_id
    else: return

    data = user_data.get(uid)
    if not data: return

    order_code = generate_order_code()
    users_count = data.get("users_count", 1)
    months = data.get("months", 1)

    cursor.execute("""
    INSERT INTO orders (order_code, user_id, order_type, users_count, months, qty, price, status, link, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (order_code, uid, data["type"], users_count, months, 1, data["price"], "pending", data.get("link", "-"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()

    agent_tag = " 💎 (نماینده)" if is_agent(uid) else ""

    if data["type"] == "buy":
        caption = f"🛒 خرید جدید{agent_tag}\n\n🧾 سفارش: {order_code}\n👤 کاربر: {uid}\n👥 تعداد کاربر: {users_count}\n⏱ مدت: {months} ماه\n💰 مبلغ: {format_price(data['price'])}"
    else:
        caption = f"♻️ تمدید جدید\n\n🧾 سفارش: {order_code}\n👤 کاربر: {uid}\n🔗 لینک:\n`{data['link']}`\n⏱ مدت: {months} ماه\n💰 مبلغ: {format_price(data['price'])}"

    keyboard = [[InlineKeyboardButton("👤 آنالیز مشتری", callback_data=f"analysis_{uid}")], [InlineKeyboardButton("❌ رد سفارش", callback_data=f"reject_{uid}")]]

    await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    user_state[uid] = "MENU"
    await update.message.reply_text(f"✅ رسید شما ارسال شد\n\n🧾 کد سفارش:\n{order_code}\n\nبعد از تایید، اکانت برات ارسال میشه 😄", reply_markup=main_keyboard)

# =====================================
# تایید سفارش (پاسخ ادمین)
# =====================================

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not update.message.reply_to_message: return
    
    reply_caption = update.message.reply_to_message.caption
    if not reply_caption: return

    if not update.message.text:
        return await update.message.reply_text("❌ لطفاً لینک اکانت را به صورت متنی ارسال کنید.")

    lines = reply_caption.split("\n")
    uid = None
    order_code = None

    # خواندن اطلاعات از کپشن فیش
    for line in lines:
        if "👤 کاربر:" in line:
            uid = int(line.split(":")[1].strip())
        elif "🧾 سفارش:" in line:
            order_code = line.split(":")[1].strip()

    if not uid or not order_code: return

    # ارسال اکانت برای کاربر
    await context.bot.send_message(
        chat_id=uid, 
        text=f"✅ سفارش شما تایید شد 😄\n\n🔗 اکانت شما:\n\n`{update.message.text}`\n\nممنون از خرید شما ❤️", 
        parse_mode="Markdown"
    )
    cursor.execute("UPDATE orders SET status = 'success' WHERE order_code = ?", (order_code,))
    db.commit()
    
    await update.message.reply_text("✅ اکانت برای مشتری ارسال شد")

# =====================================
# اجرا
# =====================================

app = (ApplicationBuilder().token(TOKEN).connect_timeout(30).read_timeout(30).write_timeout(30).pool_timeout(30).build())

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, admin_reply))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, photo_handler))
app.add_handler(MessageHandler(filters.TEXT, text_handler))

print("Bot is running 😄")
app.run_polling(drop_pending_updates=True)
