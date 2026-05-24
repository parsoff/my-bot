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
    gb INTEGER,
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
# حافظه موقت
# =====================================

user_state = {}
user_data = {}
admin_state = {}

# سیستم ارسال چند مرحله ای برای ادمین
# فرمت: {order_code: {"uid": user_id, "qty": qty, "gb": gb, "links": []}}
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
# فرمت مبلغ و قیمت گذاری
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

def price(gb):
    gb = int(gb)
    base = {1: 150000, 2: 300000, 3: 410000, 4: 550000, 5: 680000}
    if gb in base: return base[gb]
    return int(gb * 150000 * 0.9)

def agent_price(gb):
    gb = int(gb)
    base = {1: 100000, 2: 190000, 3: 270000, 4: 340000, 5: 400000}
    if gb in base: return base[gb]
    return int(gb * 75000)

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

def get_gb_menu(back_target="back_to_disc"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1GB", callback_data="buy_gb_1"), InlineKeyboardButton("2GB", callback_data="buy_gb_2")],
        [InlineKeyboardButton("3GB", callback_data="buy_gb_3"), InlineKeyboardButton("4GB", callback_data="buy_gb_4")],
        [InlineKeyboardButton("5GB", callback_data="buy_gb_5")],
        [InlineKeyboardButton("📦 حجم دلخواه", callback_data="buy_custom_gb")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=back_target)],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_buy")]
    ])

def get_qty_menu(gb):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1 عدد", callback_data="buy_qty_1"), InlineKeyboardButton("2 عدد", callback_data="buy_qty_2")],
        [InlineKeyboardButton("3 عدد", callback_data="buy_qty_3"), InlineKeyboardButton("4 عدد", callback_data="buy_qty_4")],
        [InlineKeyboardButton("5 عدد", callback_data="buy_qty_5")],
        [InlineKeyboardButton("📦 تعداد دلخواه", callback_data="buy_custom_qty")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_gb_agent")],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_buy")]
    ])

def get_invoice_menu(is_agent_flow):
    back_target = "back_to_qty" if is_agent_flow else "back_to_gb_normal"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید و ادامه", callback_data="buy_confirm")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=back_target)],
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
    user_data[uid] = {"type": "buy", "service": None, "gb": 0, "qty": 1, "discount": "ندارد", "price": 0}
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
    # مسیر خرید (قیف فروش)
    # =================================
    if uid not in user_data:
        user_data[uid] = {"type": "buy", "qty": 1, "discount": "ندارد"}

    # 1. انتخاب سرویس
    if data == "back_to_srv":
        await query.edit_message_text("🛍 بخش خرید\n\nلطفاً نوع سرویس مورد نظر خود را انتخاب کنید:", reply_markup=get_service_menu())
        return

    if data == "buy_srv_vip":
        # حل مشکل باز شدن پنجره پاپ آپ با آرگومان text
        return await query.answer(text="⛔️ فروش این سرویس موقتا بسته است. لطفا سرویس دیگری را انتخاب یا مجددا بعدا تلاش کنید.", show_alert=True)

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
        srv = "نمایندگی فروش 💎" if user_data[uid].get("service") == "agent" else "تانل عادی 🌐"
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
        await query.edit_message_text("📦 مقدار گیگ (حجم سرویس) رو انتخاب کنید:", reply_markup=get_gb_menu())
        return

    # 5. انتخاب حجم
    if data in ["back_to_gb_normal", "back_to_gb_agent"]:
        await query.edit_message_text("📦 مقدار گیگ (حجم سرویس) رو انتخاب کنید:", reply_markup=get_gb_menu())
        return

    if data == "buy_custom_gb":
        user_state[uid] = "WAIT_CUSTOM_BUY_GB"
        await query.edit_message_text("📦 مقدار حجم دلخواه رو به عدد (انگلیسی) ارسال کن:\n\nمثال: 10")
        return

    if data.startswith("buy_gb_"):
        gb = int(data.split("_")[2])
        user_data[uid]["gb"] = gb
        
        # اگر تانل عادی بود میره برای فاکتور، اگر نماینده بود میره برای انتخاب تعداد
        if user_data[uid].get("service") == "agent":
            await query.edit_message_text(f"💎 چه تعداد سرویس {gb} گیگ لازم دارین؟", reply_markup=get_qty_menu(gb))
        else:
            user_data[uid]["qty"] = 1
            await generate_and_send_invoice(query, uid)
        return

    # 6. انتخاب تعداد (فقط نمایندگان)
    if data == "back_to_qty":
        gb = user_data[uid].get("gb", 1)
        await query.edit_message_text(f"💎 چه تعداد سرویس {gb} گیگ لازم دارین؟", reply_markup=get_qty_menu(gb))
        return

    if data == "buy_custom_qty":
        user_state[uid] = "WAIT_CUSTOM_BUY_QTY"
        await query.edit_message_text("📦 تعداد سرویس دلخواه رو به عدد (انگلیسی) ارسال کن:\n\nمثال: 10")
        return

    if data.startswith("buy_qty_"):
        qty = int(data.split("_")[2])
        user_data[uid]["qty"] = qty
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
            [InlineKeyboardButton("1GB", callback_data="renew_1"), InlineKeyboardButton("2GB", callback_data="renew_2")],
            [InlineKeyboardButton("3GB", callback_data="renew_3"), InlineKeyboardButton("4GB", callback_data="renew_4")],
            [InlineKeyboardButton("5GB", callback_data="renew_5")],
            [InlineKeyboardButton("📦 حجم دلخواه", callback_data="custom_renew")],
            [InlineKeyboardButton("❌ لغو سفارش", callback_data="cancel_all")]
        ]
        await query.edit_message_text("📦 حجم تمدید رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "custom_renew":
        user_state[uid] = "WAIT_CUSTOM_RENEW"
        await query.edit_message_text("📦 حجم دلخواه رو به عدد ارسال کن\n\nمثال:\n10")
        return

    if data.startswith("renew_"):
        gb = int(data.split("_")[1])
        pr = price(gb)
        if uid not in user_data: user_data[uid] = {}
        user_data[uid]["type"] = "renew"
        user_data[uid]["gb"] = gb
        user_data[uid]["price"] = pr
        user_state[uid] = "WAIT_RENEW_RECEIPT"
        
        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_renew")], [InlineKeyboardButton("❌ لغو سفارش", callback_data="cancel_all")]]
        text = f"✅ تمدید انتخاب شد\n\n📦 حجم:\n`{gb}GB`\n\n💰 مبلغ:\n`{format_price(pr)}`\n\n💳 شماره کارت:\n`{CARD_NUMBER}`\n👤 صاحب کارت:\n{CARD_NAME}\n\n📸 بعد از پرداخت رسید رو ارسال کن 😄"
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
    gb = data["gb"]
    qty = data.get("qty", 1)
    is_agent_flow = (data.get("service") == "agent")
    
    # محاسبه قیمت
    unit_price = agent_price(gb) if is_agent_flow else price(gb)
    total_price = unit_price * qty
    user_data[uid]["price"] = total_price
    
    service_name = "نمایندگی فروش 💎" if is_agent_flow else "تانل عادی 🌐"
    
    text = f"""
🧾 پیش فاکتور شما:

🔸 نوع سرویس: {service_name}
🔸 حجم سرویس: {gb} گیگابایت
"""
    if is_agent_flow:
        text += f"🔸 تعداد سرویس: {qty} عدد\n"
        
    text += f"""🔸 روش پرداخت: نقدی (کارت به کارت)
🔸 کد تخفیف: {data.get("discount", "ندارد")}
    
💰 قیمت نهایی: {format_price(total_price)}

✅ در صورت اطمینان، روی تایید و ادامه کلیک کنید."""

    reply_markup = get_invoice_menu(is_agent_flow)
    
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
        await update.message.reply_text("✅ کد تخفیف اعمال شد.\n\n📦 مقدار گیگ رو انتخاب کنید:", reply_markup=get_gb_menu())
        return

    # دریافت دستی حجم گیگ
    if state == "WAIT_CUSTOM_BUY_GB":
        if not text.isdigit(): return await update.message.reply_text("❌ فقط عدد انگلیسی ارسال کن")
        gb = int(text)
        user_data[uid]["gb"] = gb
        if user_data[uid].get("service") == "agent":
            await update.message.reply_text(f"💎 چه تعداد سرویس {gb} گیگ لازم دارین؟", reply_markup=get_qty_menu(gb))
        else:
            user_data[uid]["qty"] = 1
            await generate_and_send_invoice(update.message, uid)
        return

    # دریافت دستی تعداد اکانت (مخصوص نماینده)
    if state == "WAIT_CUSTOM_BUY_QTY":
        if not text.isdigit(): return await update.message.reply_text("❌ فقط عدد انگلیسی ارسال کن")
        user_data[uid]["qty"] = int(text)
        await generate_and_send_invoice(update.message, uid)
        return

    # دریافت لینک برای تمدید
    if state == "WAIT_RENEW_LINK":
        user_data[uid] = {"type": "renew", "link": text}
        keyboard = [
            [InlineKeyboardButton("1GB", callback_data="renew_1"), InlineKeyboardButton("2GB", callback_data="renew_2")],
            [InlineKeyboardButton("3GB", callback_data="renew_3"), InlineKeyboardButton("4GB", callback_data="renew_4")],
            [InlineKeyboardButton("5GB", callback_data="renew_5")],
            [InlineKeyboardButton("📦 حجم دلخواه", callback_data="custom_renew")],
            [InlineKeyboardButton("❌ لغو سفارش", callback_data="cancel_all")]
        ]
        user_state[uid] = "WAIT_RENEW_GB"
        return await update.message.reply_text("📦 حجم تمدید رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

    if state == "WAIT_CUSTOM_RENEW":
        if not text.isdigit(): return await update.message.reply_text("❌ فقط عدد ارسال کن")
        gb = int(text)
        pr = price(gb)
        user_data[uid]["gb"] = gb
        user_data[uid]["price"] = pr
        user_state[uid] = "WAIT_RENEW_RECEIPT"
        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_renew")], [InlineKeyboardButton("❌ لغو سفارش", callback_data="cancel_all")]]
        text_msg = f"✅ پلن انتخاب شد\n\n📦 حجم:\n`{gb}GB`\n\n💰 مبلغ:\n`{format_price(pr)}`\n\n💳 شماره کارت:\n`{CARD_NUMBER}`\n\n📸 بعد از پرداخت، رسید رو ارسال کن 😄"
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
    qty = data.get("qty", 1)

    cursor.execute("""
    INSERT INTO orders (order_code, user_id, order_type, gb, qty, price, status, link, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (order_code, uid, data["type"], data["gb"], qty, data["price"], "pending", data.get("link", "-"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()

    agent_tag = "💎 (نماینده)" if data.get("service") == "agent" else ""

    if data["type"] == "buy":
        caption = f"🛒 خرید جدید {agent_tag}\n\n🧾 سفارش: {order_code}\n👤 کاربر: {uid}\n📦 حجم: {data['gb']}GB\n🔢 تعداد: {qty} عدد\n💰 مبلغ: {format_price(data['price'])}"
    else:
        caption = f"♻️ تمدید جدید\n\n🧾 سفارش: {order_code}\n👤 کاربر: {uid}\n🔗 لینک:\n`{data['link']}`\n📦 حجم: {data['gb']}GB\n🔢 تعداد: 1 عدد\n💰 مبلغ: {format_price(data['price'])}"

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
    qty = 1
    gb = 0

    # خواندن اطلاعات از کپشن فیش
    for line in lines:
        if "👤 کاربر:" in line:
            uid = int(line.split(":")[1].strip())
        elif "🧾 سفارش:" in line:
            order_code = line.split(":")[1].strip()
        elif "🔢 تعداد:" in line:
            qty = int(line.split(":")[1].replace("عدد", "").strip())
        elif "📦 حجم:" in line:
            gb = int(line.split(":")[1].replace("GB", "").strip())

    if not uid or not order_code: return

    # اگر سفارش تک اکانته بود (خرید عادی یا تمدید)
    if qty == 1:
        await context.bot.send_message(
            chat_id=uid, 
            text=f"✅ سفارش شما تایید شد 😄\n\n🔗 اکانت شما:\n\n`{update.message.text}`\n\nممنون از خرید شما ❤️", 
            parse_mode="Markdown"
        )
        cursor.execute("UPDATE orders SET status = 'success' WHERE user_id = ? AND status = 'pending'", (uid,))
        db.commit()
        return await update.message.reply_text("✅ برای مشتری ارسال شد")

    # سیستم ارسال چند مرحله‌ای (برای تعداد بیشتر از 1)
    if order_code not in admin_multi_delivery:
        admin_multi_delivery[order_code] = {"uid": uid, "qty": qty, "gb": gb, "links": []}

    admin_multi_delivery[order_code]["links"].append(update.message.text)
    current_count = len(admin_multi_delivery[order_code]["links"])

    if current_count < qty:
        await update.message.reply_text(f"✅ اکانت {current_count} از {qty} دریافت شد.\nلطفا مجدداً روی همون فیش ریپلای کن و اکانت بعدی رو بفرست.")
    else:
        # ارسال جداگانه هر اکانت برای کاربر
        links = admin_multi_delivery[order_code]["links"]
        for idx, link in enumerate(links):
            msg_text = f"سرویس {idx + 1} با حجم {gb} گیگ\n\n`{link}`"
            await context.bot.send_message(chat_id=uid, text=msg_text, parse_mode="Markdown")

        # ارسال پیام نهایی تکمیل سفارش
        await context.bot.send_message(chat_id=uid, text="✅ تمام اکانت‌های سفارش شما ارسال شد. ممنون از خرید شما ❤️")

        # بروزرسانی دیتابیس
        cursor.execute("UPDATE orders SET status = 'success' WHERE user_id = ? AND status = 'pending'", (uid,))
        db.commit()

        await update.message.reply_text(f"✅ هر {qty} اکانت به صورت جداگانه برای نماینده ارسال شد و سفارش تکمیل گردید.")
        
        # پاک کردن حافظه موقت سفارش تکمیل شده
        del admin_multi_delivery[order_code]

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