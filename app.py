import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import uuid
import os
import db
import config
import forum
import users
import likes
import ratings
import secrets
from flask import abort, url_for
from services.posts import enrich_posts_with_likes_and_ratings

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
        artist = request.form.get("artist", "").strip()
        song = request.form.get("song", "").strip()
        genre = request.form.get("genre", "").strip()
        mood = request.form.get("mood", "").strip()
        comment = request.form.get("comment", "").strip()
        user_id = session["user_id"]

        errors = []
        if not artist:
            errors.append("Artist is required")
        if not song:
            errors.append("Song is required")
        if not genre:
            errors.append("Genre is required")
        if not mood:
            errors.append("Mood is required")

        if errors:
            posts = forum.get_posts()
            uid = session.get("user_id")
            posts = enrich_posts_with_likes_and_ratings(posts, uid)
            genres = forum.get_genre()
            moods = forum.get_mood()
            return render_template(
                "frontpage.html",
                posts=posts,
                username=session.get("username"),
                error="; ".join(errors),
                form={"artist": artist, "song": song, "genre": genre, "mood": mood, "comment": comment}
            )

        image_file = request.files.get("image")
        image_path = None
        if image_file and image_file.filename:
            filename = f"{uuid.uuid4().hex}_{secure_filename(image_file.filename)}"
            os.makedirs('static/uploads', exist_ok=True)
            image_path = os.path.join('static/uploads', filename)
            image_file.save(image_path)

        sql = """INSERT INTO posts (artist, song, comment, image_path, sent_at, user_id, genre, mood)
                 VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)"""
        db.execute(sql, [artist, song, comment, image_path, user_id, genre, mood])
        return redirect("/frontpage")

    posts = forum.get_posts()
    uid = session.get("user_id")
    posts = enrich_posts_with_likes_and_ratings(posts, uid)

    genres = forum.get_genre()
    moods = forum.get_mood()
    return render_template("frontpage.html", posts=posts, username=session.get("username"), genres=genres, moods=moods)

@app.route("/create", methods=["POST"])
def create():
    check_csrf()
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if not username or not password1:
        return render_template("register.html", error="Username and password are required", username=username)
    if password1 != password2:
        return render_template("register.html", error="Passwords do not match", username=username)
    if len(password1) < 6:
        return render_template(
        "register.html",
        error="Password must contain at least 6 characters",
        username=username
        )
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return render_template("register.html", error="Username is taken", username=username)

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

    uid = session.get("user_id")
    if results:
        results = enrich_posts_with_likes_and_ratings(results, uid)

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
    posts = enrich_posts_with_likes_and_ratings(posts, uid)
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
    if post["user_id"] == user_id:
        back = request.args.get("from")
        return redirect(back or (url_for("frontpage") + f"#post-{post_id}"))
    likes.toggle_like(user_id, post_id)

    back = request.args.get("from")
    if back:
        return redirect(back)
    return redirect(url_for("frontpage") + f"#post-{post_id}")

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
