from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_303_SEE_OTHER
from werkzeug.security import generate_password_hash, check_password_hash
from config import settings

app = FastAPI(debug=settings.DEBUG)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
templates = Jinja2Templates(directory="templates")

users_db = {}
active_websockets = set()
SESSION_KEY = "user_email"

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    user = request.session.get(SESSION_KEY)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": ""})

@app.post("/register")
async def post_register(request: Request, email: str = Form(...), password: str = Form(...)):
    if email in users_db:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Email already registered"
        })
    users_db[email] = generate_password_hash(password)
    await broadcast_notification(f"👍 New user registered: {email}")
    return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@app.post("/login")
def post_login(request: Request, email: str = Form(...), password: str = Form(...)):
    if email not in users_db:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "This email is not registered"
        })
    if not check_password_hash(users_db[email], password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Incorrect password"
        })
    request.session[SESSION_KEY] = email
    return RedirectResponse("/welcome", status_code=HTTP_303_SEE_OTHER)

@app.get("/welcome", response_class=HTMLResponse)
def welcome(request: Request):
    user = request.session.get(SESSION_KEY)
    if not user:
        return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("welcome.html", {"request": request, "user": user})

@app.get("/logout")
def logout(request: Request):
    request.session.pop(SESSION_KEY, None)
    return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

async def broadcast_notification(message: str):
    for ws in list(active_websockets):
        try:
            await ws.send_text(message)
        except Exception:
            active_websockets.remove(ws)

if settings.DEBUG:
    print("🔧 Running in DEBUG mode")
