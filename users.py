import sqlite3
import db

def get_user(user_id):
    sql = "SELECT id, username FROM users WHERE id = ?"
    result = db.query(sql, [user_id])
    return result[0] if result else None

def get_posts(user_id):
    sql = """SELECT p.id, p.artist, p.song, p.comment, p.image_path, p.sent_at, p.user_id, p.genre, p.mood
             FROM posts AS p
             WHERE p.user_id = ?
             ORDER BY p.sent_at DESC"""
    return db.query(sql, [user_id])