import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os
import db
import config

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
                picture BLOB
        )
    ''')
    connect.commit()
    connect.close()

create_userdb()
create_postdb()

def get_posts():
    sql = """SELECT p.id, p.artist, p.song, p.comment, p.image_path, p.sent_at, u.username
             FROM posts p
             JOIN users u
             ON p.user_id = u.id
             ORDER BY p.sent_at DESC"""
    return db.query(sql)

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
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        artist = request.form["artist"]
        song = request.form["song"]
        comment = request.form["comment"]
        user_id = session["user_id"]

        image_file = request.files.get("image")
        image_path = None
        if image_file:
            filename = secure_filename(image_file.filename)
            os.makedirs('static/uploads', exist_ok=True)
            image_path = os.path.join('static/uploads', filename)
            image_file.save(image_path)

        sql = """INSERT INTO posts (artist, song, comment, image_path, sent_at, user_id)
                 VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)"""
        db.execute(sql, [artist, song, comment, image_path, user_id])
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
    del session["username"]
    return redirect("/")

app.run(debug=True)
