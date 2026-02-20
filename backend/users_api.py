from fastapi import FastAPI, Request, Form                      #fastapi für querys, request und form für calls und html
from fastapi.responses import HTMLResponse, RedirectResponse    #für html responses/query konvertierung
from fastapi.templating import Jinja2Templates                  #jinja template für einfachere query konvertierung von fastapi -> html
from pydantic import BaseModel                                  #basemodel für variablenmasken
from login import username_check, password_check                #import von username/password anforderungen
from typing import Optional                                 
from starlette.middleware.sessions import SessionMiddleware     #wir adden middleware sessions für session cookies
import sqlite3                                                  #db bearbeitung
import os                                                       #os für dateipfad deklarierung



app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY_123")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def get_db():
    conn = sqlite3.connect("hub.db")
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    return conn, curs

def get_current_user(request: Request):             # funktion um aktuellen nutzer zu deklarieren
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    conn, curs = get_db()
    user = curs.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return user


@app.get("/", response_class=HTMLResponse)
async def login_page(request:Request):
    
    #verbindung zur db herstellen, cursor erstellen
    conn, curs = get_db()
    curs = conn.cursor()

    #STARTPAGE - wir checken ob es schon user gibt, falls nicht soll der user admin erstellt werden.
    try: 
        curs.execute("SELECT COUNT(*) FROM users")
        user_count = curs.fetchone()[0]
    except sqlite3.OperationalError:
        user_count = 0
    
    #verbindung zur db wird geschlossen
    conn.close()

    #falls noch keine user existieren, soll als erstes die setup.html aufgerufen werden wenn man die webseite aufruft
    if user_count == 0:
        return templates.TemplateResponse("setup.html", {"request": request})
    
    #falls user existieren wird die login.html aufgerufen mit der loginmaske
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    return templates.TemplateResponse("setup.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, user_name: str = Form(...), user_password: str = Form(...)):
    conn, curs = get_db()

    user = curs.execute(
        "SELECT * FROM users WHERE user_name = ? AND user_password = ?",
        (user_name, user_password)
    ).fetchone()

    conn.close()
    
    
    if not user:
        return HTMLResponse(content="<h2>Falscher Benutzername oder Passwort.</h2>")
    
    request.session["user_id"] = user["user_id"] #Session Token setzen
    return RedirectResponse("/dashboard", status_code=303)     


#add user post request
@app.post("/add_user", response_class=HTMLResponse) #wir schreiben den postcall um, dass er über html referenziert werden kann
async def add_user(request:Request, user_name: str = Form(...), user_password: str = Form(...)): #add user erwartet json body über pydantic, html formular schickt aber form-daten, wir passen das an
    
    #username and password check
    username_result = username_check(user_name)
    if username_result != user_name:
        return HTMLResponse(content=f"<h2>Fehler: {username_result}</h2>")

    password_result = password_check(user_password, user_name)
    if password_result != user_password:
        return HTMLResponse(content=f"<h2>Fehler: {password_result}</h2>")

    conn, curs = get_db()
    #Check for Existing first user(admin)
    
    curs.execute("SELECT COUNT(*) FROM users")
    user_count = curs.fetchone()[0]

    if user_count == 0:
        role = "admin"
    else:
        role = "user"

    #Add new user
    curs.execute(
        "INSERT INTO users (user_name, user_password, user_role) VALUES (?, ?, ?)",
        (user_name, user_password, role)
    )
    
    new_user = curs.execute(
        "SELECT * FROM users WHERE user_name = ?",
        (user_name,)
    ).fetchone()    #neu angelegten user selecten für session-token

    conn.commit()
    conn.close()

    request.session["user_id"] = new_user["user_id"]    #session-token callen 

    return RedirectResponse("/dashboard", status_code=303)  #user direkt eingeloggt nach anlegen

#{"message": f"User '{user.user_name}' wurde als {role} angelegt"}


#role update functino and query
@app.post("/update_role")
async def update_user_role(request: Request, target_user_id: int = Form(...), user_name: str = Form(...), new_role: str = Form(...)):

    current_user = get_current_user(request)    #update role so umgeschrieben dass nur admin rollen verändern kann
    if not current_user:
        return RedirectResponse("/", status_code=303)   #falls kein user eingeloggt - zurück auf startseite

    if current_user["user_role"] != "admin":            #falls nicht admin sondern nur user - error
        return HTMLResponse("<h2>Keine Berechtigung.</h2>")
    
    #db connnection
    conn, curs = get_db()

    if current_user["user_id"] == target_user_id and new_role == "user": #falls admin sich selber auf user downgraden will

            admin_count = curs.execute(         
                "SELECT COUNT(*) FROM users WHERE user_role = 'admin'"
            ).fetchone()[0]
                                                                        #nur möglich wenn es mind. einen anderen admin gibt
            if admin_count <= 1:
                conn.close()
                return HTMLResponse("<h2>Es muss mindestens ein Admin existieren.</h2>")

    curs.execute(
        "UPDATE users SET user_role = ? WHERE user_id = ?",
        (new_role, target_user_id)
    )

    #connection close and update
    conn.commit()
    conn.close()

    return RedirectResponse("/dashboard", status_code=303) #redirect auf dashboard



#update password function and query
@app.post("/update_password")   #für html angepasst, if user exists check rausgenommen weil update password nur passieren kann wenn user eingeloggt ist und somit existiert
async def update_user_password(request: Request, target_user_id: int = Form(...), new_user_password: str = Form(...)):
    
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/", status_code=303)       #falls user nicht existiert/eingeloggt - zurück zur startseite

    # User darf eigenes Passwort ändern
    if current_user["user_id"] != target_user_id:           #user kann eigenes passwort ändern
        # nur Admin darf andere ändern
        if current_user["user_role"] != "admin":            #nur admin kann rollen von anderen usern ändern
            return HTMLResponse("<h2>Keine Berechtigung.</h2>")
    
    #db connection
    conn, curs = get_db()

    curs.execute(                                           #neues user passwort wird in db geschrieben für target user id - admin option
        "UPDATE users SET user_password = ? WHERE user_id = ?",
        (new_user_password, target_user_id)
    )

    #connection close and update
    conn.commit()
    conn.close()

    return RedirectResponse("/dashboard", status_code=303) #zurück zum dashboard

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/", status_code=303)

    conn, curs = get_db()

    # eingeloggten User holen
    curs.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = curs.fetchone()

    all_users = []

    # wenn admin → alle user holen
    if user["user_role"] == "admin":
        curs.execute("SELECT * FROM users")
        all_users = curs.fetchall()

    conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "all_users": all_users      
    })


@app.get("/logout")             #logout funktion, session beenden
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


#adminrole wird zweimal vergeben, check richtig referenzieren user_id hardcode
#variablennamen verändert uniform englisch rolle - role, passwort - password
#update password für html angepasst put-post, user exists check raus,
#update role

