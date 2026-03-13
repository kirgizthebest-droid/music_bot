from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# ====== Настройки через переменные окружения ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUNO_API_URL = "https://api.sunoapi.org/api/v1/generate"
SUNO_API_KEY = os.environ.get("SUNO_API_KEY")

if not TELEGRAM_TOKEN or not SUNO_API_KEY:
    raise ValueError("Пожалуйста, установите TELEGRAM_TOKEN и SUNO_API_KEY в переменные окружения!")

# ====== Ограничение бесплатной генерации ======
FREE_LIMIT = 1
user_usage = {}  # {chat_id: last_date}

def check_free_limit(chat_id):
    today = datetime.now().date()
    last_used = user_usage.get(chat_id)
    if last_used == today:
        return False
    user_usage[chat_id] = today
    return True

# ====== Основной маршрут ======
@app.route("/generate_telegram", methods=["POST"])
def generate_telegram():
    data = request.json
    chat_id = data.get("chat_id")
    prompt = data.get("prompt")

    if not chat_id or not prompt:
        return jsonify({"status": "error", "message": "Нужны chat_id и prompt"}), 400

    # ===== Проверка лимита =====
    if not check_free_limit(chat_id):
        return jsonify({"status": "error", "message": "Вы уже сделали бесплатную песню сегодня"}), 403

    # ===== Отправка запроса в Suno =====
    try:
        response = requests.post(
            SUNO_API_URL,
            headers={
                "Authorization": f"Bearer {SUNO_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": prompt,
                "customMode": False,
                "instrumental": False,
                "model": "V5"
            },
            timeout=60
        )
        response.raise_for_status()
        audio_url = response.json().get("audio_url")
        if not audio_url:
            return jsonify({"status": "error", "message": "Suno не вернул аудио"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Suno ошибка: {str(e)}"}), 500

    # ===== Скачиваем mp3 =====
    try:
        audio_file = requests.get(audio_url)
        filename = f"song_{chat_id}.mp3"
        with open(filename, "wb") as f:
            f.write(audio_file.content)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка скачивания mp3: {str(e)}"}), 500

    # ===== Отправка mp3 через Telegram =====
    try:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
        with open(filename, "rb") as f:
            requests.post(telegram_url, data={"chat_id": chat_id}, files={"audio": f})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка отправки в Telegram: {str(e)}"}), 500
    finally:
        # Удаляем файл mp3 после отправки
        if os.path.exists(filename):
            os.remove(filename)

    return jsonify({"status": "ok"})

# ===== Запуск сервера ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
