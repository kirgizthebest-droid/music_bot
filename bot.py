import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== Логи =====
logging.basicConfig(level=logging.INFO)

# ===== Данные пользователей =====
user_data = {}
free_generation_used = set()

# ===== Токен Telegram =====
TOKEN = "ВАШ_ТЕЛЕГРАМ_ТОКЕН"  # <-- вставьте сюда токен вашего бота

# ===== Функции =====
def generate_prompt(data: dict):
    return (
        f"Создай песню для {data.get('recipient_name','')} на тему {data.get('occasion','')}, "
        f"стиль: {data.get('style','')}, настроение: {data.get('mood','')}. "
        f"Описание: {data.get('description','')}"
    )

def generate_song(prompt: str):
    """Пример генерации трека (заглушка)"""
    # Здесь будет вызов Suno API
    return "https://example.com/song.mp3"

# ===== Команды =====
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

# ===== Кнопки =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id
    data = query.data

    # Начало создания песни
    if data == "create_song":
        keyboard = [
            [InlineKeyboardButton("❤️ Для любимого человека", callback_data="lover")],
            [InlineKeyboardButton("🎂 Для друга", callback_data="friend")],
            [InlineKeyboardButton("💍 Свадебная песня", callback_data="wedding")],
            [InlineKeyboardButton("🎉 Для компании / команды", callback_data="company")],
            [InlineKeyboardButton("✨ Другое", callback_data="other_recipient")]
        ]
        await query.message.reply_text("Для кого будет песня?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Обработка выбора типа получателя
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

    # Выбор повода
    occasion_map = {
        "birthday": "День рождения",
        "wedding_occasion": "Свадьба",
        "love": "Признание в любви",
        "funny": "Шуточная песня",
        "thanks": "Благодарность",
        "event": "Праздник / событие",
        "other_occasion": "Другое"
    }
    if data in occasion_map:
        user_data[chat_id]['occasion'] = occasion_map[data]
        await query.message.reply_text(
            "Расскажи немного о человеке / паре / компании.\nМожно написать:\n"
            "• чем они занимаются\n• особенности\n• смешные моменты\n• история знакомства\n• важные воспоминания"
        )
        return

    # Выбор стиля
    style_map = {
        "pop": "Поп",
        "rap": "Рэп",
        "rock": "Рок",
        "ballad": "Душевная баллада",
        "fun": "Весёлая песня",
        "hit": "Современный хит"
    }
    if data in style_map:
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
    mood_map = {
        "romantic": "Романтичная",
        "touching": "Трогательная",
        "funny_mood": "Смешная",
        "energetic": "Энергичная",
        "other_mood": "Другое"
    }
    if data in mood_map:
        user_data[chat_id]['mood'] = mood_map[data]
        # Бесплатная генерация
        if chat_id not in free_generation_used:
            free_generation_used.add(chat_id)
            await query.message.reply_text("🎁 Ваша бесплатная песня создается...")
            prompt = generate_prompt(user_data[chat_id])
            track_url = generate_song(prompt)
            await query.message.reply_text(f"Ваша песня готова! 🎵\n{track_url}")
        else:
            await query.message.reply_text("Вы использовали бесплатную генерацию. Платные функции пока отключены в этой тестовой версии.")
        return

# ===== Текстовые сообщения =====
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

# ===== Запуск =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()
