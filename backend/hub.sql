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
    device_status      BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);


-- -- -- 4. Table column name update
-- ALTER TABLE users RENAME COLUMN user_passwort TO user_password;
-- ALTER TABLE users RENAME COLUMN rolle TO user_role;
-- ALTER TABLE devices RENAME COLUMN status TO device_status;
ALTER TABLE device_event_log ADD COLUMN device_name TEXT NOT NULL;


-- -- 5. Sensor Data
-- CREATE TABLE IF NOT EXISTS sensor_data (
--     device_id INTEGER,
--     sensor_id INTEGER PRIMARY KEY AUTOINCREMENT,
--     sensor_type TEXT NOT NULL CHECK(sensor_type IN ('temperature', 'brightness')),
--     sensor_value INTEGER NOT NULL CHECK(sensor_value in ('°C', 'lux')),
--     sensor_timestamp TEXT NOT NULL DEFAULT '',
--     FOREIGN KEY (device_id) REFERENCES devices(device_id)
-- );

-- 6. Device event log
CREATE TABLE IF NOT EXISTS device_event_log (
    event_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER,
    device_status BOOLEAN NOT NULL DEFAULT 0,
    event_timestamp TEXT NOT NULL DEFAULT '',
    temp_value INTEGER NOT NULL DEFAULT 0, -- °C
    brightness_value INTEGER NOT NULL DEFAULT 0, -- lux
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    FOREIGN KEY (device_status) REFERENCES devices(device_status) 
);

-- 7. automation
CREATE TABLE IF NOT EXISTS automation_rules (
    automation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    device_name TEXT NOT NULL DEFAULT '',
    device_status BOOLEAN NOT NULL DEFAULT 0,
    room_name TEXT NOT NULL DEFAULT '',
    temp_treshold_high INTEGER NOT NULL DEFAULT 0,
    temp_treshold_low INTEGER NOT NULL DEFAULT 0,
    brightness_treshold_high INTEGER NOT NULL DEFAULT 0,
    brightness_treshold_low INTEGER NOT NULL DEFAULT 0,    
    FOREIGN KEY (room_name) REFERENCES rooms(room_name),
    FOREIGN KEY (device_status) REFERENCES devices(device_status),
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    FOREIGN KEY (device_name) REFERENCES devices(device_name)
);