import os
import requests

from telegram import (
Update,
ReplyKeyboardMarkup,
InlineKeyboardButton,
InlineKeyboardMarkup
)

from telegram.ext import (
ApplicationBuilder,
CommandHandler,
MessageHandler,
CallbackQueryHandler,
filters,
ContextTypes
)

from prompts import build_prompt
from database import *
from payments import *

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUNO_API_KEY = os.getenv("SUNO_API_KEY")

SUNO_URL = "https://api.sunoapi.org/api/v1/generate"

user_data = {}


# START

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["❤️ Для любимого человека"],
        ["👬 Для друга"],
        ["💍 Свадьба"],
        ["🏢 Для компании"]
    ]

    await update.message.reply_text(
        "🎵 Я создаю персональные песни!\n\nДля кого песня?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# ОБРАБОТКА СООБЩЕНИЙ

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id
    text = update.message.text

    if user not in user_data:
        user_data[user] = {}

    data = user_data[user]

    if "target_type" not in data:
        data["target_type"] = text
        await update.message.reply_text("Как зовут человека?")
        return

    if "name" not in data:
        data["name"] = text
        await update.message.reply_text("От кого песня?")
        return

    if "from" not in data:
        data["from"] = text
        await update.message.reply_text("Повод?")
        return

    if "occasion" not in data:
        data["occasion"] = text
        await update.message.reply_text("Опишите человека")
        return

    if "description" not in data:
        data["description"] = text
        await update.message.reply_text("Стиль песни? (Поп / Рэп / Рок)")
        return

    if "style" not in data:
        data["style"] = text
        await update.message.reply_text("Настроение песни?")
        return

    if "mood" not in data:

        data["mood"] = text

        free_used, credits = get_user(user)

        if free_used == 0:

            use_free(user)

        elif credits > 0:

            use_credit(user)

        else:

            keyboard = [
                [
                    InlineKeyboardButton("3 песни",callback_data="pack_3")
                ],
                [
                    InlineKeyboardButton("10 песен",callback_data="pack_10")
                ],
                [
                    InlineKeyboardButton("50 песен",callback_data="pack_50")
                ]
            ]

            await update.message.reply_text(
                "Бесплатная песня закончилась.\nКупите пакет:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            return

        prompt = build_prompt(data)

        await update.message.reply_text("🎵 Генерирую песню...")

        r = requests.post(
            SUNO_URL,
            headers={"Authorization":f"Bearer {SUNO_API_KEY}"},
            json={"prompt":prompt}
        )

        audio_url = r.json()["audio_url"]

        song = requests.get(audio_url)

        file = f"{user}.mp3"

        with open(file,"wb") as f:
            f.write(song.content)

        await update.message.reply_audio(open(file,"rb"))

        user_data[user] = {}



# ПОКУПКА

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    package = query.data

    prices = create_invoice(package)

    await context.bot.send_invoice(

        chat_id=query.message.chat_id,

        title="Пакет песен",

        description=package,

        payload=package,

        provider_token="",

        currency="XTR",

        prices=prices

    )


# ПОДТВЕРЖДЕНИЕ ОПЛАТЫ

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id

    package = update.message.successful_payment.invoice_payload

    credits = PACKAGES[package]["credits"]

    add_credits(user,credits)

    await update.message.reply_text(
        f"Оплата прошла успешно!\nНачислено {credits} песен."
    )


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT,message))
app.add_handler(CallbackQueryHandler(buy))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT,successful_payment))

app.run_polling()
