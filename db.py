import sqlite3

conn = sqlite3.connect('database.db')

conn.execute('''CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
)''')

conn.execute('''CREATE TABLE complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT,
    status TEXT
)''')

conn.commit()
conn.close()

print("Database Created ✅")