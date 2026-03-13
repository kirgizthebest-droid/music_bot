import sqlite3

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

    cursor.execute(
    "INSERT OR IGNORE INTO users(id,referrer) VALUES (?,?)",
    (user_id,ref)
    )

    conn.commit()


def get_user(user_id):

    cursor.execute(
    "SELECT free_used,credits FROM users WHERE id=?",
    (user_id,)
    )

    return cursor.fetchone()


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
