from fastapi import FastAPI
from pydantic import BaseModel
from login import username_check, password_check
from typing import Optional
import sqlite3

app = FastAPI()
#connect to db function
def get_db():
    conn = sqlite3.connect("hub.db")
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    return conn, curs
#class User
class User(BaseModel):
    user_name: str
    user_passwort: str
    rolle: Optional[str] = "user"

#add user post request
@app.post("/add_user")
async def add_user(user: User):
    
    #username and password check
    username_result = username_check(user.user_name)
    if username_result != user.user_name:
        return {"error": username_result}

    password_result = password_check(user.user_passwort, user.user_name)
    if password_result != user.user_passwort:
        return {"error": password_result}

    conn, curs = get_db()
    #Check for Existing first user(admin)
    existing = curs.execute("SELECT user_id FROM users WHERE user_id = 1").fetchone()

    if not existing:
        rolle = "admin"
    else:
        rolle = user.rolle
    #Add new user
    curs.execute(
        "INSERT INTO users (user_name, user_passwort, rolle) VALUES (?, ?, ?)",
        (user.user_name, user.user_passwort, rolle)
    )
    conn.commit()
    conn.close()

    return {"message": f"User '{user.user_name}' wurde als {rolle} angelegt"}

