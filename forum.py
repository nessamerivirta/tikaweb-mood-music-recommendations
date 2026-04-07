import sqlite3
import db

def create_userdb():
    connect = sqlite3.connect("database.db")
    cursor = connect.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')
    connect.commit()
    connect.close()

def create_postdb():
    connect = sqlite3.connect("database.db")
    cursor = connect.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                artist TEXT,
                song TEXT,
                comment TEXT,
                image_path TEXT,
                sent_at TEXT,
                user_id INTEGER REFERENCES users,
                category TEXT
        )
    ''')
    connect.commit()
    connect.close()

def create_likesdb():
    connect = sqlite3.connect("database.db")
    cursor = connect.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, post_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    """)
    connect.commit()
    connect.close()

create_userdb()
create_postdb()
create_likesdb()

def get_posts():
    sql = """SELECT p.id, p.artist, p.song, p.comment, p.image_path, p.sent_at, p.user_id, p.category, u.username
             FROM posts p
             JOIN users u
             ON p.user_id = u.id
             ORDER BY p.sent_at DESC"""
    return db.query(sql)

def get_post(post_id):
    sql = """
        SELECT id, artist, song, comment, image_path, sent_at, user_id, category
        FROM posts
        WHERE id = ?
    """
    rows = db.query(sql, [post_id])
    return rows[0] if rows else None

def remove_post(post_id):
    sql = "DELETE FROM posts WHERE id = ?"
    db.execute(sql, [post_id])

def update_post(post_id, artist, song, comment, image_path=None, category=None):
    if image_path is not None and category is not None:
        sql = "UPDATE posts SET artist = ?, song = ?, comment = ?, image_path = ?, category = ? WHERE id = ?"
        db.execute(sql, [artist, song, comment, image_path, category, post_id])
    elif image_path is not None:
        sql = "UPDATE posts SET artist = ?, song = ?, comment = ?, image_path = ? WHERE id = ?"
        db.execute(sql, [artist, song, comment, image_path, post_id])
    elif category is not None:
        sql = "UPDATE posts SET artist = ?, song = ?, comment = ?, category = ? WHERE id = ?"
        db.execute(sql, [artist, song, comment, category, post_id])
    else:
        sql = "UPDATE posts SET artist = ?, song = ?, comment = ? WHERE id = ?"
        db.execute(sql, [artist, song, comment, post_id])

def search_songs(query, category):
    base_sql = """
        SELECT p.id AS post_id,
               p.artist,
               p.song,
               p.comment,
               p.image_path,
               p.sent_at,
               p.category,
               u.username,
               u.id AS user_id
        FROM posts p
        JOIN users u ON u.id = p.user_id
        WHERE 1=1
    """
    params = []
    if query:
        like = f"%{query}%"
        base_sql += " AND (p.artist LIKE ? OR p.song LIKE ? OR p.comment LIKE ? OR p.category LIKE ?)"
        params += [like, like, like, like]

    if category:
        base_sql += " AND p.category = ?"
        params.append(category)

    base_sql += " ORDER BY p.sent_at DESC"
    return db.query(base_sql, params)

def get_categories():
    rows = db.query("SELECT DISTINCT category FROM posts WHERE category IS NOT NULL AND category <> '' ORDER BY category")
    return [r["category"] for r in rows]
