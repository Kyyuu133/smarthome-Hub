CREATE TABLE IF NOT EXISTS `rooms` (
    room_id     INT          PRIMARY KEY AUTOINCREMENT,
    room_name   VARCHAR(50)  NOT NULL UNIQUE,
    device_id   INT,
    device_name VARCHAR(100),
    user_id     INT,
    FOREIGN KEY (device_id)   REFERENCES devices(device_id),
    FOREIGN KEY (device_name) REFERENCES devices(device_name),
    FOREIGN KEY (user_id)     REFERENCES users(user_id)
);