import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os
import db
import config
import forum
import users
import likes
import ratings
import secrets
from flask import abort

app = Flask(__name__)
app.secret_key = config.secret_key

@app.before_request
def make_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)


def check_csrf():
    if request.form.get("csrf_token") != session.get("csrf_token"):
        abort(403)

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
        check_csrf()
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
                session["csrf_token"] = secrets.token_hex(16)
                return redirect("/frontpage")
            else:
                error = "ERROR: wrong username or password"


    return render_template("login.html", error=error)

@app.route("/frontpage", methods=["GET", "POST"])
def frontpage():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        check_csrf()
        artist = request.form["artist"]
        song = request.form["song"]
        genre = request.form["genre"]
        mood = request.form["mood"]
        comment = request.form["comment"]
        user_id = session["user_id"]

        image_file = request.files.get("image")
        image_path = None
        if image_file:
            filename = secure_filename(image_file.filename)
            os.makedirs('static/uploads', exist_ok=True)
            image_path = os.path.join('static/uploads', filename)
            image_file.save(image_path)

        sql = """INSERT INTO posts (artist, song, comment, image_path, sent_at, user_id, genre, mood)
                 VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)"""
        db.execute(sql, [artist, song, comment, image_path, user_id, genre, mood])
        return redirect("/frontpage")

    posts = forum.get_posts()
    uid = session.get("user_id")
    for p in posts:
        p["like_count"] = likes.like_count(p["id"])
        p["liked_by_me"] = likes.has_liked(uid, p["id"]) if uid else False

    for p in posts:
        p["like_count"] = likes.like_count(p["id"])
        p["liked_by_me"] = likes.has_liked(uid, p["id"]) if uid else False

    post_ids = [p["id"] for p in posts]
    stats = ratings.get_rating_stats_for_posts(post_ids)

    for p in posts:
        s = stats.get(p["id"])
        p["avg_rating"] = s["avg"] if s else None
        p["rating_count"] = s["count"] if s else 0

    return render_template("frontpage.html", posts=posts, username=session.get("username"))

@app.route("/create", methods=["POST"])
def create():
    check_csrf()
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

    post = forum.get_post(post_id)
    if not post:
        return redirect("/frontpage")
    if post["user_id"] != session["user_id"]:
        return redirect("/frontpage")

    if request.method == "GET":
        return render_template("edit.html", post=post)
    
    check_csrf()

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
        forum.update_post(post_id, artist, song, comment, image_path=image_path)
    else:
        forum.update_post(post_id, artist, song, comment)

    return redirect("/frontpage")

@app.route("/remove/<int:post_id>", methods=["GET", "POST"])
def remove_post_route(post_id):
    if "user_id" not in session:
        return redirect("/login")

    post = forum.get_post(post_id)
    if not post:
        return redirect("/frontpage")
    if post["user_id"] != session["user_id"]:
        return redirect("/frontpage")

    if request.method == "GET":
        return render_template("remove.html", post=post)
    
    check_csrf()

    if "continue" in request.form:
        forum.remove_post(post_id)
    return redirect("/frontpage")

@app.route("/search")
def search():
    query = request.args.get("query", "")
    genre = request.args.get("genre", "")
    mood = request.args.get("mood", "")
    results = forum.search_songs(query, genre, mood)

    ids = [r["id"] for r in results]
    uid = session.get("user_id")

    if ids:
        placeholders = ",".join(["?"] * len(ids))
        like_rows = db.query(
            f"SELECT post_id, COUNT(*) AS cnt FROM likes WHERE post_id IN ({placeholders}) GROUP BY post_id",
            ids
        )
        like_counts = {row["post_id"]: row["cnt"] for row in like_rows}

        liked_set = set()
        if uid:
            liked_rows = db.query(
                f"SELECT post_id FROM likes WHERE user_id = ? AND post_id IN ({placeholders})",
                [uid] + ids
            )
            liked_set = {row["post_id"] for row in liked_rows}

        rating_rows = db.query(
            f"SELECT post_id, AVG(rating) AS avg_rating, COUNT(*) AS cnt FROM ratings WHERE post_id IN ({placeholders}) GROUP BY post_id",
            ids
        )
        rating_stats = {
            row["post_id"]: (float(row["avg_rating"]) if row["avg_rating"] is not None else None, row["cnt"])
            for row in rating_rows
        }
        my_ratings = {}
        if uid:
            my_rows = db.query(
                f"SELECT post_id, rating FROM ratings WHERE user_id = ? AND post_id IN ({placeholders})",
                [uid] + ids
            )
            my_ratings = {row["post_id"]: row["rating"] for row in my_rows}

        for r in results:
            pid = r["id"]
            r["like_count"] = like_counts.get(pid, 0)
            r["liked_by_me"] = pid in liked_set
            avg, cnt = rating_stats.get(pid, (None, 0))
            r["avg_rating"] = avg
            r["rating_count"] = cnt
            r["my_rating"] = my_ratings.get(pid)

    genres = forum.get_genre()
    moods = forum.get_mood()
    return render_template("search.html", genre=genre, mood=mood, genres=genres, moods=moods, query=query, results=results)

@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    posts = users.get_posts(user_id)
    uid = session.get("user_id")
    for p in posts:
        p["like_count"] = likes.like_count(p["id"])
        p["liked_by_me"] = likes.has_liked(uid, p["id"]) if uid else False
    return render_template("user.html", user=user, posts=posts)

@app.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    if "user_id" not in session:
        return redirect("/login")
    check_csrf()
    user_id = session["user_id"]

    post = forum.get_post(post_id)
    if not post:
        return redirect(url_for("frontpage"))

    likes.toggle_like(user_id, post_id)

    back = request.args.get("from")
    if back:
        return redirect(back)
    return redirect(url_for("frontpage") + f"#post-{post_id}")

from flask import url_for

@app.route("/rate/<int:post_id>", methods=["POST"])
def rate_post(post_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    check_csrf()
    post = forum.get_post(post_id)
    if not post:
        return redirect(url_for("frontpage"))

    try:
        rating = int(request.form.get("rating", ""))
    except ValueError:
        return redirect(request.headers.get("Referer") or url_for("frontpage"))

    if rating < 1 or rating > 10:
        return redirect(request.headers.get("Referer") or url_for("frontpage"))

    ratings.set_rating(session["user_id"], post_id, rating)

    ref = request.headers.get("Referer") or url_for("frontpage")
    return redirect(ref)


if __name__ == "__main__":
    app.run(debug=True)
