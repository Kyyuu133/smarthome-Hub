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
    room_name TEXT NOT NULL UNIQUE,
    user_id   INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 3. Devices Tabelle
CREATE TABLE IF NOT EXISTS devices (
    device_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id     INTEGER,
    device_name TEXT    NOT NULL UNIQUE,
    device_type TEXT    NOT NULL,
    device_status      BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

--4. rooms_users
CREATE TABLE IF NOT EXISTS room_users (
    room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    room_name TEXT,
    user_name TEXT,
    user_role TEXT,
    PRIMARY KEY (room_id, user_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 5. Device event log
CREATE TABLE IF NOT EXISTS device_event_log (
    event_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER,
    device_name TEXT NOT NULL DEFAULT '',
    device_type TEXT NOT NULL DEFAULT '',
    device_status BOOLEAN NOT NULL DEFAULT 0,
    event_timestamp TEXT NOT NULL DEFAULT '',
    temp_value INTEGER,
    brightness_value INTEGER,
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    FOREIGN KEY (device_name) REFERENCES devices(device_name),
    FOREIGN KEY (device_status) REFERENCES devices(device_status),
    FOREIGN KEY (device_type) REFERENCES devices(device_type)
);

-- 6. rules
CREATE TABLE IF NOT EXISTS rules (
    rules_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL DEFAULT '',
    device_name TEXT NOT NULL DEFAULT '',
    device_status BOOLEAN NOT NULL DEFAULT 0,
    device_type TEXT NOT NULL DEFAULT '',
    room_id INTEGER NOT NULL DEFAULT '', 
    room_name TEXT NOT NULL DEFAULT '',
    temp_treshold_high INTEGER NOT NULL DEFAULT 0,
    temp_treshold_low INTEGER NOT NULL DEFAULT 0,
    brightness_treshold_high INTEGER NOT NULL DEFAULT 0,
    brightness_treshold_low INTEGER NOT NULL DEFAULT 0,    
    FOREIGN KEY (device_status) REFERENCES devices(device_status),
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    FOREIGN KEY (device_name) REFERENCES devices(device_name),
    FOREIGN KEY (device_type) REFERENCES devices(device_type),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    FOREIGN KEY (room_name) REFERENCES rooms(room_name)
    );