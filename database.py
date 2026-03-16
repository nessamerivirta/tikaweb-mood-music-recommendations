import sqlite3

def create_db():
    connect = sqlite3.connect("database.db")
    cursor = connect.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                   id INTEGER PRIMARY KEY
                   username TEXT UNIQUE
                   password_hash TEXT
                   )''')
    