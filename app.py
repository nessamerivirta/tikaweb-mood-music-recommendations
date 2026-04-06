import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os
import db
import config
import users
from flask import abort

app = Flask(__name__)
app.secret_key = config.secret_key

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

create_userdb()
create_postdb()

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


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        sql = "SELECT id, password_hash FROM users WHERE username = ?"
        results = db.query(sql, [username])
        if not results:
            error = "ERROR: wrong username or password"
        else:
            row = results[0]
            user_id = row["id"]
            password_hash = row["password_hash"]
            if check_password_hash(password_hash, password):
                session["username"] = username
                session["user_id"] = user_id
                return redirect("/frontpage")
            else:
                error = "ERROR: wrong username or password"


    return render_template("login.html", error=error)

@app.route("/frontpage", methods=["GET", "POST"])
def frontpage():
    print("SESSION DEBUG:", dict(session), flush=True)
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        artist = request.form["artist"]
        song = request.form["song"]
        category = request.form["category"]
        comment = request.form["comment"]
        user_id = session["user_id"]

        image_file = request.files.get("image")
        image_path = None
        if image_file:
            filename = secure_filename(image_file.filename)
            os.makedirs('static/uploads', exist_ok=True)
            image_path = os.path.join('static/uploads', filename)
            image_file.save(image_path)

        sql = """INSERT INTO posts (artist, song, comment, image_path, sent_at, user_id, category)
                 VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)"""
        db.execute(sql, [artist, song, comment, image_path, user_id, category])
        return redirect("/frontpage")

    posts = get_posts()
    return render_template("frontpage.html", posts=posts, username=session.get("username"))

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return "ERROR: passwords do not match"
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "ERROR: username taken"

    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    if "user_id" not in session:
        return redirect("/login")

    post = get_post(post_id)
    if not post:
        return redirect("/frontpage")
    if post["user_id"] != session["user_id"]:
        return redirect("/frontpage")

    if request.method == "GET":
        return render_template("edit.html", post=post)

    artist = request.form["artist"]
    song = request.form["song"]
    comment = request.form["comment"]
 
    image_file = request.files.get("image")
    if image_file and image_file.filename:
        from werkzeug.utils import secure_filename
        import uuid, os
        filename = f"{uuid.uuid4().hex}_{secure_filename(image_file.filename)}"
        os.makedirs('static/uploads', exist_ok=True)
        image_path = os.path.join('static/uploads', filename)
        image_file.save(image_path)
        update_post(post_id, artist, song, comment, image_path=image_path)
    else:
        update_post(post_id, artist, song, comment)

    return redirect("/frontpage")

@app.route("/remove/<int:post_id>", methods=["GET", "POST"])
def remove_post_route(post_id):
    if "user_id" not in session:
        return redirect("/login")

    post = get_post(post_id)
    if not post:
        return redirect("/frontpage")
    if post["user_id"] != session["user_id"]:
        return redirect("/frontpage")

    if request.method == "GET":
        return render_template("remove.html", post=post)

    if "continue" in request.form:
        remove_post(post_id)
    return redirect("/frontpage")

@app.route("/search")
def search():
    query = request.args.get("query")
    category = request.args.get("category")
    results = search_songs(query, category) if (query or category) else []
    categories = get_categories()
    return render_template("search.html", categories=categories, category=category, query=query, results=results)

@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    posts = users.get_posts(user_id)
    return render_template("user.html", user=user, posts=posts)

if __name__ == "__main__":
    app.run(debug=True)
