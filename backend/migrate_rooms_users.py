import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "hub.db")

conn = sqlite3.connect(db_path)
curs = conn.cursor()

curs.execute("""
    CREATE TABLE IF NOT EXISTS room_users (
        room_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        room_name TEXT,
        user_name TEXT,
        user_role TEXT,
        PRIMARY KEY (room_id, user_id),
        FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
""")

conn.commit()
conn.close()

#user_name, user_role, room_name geadded in room_users geadded