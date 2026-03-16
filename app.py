import sqlite3
from flask import Flask
from flask import redirect, render_template, request
from werkzeug.security import generate_password_hash
import db

app = Flask(__name__)

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/login")
def login():
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

    return "Account created"

if __name__ == "__main__":
    create_db()
    app.run(debug=True)
