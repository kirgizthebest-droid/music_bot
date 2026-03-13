import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Логи
logging.basicConfig(level=logging.INFO)

# Данные пользователей
user_data = {}
free_generation_used = set()

# Настройки
TOKEN = os.getenv("8069144735:AAEm_36bw0UctO7d88L_3XWjKIgiIGg_kLY")  # Токен бота Telegram
ROBOX_LOGIN = os.getenv("ROBOX_LOGIN")  # Robokassa login
ROBOX_PASS1 = os.getenv("ROBOX_PASS1")  # Robokassa пароль1
ROBOX_PASS2 = os.getenv("ROBOX_PASS2")  # Robokassa пароль2
CURRENCY = "RUB"

# ---------------------
# Функции генерации трека
# ---------------------
def generate_prompt(data: dict):
    return (
        f"Создай песню для {data['recipient_name']} на тему {data['occasion']}, "
        f"стиль: {data['style']}, настроение: {data['mood']}. "
        f"Описание: {data['description']}"
    )

def generate_song(prompt: str):
    """
    Тут должен быть ваш вызов Suno API.
    Для примера возвращаем ссылку-заглушку.
    """
    # Пример вызова:
    # response = requests.post("SUNO_API_URL", json={"prompt": prompt})
    # track_url = response.json()["track_url"]
    track_url = "https://example.com/song.mp3"
    return track_url

# ---------------------
# Старт
# ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {}
    keyboard = [[InlineKeyboardButton("Создать песню", callback_data="create_song")]]
    await update.message.reply_text(
        "Привет! Я бот, который создаёт песни на заказ. 🎵\n"
        "Первая песня бесплатна! 🎁\n"
        "Вы можете сделать песню для любимого человека, друга, свадьбы, компании или просто шутку!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------
# Кнопки
# ---------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id
    data = query.data

    if data == "create_song":
        # Вопрос 1: Для кого песня
        keyboard = [
            [InlineKeyboardButton("❤️ Для любимого человека", callback_data="lover")],
            [InlineKeyboardButton("🎂 Для друга", callback_data="friend")],
            [InlineKeyboardButton("💍 Свадебная песня", callback_data="wedding")],
            [InlineKeyboardButton("🎉 Для компании / команды", callback_data="company")],
            [InlineKeyboardButton("✨ Другое", callback_data="other_recipient")]
        ]
        await query.message.reply_text("Для кого будет песня?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Обработка выбора
    if data in ["lover", "friend", "wedding", "company", "other_recipient"]:
        user_data[chat_id]['recipient_type'] = data
        if data == "wedding":
            await query.message.reply_text("Как зовут пару?\nПример: Оля и Дима")
        elif data == "company":
            await query.message.reply_text("Название компании?\nПример: Coffelub")
        elif data in ["lover", "friend"]:
            await query.message.reply_text("Как зовут человека?\nПример: Оля")
        else:
            await query.message.reply_text("Введите свой вариант для кого песня")
        return

    # Вопрос 4: Повод
    if data in ["birthday", "wedding_occasion", "love", "funny", "thanks", "event", "other_occasion"]:
        occasion_map = {
            "birthday": "День рождения",
            "wedding_occasion": "Свадьба",
            "love": "Признание в любви",
            "funny": "Шуточная песня",
            "thanks": "Благодарность",
            "event": "Праздник / событие",
            "other_occasion": "Другое"
        }
        user_data[chat_id]['occasion'] = occasion_map[data]
        await query.message.reply_text(
            "Расскажи немного о человеке / паре / компании.\nМожно написать:\n"
            "• чем они занимаются\n• особенности\n• смешные моменты\n• история знакомства\n• важные воспоминания"
        )
        return

    # Выбор стиля
    if data in ["pop","rap","rock","ballad","fun","hit"]:
        style_map = {
            "pop": "Поп",
            "rap": "Рэп",
            "rock": "Рок",
            "ballad": "Душевная баллада",
            "fun": "Весёлая песня",
            "hit": "Современный хит"
        }
        user_data[chat_id]['style'] = style_map[data]
        keyboard = [
            [InlineKeyboardButton("❤️ Романтичная", callback_data="romantic")],
            [InlineKeyboardButton("🥹 Трогательная", callback_data="touching")],
            [InlineKeyboardButton("😂 Смешная", callback_data="funny_mood")],
            [InlineKeyboardButton("🔥 Энергичная", callback_data="energetic")],
            [InlineKeyboardButton("✨ Другое", callback_data="other_mood")]
        ]
        await query.message.reply_text("Настроение песни?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Выбор настроения
    if data in ["romantic","touching","funny_mood","energetic","other_mood"]:
        mood_map = {
            "romantic": "Романтичная",
            "touching": "Трогательная",
            "funny_mood": "Смешная",
            "energetic": "Энергичная",
            "other_mood": "Другое"
        }
        user_data[chat_id]['mood'] = mood_map[data]

        # Проверка бесплатной генерации
        if chat_id not in free_generation_used:
            free_generation_used.add(chat_id)
            await query.message.reply_text("🎁 Ваша бесплатная песня создается...")
            prompt = generate_prompt(user_data[chat_id])
            track_url = generate_song(prompt)
            await query.message.reply_text(f"Ваша песня готова! 🎵\n{track_url}")
        else:
            # Предложение покупки
            keyboard = [
                [InlineKeyboardButton("1 песня - 350 ₽", callback_data="buy_1")],
                [InlineKeyboardButton("3 песни - 1000 ₽", callback_data="buy_3")],
                [InlineKeyboardButton("10 песен - 2500 ₽", callback_data="buy_10")],
                [InlineKeyboardButton("50 песен - 4000 ₽", callback_data="buy_50")]
            ]
            await query.message.reply_text("Вы использовали бесплатную генерацию. Выберите пакет:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Обработка покупки
    if data.startswith("buy_"):
        price_map = {
            "buy_1": 350,
            "buy_3": 1000,
            "buy_10": 2500,
            "buy_50": 4000
        }
        amount = price_map[data]
        # Формирование ссылки Robokassa
        # Простейший вариант: ссылка на оплату
        order_id = f"{chat_id}_{data}"
        payment_url = f"https://auth.robokassa.ru/Merchant/Index.aspx?MerchantLogin={ROBOX_LOGIN}&OutSum={amount}&InvoiceID={order_id}&Description=Покупка песен&Culture=ru"
        await query.message.reply_text(f"Оплатите через Robokassa:\n{payment_url}")
        return

# ---------------------
# Обработка текстовых сообщений
# ---------------------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    if chat_id not in user_data:
        user_data[chat_id] = {}

    if 'recipient_name' not in user_data[chat_id]:
        user_data[chat_id]['recipient_name'] = text
        await update.message.reply_text(
            "Расскажи немного о человеке / паре / компании.\nМожно написать:\n• чем они занимаются\n• особенности\n• смешные моменты\n• история знакомства\n• важные воспоминания"
        )
        return

    if 'description' not in user_data[chat_id]:
        user_data[chat_id]['description'] = text
        keyboard = [
            [InlineKeyboardButton("Поп", callback_data="pop")],
            [InlineKeyboardButton("Рэп", callback_data="rap")],
            [InlineKeyboardButton("Рок", callback_data="rock")],
            [InlineKeyboardButton("Душевная баллада", callback_data="ballad")],
            [InlineKeyboardButton("Весёлая песня", callback_data="fun")],
            [InlineKeyboardButton("Современный хит", callback_data="hit")]
        ]
        await update.message.reply_text("Выберите стиль песни", reply_markup=InlineKeyboardMarkup(keyboard))
        return

# ---------------------
# Запуск
# ---------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()
