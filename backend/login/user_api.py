from fastapi import FastAPI
from pydantic import BaseModel
from user_pw_check import username_check, password_check
from typing import Optional
import sqlite3

app = FastAPI()

#connect to db function
def get_db():
    '''
    Docstring for get_db
    Connects to the database and returns a cursor object
    '''
    conn = sqlite3.connect("hub.db")
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    return conn, curs

#class User
class User(BaseModel):
    '''
    Docstring for User
    Class to represent a user in the database
    '''
    user_id: Optional[int] = None
    user_name: str
    user_password: str
    user_role: Optional[str] = "user"
    
#show users
@app.get("/show_users")
async def show_users():
    '''
    Docstring for show_users
    Returns all users in the database
    '''
    #connect to db and execute sql query
    conn, curs = get_db()
    result = curs.execute("SELECT user_id, user_name, user_role  FROM users").fetchall()
    conn.close
    return result

@app.delete("/remove_user")
async def remove_user(user: User):#
    '''
    Docstring for remove_user
    Removes a user from the database
    '''
    #connect do db
    conn, curs = get_db()
    
    #Check for existing user with given id and name and deletes it if it exists
    check = curs.execute("SELECT * FROM users WHERE user_id = ? AND user_name = ?", (user.user_id, user.user_name)).fetchone()
    if check is None:
        return {"error": "User does not exist"}
    else:
        curs.execute("DELETE FROM users WHERE user_id = ? AND user_name = ?", (user.user_id, user.user_name))
        conn.commit()
        conn.close()
        return {"message": f"User {user.user_name} deleted"}

#add user post request
@app.post("/add_user")
async def add_user(user: User):
    
    #username and password check
    username_result = username_check(user.user_name)
    if username_result != user.user_name:
        return {"error": username_result}

    password_result = password_check(user.user_password, user.user_name)
    if password_result != user.user_password:
        return {"error": password_result}
    
    #Check for Existing first user(admin)
    conn, curs = get_db()
    existing = curs.execute("SELECT user_id FROM users WHERE user_id = 1").fetchone()
    
    if not existing:
        user_role = "admin"
    else:
        user_role = "user"
    
    #Add new user
    curs.execute(
        "INSERT INTO users (user_name, user_password, user_role) VALUES (?, ?, ?)",
        (user.user_name, user.user_password, user_role)
    )
    conn.commit()
    conn.close()

    return {"message": f"User '{user.user_name}' wurde als {user_role} angelegt"}
