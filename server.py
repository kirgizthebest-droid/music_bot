import os
import requests
import sqlite3

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes


TOKEN = os.getenv("TELEGRAM_TOKEN")
SUNO_API_KEY = os.getenv("SUNO_API_KEY")

BOT_USERNAME = "YOUR_BOT_USERNAME"

SUNO_URL = "https://api.sunoapi.org/api/v1/generate"


# ===== БАЗА ДАННЫХ =====

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


def create_user(user_id, ref=None):

    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    exists = cursor.fetchone()

    if not exists:

        cursor.execute(
        "INSERT INTO users(id,referrer) VALUES (?,?)",
        (user_id,ref)
        )

        conn.commit()

        if ref and ref != user_id:
            add_credits(ref,1)


def get_user(user):

    cursor.execute(
    "SELECT free_used,credits FROM users WHERE id=?",
    (user,)
    )

    row = cursor.fetchone()

    if row is None:

        cursor.execute(
        "INSERT INTO users(id) VALUES(?)",
        (user,)
        )

        conn.commit()

        return (0,0)

    return row


def add_credits(user,amount):

    cursor.execute(
    "UPDATE users SET credits = credits + ? WHERE id=?",
    (amount,user)
    )

    conn.commit()


def use_credit(user):

    cursor.execute(
    "UPDATE users SET credits = credits - 1 WHERE id=?",
    (user,)
    )

    conn.commit()


def use_free(user):

    cursor.execute(
    "UPDATE users SET free_used = 1 WHERE id=?",
    (user,)
    )

    conn.commit()


# ===== PROMPT =====

def build_prompt(data):

    prompt = f"""
Create a Russian song.

Style: {data['style']}
Mood: {data['mood']}

Song for: {data['name']}
From: {data['from']}
Occasion: {data['occasion']}

Description:
{data['description']}
"""

    return prompt


user_data = {}


# ===== START =====

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    ref = None

    if context.args:
        try:
            ref = int(context.args[0])
        except:
            pass

    create_user(user,ref)

    keyboard = [
    ["❤️ Любимому человеку"],
    ["👬 Другу"],
    ["💍 Свадебная песня"],
    ["🏢 Для компании"]
    ]

    await update.message.reply_text(

    "🎵 Я создаю персональные песни\n\nДля кого будет песня?",

    reply_markup=ReplyKeyboardMarkup(keyboard,resize_keyboard=True)

    )


# ===== РЕФЕРАЛЬНАЯ ССЫЛКА =====

async def ref(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    link = f"https://t.me/{BOT_USERNAME}?start={user}"

    await update.message.reply_text(

f"""
Приглашай друзей и получай бесплатные песни 🎵

За каждого друга ты получаешь:

+1 генерацию песни

Твоя ссылка:

{link}
"""

    )


# ===== ОСНОВНАЯ ЛОГИКА =====

async def message(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id
    text = update.message.text

    if user not in user_data:
        user_data[user] = {}

    data = user_data[user]


    if "target" not in data:

        data["target"] = text

        await update.message.reply_text("Как зовут человека?")

        return


    if "name" not in data:

        data["name"] = text

        await update.message.reply_text("От кого песня?")

        return


    if "from" not in data:

        data["from"] = text

        await update.message.reply_text("Какой повод для песни?")

        return


    if "occasion" not in data:

        data["occasion"] = text

        await update.message.reply_text("Опишите человека или событие")

        return


    if "description" not in data:

        data["description"] = text

        await update.message.reply_text("Стиль песни? (Поп / Рэп / Рок)")

        return


    if "style" not in data:

        data["style"] = text

        await update.message.reply_text("Какое настроение песни?")

        return


    if "mood" not in data:

        data["mood"] = text


        free_used,credits = get_user(user)


        if free_used == 0:

            use_free(user)


        elif credits > 0:

            use_credit(user)


        else:

            await update.message.reply_text(

            "Бесплатная песня закончилась.\n\nНапиши /ref и пригласи друга чтобы получить новую генерацию 🎵"

            )

            return


        prompt = build_prompt(data)


        await update.message.reply_text("🎵 Генерирую песню...")


        r = requests.post(

        SUNO_URL,

        headers={"Authorization":f"Bearer {SUNO_API_KEY}"},

        json={"prompt":prompt}

        )


        audio = r.json()["audio_url"]


        song = requests.get(audio)


        file = f"{user}.mp3"


        with open(file,"wb") as f:

            f.write(song.content)


        await update.message.reply_audio(open(file,"rb"))


        user_data[user] = {}


# ===== ЗАПУСК =====

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("ref",ref))
app.add_handler(MessageHandler(filters.TEXT,message))

app.run_polling()
