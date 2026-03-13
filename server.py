import os
import requests

from telegram import Update,ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder,CommandHandler,MessageHandler,filters,ContextTypes

from database import *
from prompts import *
from payments import *

TOKEN = os.getenv("TELEGRAM_TOKEN")

SUNO_API = os.getenv("SUNO_API_KEY")

user_data = {}


async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    ref = None

    if context.args:
        ref = int(context.args[0])

    create_user(user,ref)

    keyboard = [
    ["❤️ Любимому"],
    ["👬 Другу"],
    ["💍 Свадьба"],
    ["🏢 Компания"]
    ]

    await update.message.reply_text(
    "Я создаю персональные песни\n\nДля кого песня?",
    reply_markup=ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
    )


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

        await update.message.reply_text("Какой повод?")

        return

    if "occasion" not in data:

        data["occasion"] = text

        await update.message.reply_text("Опишите человека")

        return

    if "description" not in data:

        data["description"] = text

        await update.message.reply_text("Стиль песни")

        return

    if "style" not in data:

        data["style"] = text

        await update.message.reply_text("Настроение")

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
            "Бесплатная песня закончилась. Купите пакет."
            )

            return

        prompt = build_prompt(data)

        await update.message.reply_text("Генерирую песню...")

        r = requests.post(
        "https://api.sunoapi.org/api/v1/generate",
        headers={"Authorization":f"Bearer {SUNO_API}"},
        json={"prompt":prompt}
        )

        audio = r.json()["audio_url"]

        song = requests.get(audio)

        file = f"{user}.mp3"

        with open(file,"wb") as f:
            f.write(song.content)

        await update.message.reply_audio(open(file,"rb"))

        user_data[user] = {}
