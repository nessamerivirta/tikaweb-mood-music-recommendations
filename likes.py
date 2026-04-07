import sqlite3
import db

def has_liked(user_id, post_id):
    if not user_id:
        return False
    rows = db.query("SELECT 1 AS ok FROM likes WHERE user_id = ? AND post_id = ?", [user_id, post_id])
    return bool(rows)

def like_count(post_id):
    rows = db.query("SELECT COUNT(*) AS c FROM likes WHERE post_id = ?", [post_id])
    return rows[0]["c"] if rows else 0

def add_like(user_id, post_id):
    try:
        db.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)", [user_id, post_id])
        return True
    except sqlite3.IntegrityError:
        return False

def remove_like(user_id, post_id):
    db.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", [user_id, post_id])

def toggle_like(user_id, post_id):
    if has_liked(user_id, post_id):
        remove_like(user_id, post_id)
        return False
    else:
        add_like(user_id, post_id)
        return True
