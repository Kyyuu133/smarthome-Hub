import sqlite3

with sqlite3.connect("devices.db") as conn:
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()


# hier ist der Table mit der Referenz zum Foreign Key von Timo - kann aber erst referenziert werden wenn der andere Table auch existiert. Daher erstmal Platzhalter

# cursor.execute("""
#             CREATE TABLE IF NOT EXISTS devices (
#             device_id INTEGER PRIMARY KEY,
#             room_id INTEGER,
#             device_name TEXT UNIQUE NOT NULL,
#             device_type TEXT NOT NULL,
#             status BOOLEAN NOT NULL,
#             FOREIGN KEY (room_id) REFERENCES rooms (room_id)
#             )
#             """)



cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
            device_id INTEGER PRIMARY KEY,
            room_id INTEGER,
            device_name TEXT UNIQUE NOT NULL,
            device_type TEXT NOT NULL,
            status BOOLEAN NOT NULL
            )
            """)



conn.commit()
print("Tabelle erfolgreich erstellt!")
conn.close()
print("Verbindung geschlossen!")