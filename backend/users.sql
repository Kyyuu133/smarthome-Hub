#  SQLite Datenbank für Users

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL UNIQUE,
    user_passwort TEXT NOT NULL,
    rolle TEXT NOT NULL CHECK(rolle IN ('admin', 'user'))
);

