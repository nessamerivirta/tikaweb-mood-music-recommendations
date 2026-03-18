import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key

def create_db():
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

create_db()

def get_posts():
    sql = """SELECT artist, song, comment, image_path, sent_at
             FROM posts p
             ORDER BY sent_at DESC
             JOIN users u
             ON p.user_id = u.id"""
    return db.query(sql)

@app.route("/")
def index():
    posts = get_posts()
    return render_template("index.html", posts=posts)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
    
        sql = "SELECT password_hash FROM users WHERE username = ?"
        results = db.query(sql, [username])
        if not results:
            return "ERROR: wrong username or password"
        password_hash = results[0][0]


        if check_password_hash(password_hash, password):
            session["username"] = username
            return redirect("/frontpage")
        else:
            return "ERROR: wrong username or password"
    return render_template("login.html")

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

    return redirect("/frontpage")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

app.run(debug=True)
