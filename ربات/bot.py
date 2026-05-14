
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

TOKEN = "8681136841:AAGl_bEOluOXsKqCtuBVk-hb47jeRCMIiRc"

ADMIN_ID = 8422742448

CARD_NUMBER = "6219861936116119"
CARD_NAME = "رحیم آخوندی زاده"

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
    join_date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT,
    user_id INTEGER,
    order_type TEXT,
    gb INTEGER,
    price INTEGER,
    status TEXT,
    link TEXT,
    created_at TEXT
)
""")

try:
    cursor.execute(
        "ALTER TABLE orders ADD COLUMN order_code TEXT"
    )
except:
    pass


db.commit()

# =====================================
# حافظه موقت
# =====================================

user_state = {}
user_data = {}
admin_state = {}

# =====================================
# کیبورد ها
# =====================================

main_keyboard = ReplyKeyboardMarkup(
    [
        ["♻️ تمدید", "💰 خرید"],
        ["📞 پشتیبانی"]
    ],
    resize_keyboard=True
)

admin_keyboard = ReplyKeyboardMarkup(
    [
        ["📦 فروش تا این لحظه"],
        ["♻️ تمدید تا این لحظه"],
        ["👤 کاربران بدون خرید"]
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

# =====================================
# قیمت
# =====================================

def price(gb):

    gb = int(gb)

    base = {
        1: 350000,
        2: 680000,
        3: 850000,
        4: 1200000,
        5: 1550000
    }

    if gb in base:
        return base[gb]

    return int(gb * 350000 * 0.9)

# =====================================
# کد سفارش
# =====================================

def generate_order_code():

    now = datetime.now().strftime("%Y%m%d")

    rand = random.randint(1000, 9999)

    return f"AKZ-{now}-{rand}"

# =====================================
# عضویت کانال
# =====================================

async def check_membership(user_id, context):

    try:

        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        if member.status in [
            "member",
            "administrator",
            "creator"
        ]:
            return True

        return False

    except:
        return False

# =====================================
# ثبت کاربر
# =====================================

def register_user(uid):

    cursor.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (uid,)
    )

    user = cursor.fetchone()

    if not user:

        cursor.execute(
            "INSERT INTO users VALUES (?, ?)",
            (
                uid,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        db.commit()

# =====================================
# آنالیز مشتری
# =====================================

def customer_analysis(uid):

    cursor.execute("""
    SELECT COUNT(*)
    FROM orders
    WHERE user_id = ?
    AND status = 'success'
    """, (uid,))

    success = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM orders
    WHERE user_id = ?
    AND status = 'reject'
    """, (uid,))

    reject = cursor.fetchone()[0]

    text = f"""
👤 آنالیز مشتری

🆔 آیدی:
{uid}

✅ سفارش موفق:
{success}

❌ سفارش رد شده:
{reject}
"""

    return text

# =====================================
# آمار فروش
# =====================================

def sales_stats():

    cursor.execute("""
    SELECT COUNT(*), COALESCE(SUM(price),0)
    FROM orders
    WHERE order_type = 'buy'
    AND status = 'success'
    """)

    data = cursor.fetchone()

    return f"""
📦 آمار فروش

✅ تعداد فروش موفق:
{data[0]}

💰 مجموع فروش:
{format_price(data[1])}
"""

# =====================================
# آمار تمدید
# =====================================

def renew_stats():

    cursor.execute("""
    SELECT COUNT(*), COALESCE(SUM(price),0)
    FROM orders
    WHERE order_type = 'renew'
    AND status = 'success'
    """)

    data = cursor.fetchone()

    return f"""
♻️ آمار تمدید

✅ تعداد تمدید موفق:
{data[0]}

💰 مجموع تمدید:
{format_price(data[1])}
"""

# =====================================
# کاربران بدون خرید
# =====================================

def users_without_orders():

    cursor.execute("""
    SELECT user_id
    FROM users
    WHERE user_id NOT IN (
        SELECT DISTINCT user_id
        FROM orders
    )
    """)

    users = cursor.fetchall()

    if not users:
        return "✅ همه کاربران خرید یا تمدید داشتن"

    text = "👤 کاربران بدون خرید:\n\n"

    for user in users:
        text += f"{user[0]}\n"

    return text

# =====================================
# استارت
# =====================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    register_user(uid)

    member = await check_membership(uid, context)

    if not member:

        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 عضویت در کانال",
                    url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ بررسی عضویت",
                    callback_data="check_join"
                )
            ]
        ]

        return await update.message.reply_text(
            "❌ ابتدا داخل کانال عضو شو سپس روی بررسی عضویت بزن",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    user_state[uid] = "MENU"

    user_data.pop(uid, None)

    if uid == ADMIN_ID:

        return await update.message.reply_text(
            "👑 پنل مدیریت فعال شد",
            reply_markup=admin_keyboard
        )

    text = """
سلام 😄
به Akz VPN خوش اومدی

از منوی پایین انتخاب کن 👇
"""

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard
    )

# =====================================
# خرید
# =====================================

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "1GB",
                callback_data="buy_1"
            ),
            InlineKeyboardButton(
                "2GB",
                callback_data="buy_2"
            )
        ],
        [
            InlineKeyboardButton(
                "3GB",
                callback_data="buy_3"
            ),
            InlineKeyboardButton(
                "4GB",
                callback_data="buy_4"
            )
        ],
        [
            InlineKeyboardButton(
                "5GB",
                callback_data="buy_5"
            )
        ],
        [
            InlineKeyboardButton(
                "📦 حجم دلخواه",
                callback_data="custom_buy"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ لغو سفارش",
                callback_data="cancel_all"
            )
        ]
    ]

    await update.message.reply_text(
        "📦 حجم موردنظر رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================================
# تمدید
# =====================================

async def renew(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    user_state[uid] = "WAIT_RENEW_LINK"

    keyboard = [
        [
            InlineKeyboardButton(
                "❌ لغو سفارش",
                callback_data="cancel_all"
            )
        ]
    ]

    await update.message.reply_text(
        "🔗 لینک یا کانفیگ قبلی رو ارسال کن 😄",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================================
# لغو
# =====================================

async def cancel_process(query):

    uid = query.from_user.id

    user_state[uid] = "MENU"

    user_data.pop(uid, None)

    await query.message.reply_text(
        "❌ عملیات لغو شد",
        reply_markup=main_keyboard
    )

# =====================================
# دکمه ها
# =====================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    uid = query.from_user.id

    data = query.data

    if data == "check_join":

        member = await check_membership(uid, context)

        if member:

            if uid == ADMIN_ID:

                return await query.message.reply_text(
                    "✅ عضویت تایید شد",
                    reply_markup=admin_keyboard
                )

            return await query.message.reply_text(
                "✅ عضویت تایید شد",
                reply_markup=main_keyboard
            )

        return await query.message.reply_text(
            "❌ هنوز عضو کانال نشدی"
        )

    # =================================
    # لغو
    # =================================

    if data == "cancel_all":

        return await cancel_process(query)

    # =================================
    # برگشت خرید
    # =================================

    if data == "back_buy":

        keyboard = [
            [
                InlineKeyboardButton(
                    "1GB",
                    callback_data="buy_1"
                ),
                InlineKeyboardButton(
                    "2GB",
                    callback_data="buy_2"
                )
            ],
            [
                InlineKeyboardButton(
                    "3GB",
                    callback_data="buy_3"
                ),
                InlineKeyboardButton(
                    "4GB",
                    callback_data="buy_4"
                )
            ],
            [
                InlineKeyboardButton(
                    "5GB",
                    callback_data="buy_5"
                )
            ],
            [
                InlineKeyboardButton(
                    "📦 حجم دلخواه",
                    callback_data="custom_buy"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ لغو سفارش",
                    callback_data="cancel_all"
                )
            ]
        ]

        await query.edit_message_text(
            "📦 حجم موردنظر رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =================================
    # برگشت تمدید
    # =================================

    if data == "back_renew":

        keyboard = [
            [
                InlineKeyboardButton(
                    "1GB",
                    callback_data="renew_1"
                ),
                InlineKeyboardButton(
                    "2GB",
                    callback_data="renew_2"
                )
            ],
            [
                InlineKeyboardButton(
                    "3GB",
                    callback_data="renew_3"
                ),
                InlineKeyboardButton(
                    "4GB",
                    callback_data="renew_4"
                )
            ],
            [
                InlineKeyboardButton(
                    "5GB",
                    callback_data="renew_5"
                )
            ],
            [
                InlineKeyboardButton(
                    "📦 حجم دلخواه",
                    callback_data="custom_renew"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ لغو سفارش",
                    callback_data="cancel_all"
                )
            ]
        ]

        await query.edit_message_text(
            "📦 حجم تمدید رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =================================
    # حجم دلخواه خرید
    # =================================

    if data == "custom_buy":

        user_state[uid] = "WAIT_CUSTOM_BUY"

        await query.edit_message_text(
            """📦 حجم دلخواه رو به عدد ارسال کن

مثال:
10"""
        )

        return

    # =================================
    # حجم دلخواه تمدید
    # =================================

    if data == "custom_renew":

        user_state[uid] = "WAIT_CUSTOM_RENEW"

        await query.edit_message_text(
             """📦 حجم دلخواه رو به عدد ارسال کن

مثال:
10"""
        )

        return

    # =================================
    # خرید
    # =================================

    if data.startswith("buy_"):

        gb = int(data.split("_")[1])

        pr = price(gb)

        user_data[uid] = {
            "type": "buy",
            "gb": gb,
            "price": pr
        }

        user_state[uid] = "WAIT_BUY_RECEIPT"

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 برگشت",
                    callback_data="back_buy"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ لغو سفارش",
                    callback_data="cancel_all"
                )
            ]
        ]

        text = f"""
✅ پلن انتخاب شد

📦 حجم:
`{gb}GB`

💰 مبلغ:
`{format_price(pr)}`

💳 شماره کارت:
`{CARD_NUMBER}`

👤 صاحب کارت:
{CARD_NAME}

📸 بعد از پرداخت، رسید رو ارسال کن 😄
"""

        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =================================
    # تمدید
    # =================================

    if data.startswith("renew_"):

        gb = int(data.split("_")[1])

        pr = price(gb)

        user_data[uid]["gb"] = gb
        user_data[uid]["price"] = pr

        user_state[uid] = "WAIT_RENEW_RECEIPT"

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 برگشت",
                    callback_data="back_renew"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ لغو سفارش",
                    callback_data="cancel_all"
                )
            ]
        ]

        text = f"""
✅ تمدید انتخاب شد

📦 حجم:
`{gb}GB`

💰 مبلغ:
`{format_price(pr)}`

💳 شماره کارت:
`{CARD_NUMBER}`

👤 صاحب کارت:
{CARD_NAME}

📸 بعد از پرداخت رسید رو ارسال کن 😄
"""

        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =================================
    # آنالیز
    # =================================

    if data.startswith("analysis_"):

        target = int(data.split("_")[1])

        text = customer_analysis(target)

        await query.message.reply_text(text)

        return

    # =================================
    # رد سفارش
    # =================================

    if data.startswith("reject_"):

        target = int(data.split("_")[1])

        admin_state[uid] = {
            "action": "reject",
            "target": target
        }

        await query.message.reply_text(
            "✍ متن رد سفارش رو ارسال کن:"
        )

        return

# =====================================
# متن ها
# =====================================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    text = update.message.text

    state = user_state.get(uid, "MENU")

    # =================================
    # متن رد سفارش
    # =================================

    if uid == ADMIN_ID:

        admin_action = admin_state.get(uid)

        if admin_action:

            if admin_action["action"] == "reject":

                target = admin_action["target"]

                await context.bot.send_message(
                    chat_id=target,
                    text=f"""
❌ سفارش شما رد شد

{text}
"""
                )

                cursor.execute("""
                UPDATE orders
                SET status = 'reject'
                WHERE user_id = ?
                AND status = 'pending'
                """, (target,))

                db.commit()

                admin_state.pop(uid)

                await update.message.reply_text(
                    "✅ پیام رد ارسال شد"
                )

                return

    if uid == ADMIN_ID:

        if text == "📦 فروش تا این لحظه":

            return await update.message.reply_text(
                sales_stats()
            )

        if text == "♻️ تمدید تا این لحظه":

            return await update.message.reply_text(
                renew_stats()
            )

        if text == "👤 کاربران بدون خرید":

            return await update.message.reply_text(
                users_without_orders()
            )

    # =================================
    # خرید
    # =================================

    if text == "💰 خرید":

        await update.message.reply_text(
            "درحال ورود به بخش خرید 😄",
            reply_markup=ReplyKeyboardRemove()
        )

        return await buy(update, context)

    # =================================
    # تمدید
    # =================================

    if text == "♻️ تمدید":

        await update.message.reply_text(
            "درحال ورود به بخش تمدید 😄",
            reply_markup=ReplyKeyboardRemove()
        )

        return await renew(update, context)

    # =================================
    # پشتیبانی
    # =================================

    if text == "📞 پشتیبانی":

        await update.message.reply_text(
            """ 🆔 پشتیبانی:
{SUPPORT_ID} """
        )

        return

    # =================================
    # حجم دلخواه خرید
    # =================================

    if state == "WAIT_CUSTOM_BUY":

        if not text.isdigit():

            return await update.message.reply_text(
                "❌ فقط عدد ارسال کن"
            )

        gb = int(text)

        pr = price(gb)

        user_data[uid] = {
            "type": "buy",
            "gb": gb,
            "price": pr
        }

        user_state[uid] = "WAIT_BUY_RECEIPT"

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 برگشت",
                    callback_data="back_buy"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ لغو سفارش",
                    callback_data="cancel_all"
                )
            ]
        ]

        text_msg = f"""
✅ پلن انتخاب شد

📦 حجم:
`{gb}GB`

💰 مبلغ:
`{format_price(pr)}`

💳 شماره کارت:
`{CARD_NUMBER}`

👤 صاحب کارت:
{CARD_NAME}

📸 بعد از پرداخت، رسید رو ارسال کن 😄
"""

        await update.message.reply_text(
            text_msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =================================
    # گرفتن لینک تمدید
    # =================================

    if state == "WAIT_RENEW_LINK":

        user_data[uid] = {
            "type": "renew",
            "link": text
        }

        keyboard = [
            [
                InlineKeyboardButton(
                    "1GB",
                    callback_data="renew_1"
                ),
                InlineKeyboardButton(
                    "2GB",
                    callback_data="renew_2"
                )
            ],
            [
                InlineKeyboardButton(
                    "3GB",
                    callback_data="renew_3"
                ),
                InlineKeyboardButton(
                    "4GB",
                    callback_data="renew_4"
                )
            ],
            [
                InlineKeyboardButton(
                    "5GB",
                    callback_data="renew_5"
                )
            ],
            [
                InlineKeyboardButton(
                    "📦 حجم دلخواه",
                    callback_data="custom_renew"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ لغو سفارش",
                    callback_data="cancel_all"
                )
            ]
        ]

        user_state[uid] = "WAIT_RENEW_GB"

        await update.message.reply_text(
            "📦 حجم تمدید رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================
# رسید
# =====================================

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    state = user_state.get(uid)

    if state not in [
        "WAIT_BUY_RECEIPT",
        "WAIT_RENEW_RECEIPT"
    ]:
        return

    if update.message.photo:

        file_id = update.message.photo[-1].file_id

    elif update.message.document:

        file_id = update.message.document.file_id

    else:
        return

    data = user_data.get(uid)

    if not data:
        return

    order_code = generate_order_code()

    cursor.execute("""
    INSERT INTO orders (
        order_code,
        user_id,
        order_type,
        gb,
        price,
        status,
        link,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_code,
        uid,
        data["type"],
        data["gb"],
        data["price"],
        "pending",
        data.get("link", "-"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    db.commit()

    if data["type"] == "buy":

        caption = f"""
🛒 خرید جدید

🧾 کد سفارش:
{order_code}

👤 کاربر:
{uid}

📦 حجم:
{data['gb']}GB

💰 مبلغ:
{format_price(data['price'])}
"""

    else:

        caption = f"""
♻️ تمدید جدید

🧾 کد سفارش:
{order_code}

👤 کاربر:
{uid}

🔗 لینک:
`{data['link']}`

📦 حجم:
{data['gb']}GB

💰 مبلغ:
{format_price(data['price'])}
"""

    keyboard = [
        [
            InlineKeyboardButton(
                "👤 آنالیز مشتری",
                callback_data=f"analysis_{uid}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ رد سفارش",
                callback_data=f"reject_{uid}"
            )
        ]
    ]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=file_id,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    user_state[uid] = "MENU"

    await update.message.reply_text(
        f"""
✅ رسید شما ارسال شد

🧾 کد سفارش:
{order_code}

بعد از تایید، اکانت برات ارسال میشه 😄
""",
        reply_markup=main_keyboard
    )

# =====================================
# تایید سفارش
# =====================================

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    reply = update.message.reply_to_message.caption

    if not reply:
        return

    lines = reply.split("\n")

    uid = None

    for i in range(len(lines)):

        if "👤 کاربر:" in lines[i]:

            uid = int(lines[i + 1])

            break

    if not uid:
        return

    await context.bot.send_message(
        chat_id=uid,
        text=f"""
✅ سفارش شما تایید شد 😄

🔗 اکانت شما:

`{update.message.text}`

ممنون از خرید شما ❤️
""",
        parse_mode="Markdown"
    )

    cursor.execute("""
    UPDATE orders
    SET status = 'success'
    WHERE user_id = ?
    AND status = 'pending'
    """, (uid,))

    db.commit()

    await update.message.reply_text(
        "✅ برای مشتری ارسال شد"
    )

# =====================================
# اجرا
# =====================================

app = (
    ApplicationBuilder()
    .token(TOKEN)
    .connect_timeout(30)
    .read_timeout(30)
    .write_timeout(30)
    .pool_timeout(30)
    .build()
)

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CallbackQueryHandler(buttons)
)

app.add_handler(
    MessageHandler(
        filters.TEXT & filters.REPLY,
        admin_reply
    )
)

app.add_handler(
    MessageHandler(
        filters.PHOTO |
        filters.Document.IMAGE,
        photo_handler
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT,
        text_handler
    )
)

print("Bot is running 😄")

app.run_polling(
    drop_pending_updates=True
)
