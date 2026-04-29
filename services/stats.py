import db

def get_like_counts_for_posts(ids):
    if not ids:
        return {}
    placeholders = ",".join(["?"] * len(ids))
    sql = f"SELECT post_id, COUNT(*) AS cnt FROM likes WHERE post_id IN ({placeholders}) GROUP BY post_id"
    rows = db.query(sql, ids)
    return {row["post_id"]: row["cnt"] for row in rows}

def get_liked_set_for_user(user_id, ids):
    if not ids or not user_id:
        return set()
    placeholders = ",".join(["?"] * len(ids))
    sql = f"SELECT post_id FROM likes WHERE user_id = ? AND post_id IN ({placeholders})"
    rows = db.query(sql, [user_id] + ids)
    return {row["post_id"] for row in rows}

def get_rating_stats_for_posts(ids):
    if not ids:
        return {}
    placeholders = ",".join(["?"] * len(ids))
    sql = f"SELECT post_id, AVG(rating) AS avg_rating, COUNT(*) AS cnt FROM ratings WHERE post_id IN ({placeholders}) GROUP BY post_id"
    rows = db.query(sql, ids)
    return {
        row["post_id"]: (float(row["avg_rating"]) if row["avg_rating"] is not None else None, row["cnt"])
        for row in rows
    }

def get_my_ratings_for_user(user_id, ids):
    if not ids or not user_id:
        return {}
    placeholders = ",".join(["?"] * len(ids))
    sql = f"SELECT post_id, rating FROM ratings WHERE user_id = ? AND post_id IN ({placeholders})"
    rows = db.query(sql, [user_id] + ids)
    return {row["post_id"]: row["rating"] for row in rows}
