import os
import sqlite3
import requests

from telegram import (
Update,
ReplyKeyboardMarkup,
InlineKeyboardButton,
InlineKeyboardMarkup,
LabeledPrice
)

from telegram.ext import (
ApplicationBuilder,
CommandHandler,
MessageHandler,
CallbackQueryHandler,
PreCheckoutQueryHandler,
filters,
ContextTypes
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
SUNO_API = os.getenv("SUNO_API_KEY")

BOT_USERNAME = "Pesnya_iz_text_bot"

SUNO_URL = "https://api.sunoapi.org/api/v1/generate"


# ================= DATABASE =================

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
free_used INTEGER DEFAULT 0,
credits INTEGER DEFAULT 0,
referrer INTEGER
)
""")

conn.commit()


def create_user(user,ref=None):

    cursor.execute("SELECT id FROM users WHERE id=?",(user,))
    exists = cursor.fetchone()

    if not exists:

        cursor.execute(
        "INSERT INTO users(id,referrer) VALUES (?,?)",
        (user,ref)
        )

        conn.commit()

        if ref and ref!=user:

            cursor.execute(
            "UPDATE users SET credits = credits + 1 WHERE id=?",
            (ref,)
            )

            conn.commit()


def get_user(user):

    cursor.execute(
    "SELECT free_used,credits FROM users WHERE id=?",
    (user,)
    )

    row = cursor.fetchone()

    if not row:

        cursor.execute(
        "INSERT INTO users(id) VALUES(?)",
        (user,)
        )

        conn.commit()

        return (0,0)

    return row


def use_free(user):

    cursor.execute(
    "UPDATE users SET free_used=1 WHERE id=?",
    (user,)
    )

    conn.commit()


def use_credit(user):

    cursor.execute(
    "UPDATE users SET credits=credits-1 WHERE id=?",
    (user,)
    )

    conn.commit()


def add_credits(user,amount):

    cursor.execute(
    "UPDATE users SET credits=credits+? WHERE id=?",
    (amount,user)
    )

    conn.commit()


# ================= PACKAGES =================

PACKAGES = {

"pack3":{
"title":"3 песни",
"credits":3,
"price":100
},

"pack10":{
"title":"10 песен",
"credits":10,
"price":250
},

"pack50":{
"title":"50 песен",
"credits":50,
"price":900
}

}


# ================= PROMPT =================

def build_prompt(data):

    prompt = f"""
Create a Russian song.

Style: {data['style']}
Mood: {data['mood']}

Song for: {data['name']}
From: {data['from']}

Occasion:
{data['occasion']}

Description:
{data['description']}
"""

    return prompt


user_data = {}


# ================= START =================

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    ref=None

    if context.args:
        try:
            ref=int(context.args[0])
        except:
            pass

    create_user(user,ref)

    keyboard=[

["❤️ Любимому"],
["👬 Другу"],
["💍 Свадьба"],
["🏢 Компания"]

]

    await update.message.reply_text(

"🎵 Я создаю персональные песни\n\nДля кого песня?",

reply_markup=ReplyKeyboardMarkup(keyboard,resize_keyboard=True)

)


# ================= REF =================

async def ref(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.message.from_user.id

    link=f"https://t.me/{BOT_USERNAME}?start={user}"

    await update.message.reply_text(

f"""
Приглашай друзей и получай песни 🎵

За каждого друга:

+1 генерация

Твоя ссылка:

{link}
"""
)


# ================= BUY =================

async def buy(update:Update,context:ContextTypes.DEFAULT_TYPE):

    keyboard=[

[InlineKeyboardButton("3 песни ⭐",callback_data="pack3")],
[InlineKeyboardButton("10 песен ⭐",callback_data="pack10")],
[InlineKeyboardButton("50 песен ⭐",callback_data="pack50")]

]

    await update.message.reply_text(

"Выберите пакет",

reply_markup=InlineKeyboardMarkup(keyboard)

)


# ================= PACKAGE CLICK =================

async def package_click(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    package=query.data

    pack=PACKAGES[package]

    prices=[LabeledPrice(pack["title"],pack["price"])]

    await context.bot.send_invoice(

chat_id=query.message.chat_id,

title=pack["title"],

description="Покупка песен",

payload=package,

provider_token="",

currency="XTR",

prices=prices

)


# ================= PAYMENT =================

async def precheckout(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.pre_checkout_query.answer(ok=True)


async def successful_payment(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.message.from_user.id

    package=update.message.successful_payment.invoice_payload

    credits=PACKAGES[package]["credits"]

    add_credits(user,credits)

    await update.message.reply_text(

f"Оплата прошла успешно 🎉\n\nНачислено {credits} песен"

)


# ================= QUESTIONS =================

async def message(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.message.from_user.id
    text=update.message.text

    if user not in user_data:
        user_data[user]={}

    data=user_data[user]

    if "target" not in data:

        data["target"]=text

        await update.message.reply_text("Имя человека?")

        return

    if "name" not in data:

        data["name"]=text

        await update.message.reply_text("От кого песня?")

        return

    if "from" not in data:

        data["from"]=text

        await update.message.reply_text("Повод?")

        return

    if "occasion" not in data:

        data["occasion"]=text

        await update.message.reply_text("Описание человека")

        return

    if "description" not in data:

        data["description"]=text

        await update.message.reply_text("Стиль песни")

        return

    if "style" not in data:

        data["style"]=text

        await update.message.reply_text("Настроение песни")

        return

    if "mood" not in data:

        data["mood"]=text

        free,credits=get_user(user)

        if free==0:

            use_free(user)

        elif credits>0:

            use_credit(user)

        else:

            await update.message.reply_text(

"Бесплатная песня закончилась.\n\n/ref — пригласи друга\n/buy — купить песни"

)

            return

        prompt=build_prompt(data)

        await update.message.reply_text("🎵 Генерирую песню...")

        r=requests.post(

SUNO_URL,

headers={"Authorization":f"Bearer {SUNO_API}"},

json={"prompt":prompt}

)

        audio=r.json()["audio_url"]

        song=requests.get(audio)

        file=f"{user}.mp3"

        with open(file,"wb") as f:
            f.write(song.content)

        await update.message.reply_audio(open(file,"rb"))

        user_data[user]={}


# ================= RUN =================

app=ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("ref",ref))
app.add_handler(CommandHandler("buy",buy))

app.add_handler(CallbackQueryHandler(package_click))

app.add_handler(PreCheckoutQueryHandler(precheckout))

app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT,successful_payment))

app.add_handler(MessageHandler(filters.TEXT,message))

app.run_polling()
