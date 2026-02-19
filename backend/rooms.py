




class Room:

    def __init__(self, room_id, room_name, user_id, database):

        self.room_id = room_id
        self.room_name = room_name
        self.user_id = user_id
        self.database = database


    
    def save_to_db(self):

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO rooms (room_name, user_id)
            VALUES (?, ?)
        """, (self.room_name, self.user_id))

        conn.commit()

       
        self.room_id = cursor.lastrowid

        conn.close()

        print(f"Room '{self.room_name}' saved with ID {self.room_id}")


    
    def delete_from_db(self):

        if self.room_id is None:
            print("Room has no ID, cannot delete")
            return

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM rooms
            WHERE room_id = ?
        """, (self.room_id,))

        conn.commit()
        conn.close()

        print(f"Room '{self.room_name}' deleted")


    
    def get_devices(self):

        conn = self.database.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM devices
            WHERE room_id = ?
        """, (self.room_id,))

        rows = cursor.fetchall()

        conn.close()

        return rows



    def print_info(self):

        print(f"""
        Room ID: {self.room_id}
        Name: {self.room_name}
        User ID: {self.user_id}
        """)

#Beispiel wie man  nen room mit der class erstellt


# from rooms import Room

# def main():
#     # neuen Raum erstellen
#     room = Room(room_name="Living Room", user_id=1)

#     # in Datenbank speichern
#     room.save()


