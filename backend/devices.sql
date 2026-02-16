PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS devices (
    device_id INTEGER PRIMARY KEY,
    room_id INTEGER,
    device_name TEXT UNIQUE NOT NULL,
    device_type TEXT NOT NULL,
    status BOOLEAN NOT NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);
