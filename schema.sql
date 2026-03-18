CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    artist TEXT,
    song TEXT,
    comment TEXT,
    image_path TEXT,
    sent_at TEXT,
    user_id INTEGER REFERENCES users

);
