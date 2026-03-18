import sqlite3

def connect_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def query(sql, params=()):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def execute(sql, params=()):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()
