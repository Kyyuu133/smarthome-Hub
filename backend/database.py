# database.py
import sqlite3

class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn