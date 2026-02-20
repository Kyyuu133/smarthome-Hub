PRAGMA foreign_keys = ON;

-- 1. Users Tabelle
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name     TEXT    NOT NULL,
    user_password TEXT    NOT NULL,
    user_role     TEXT    NOT NULL CHECK(user_role IN ('admin', 'user'))
);

-- 2. Rooms Tabelle
CREATE TABLE IF NOT EXISTS rooms (
    room_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name VARCHAR(50) NOT NULL UNIQUE,
    user_id   INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 3. Devices Tabelle
CREATE TABLE IF NOT EXISTS devices (
    device_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id     INTEGER,
    device_name TEXT    NOT NULL UNIQUE,
    device_type TEXT    NOT NULL,
    status      BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);
