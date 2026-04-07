import sqlite3
import db

def set_rating(user_id, post_id, rating):
    rows = db.query("SELECT 1 FROM ratings WHERE user_id=? AND post_id=?", [user_id, post_id])
    if rows:
        db.execute("UPDATE ratings SET rating=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND post_id=?", [rating, user_id, post_id])
    else:
        db.execute("INSERT INTO ratings (user_id, post_id, rating) VALUES (?, ?, ?)", [user_id, post_id, rating])

def get_user_rating(user_id, post_id):
    rows = db.query("SELECT rating FROM ratings WHERE user_id=? AND post_id=?", [user_id, post_id])
    return rows[0]["rating"] if rows else None

def get_rating_stats_for_posts(post_ids):
    if not post_ids:
        return {}
    placeholders = ",".join(["?"] * len(post_ids))
    sql = f"""
        SELECT post_id, AVG(rating) AS avg_rating, COUNT(*) AS cnt
        FROM ratings
        WHERE post_id IN ({placeholders})
        GROUP BY post_id
    """
    rows = db.query(sql, post_ids)
    return {r["post_id"]: {"avg": r["avg_rating"], "count": r["cnt"]} for r in rows}
