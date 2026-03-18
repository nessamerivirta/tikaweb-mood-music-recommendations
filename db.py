import sqlite3

def connect_db():
    return sqlite3.connect("database.db")

def query(sql, params=()):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()
    return results

def execute(sql, params=()):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    conn.close()