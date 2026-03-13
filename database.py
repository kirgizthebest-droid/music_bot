import sqlite3

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
free_used INTEGER DEFAULT 0,
credits INTEGER DEFAULT 0
)
""")

conn.commit()


def get_user(user_id):
    cursor.execute("SELECT free_used,credits FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("INSERT INTO users(id) VALUES(?)", (user_id,))
        conn.commit()
        return 0,0

    return row


def add_credits(user_id, amount):
    cursor.execute(
        "UPDATE users SET credits = credits + ? WHERE id=?",
        (amount, user_id)
    )
    conn.commit()


def use_credit(user_id):
    cursor.execute(
        "UPDATE users SET credits = credits - 1 WHERE id=?",
        (user_id,)
    )
    conn.commit()


def use_free(user_id):
    cursor.execute(
        "UPDATE users SET free_used = 1 WHERE id=?",
        (user_id,)
    )
    conn.commit()
