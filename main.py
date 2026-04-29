from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import json
import os
import re

app = FastAPI(title="The Internet Scrapbook API")

# --- SETTINGS & DATABASE ---
DATA_FILE = "data.json"
BLOCKED_FILE = "blocked.txt"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "fallback_password_here") 

def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except: return []
    return []

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_banned_words():
    if os.path.exists(BLOCKED_FILE):
        with open(BLOCKED_FILE, "r") as f:
            return [line.strip().lower() for line in f if line.strip()]
    return []

db = load_db()
app_settings = {
    "filters_enabled": True,
    "banned_words": load_banned_words()
}

# --- MODELS ---
class Pin(BaseModel):
    id: Optional[int] = None
    site_name: str
    url: str
    comment: str
    added_by: str
    timestamp: Optional[str] = None

# --- UI STYLING ---
STYLE = """
<style>
    body { font-family: sans-serif; background: #fafafa; color: #3b4151; margin: 0; padding: 0; }
    nav { background: #1b1b1b; padding: 10px 20px; display: flex; gap: 20px; align-items: center; }
    nav a { color: #fff; text-decoration: none; font-weight: bold; font-size: 14px; }
    .container { max-width: 800px; margin: 40px auto; padding: 20px; }
    h1 { border-bottom: 1px solid rgba(59,65,81,.3); padding-bottom: 10px; }
    .search-box { margin-bottom: 20px; display: flex; gap: 10px; }
    .form-container { background: #fff; border: 1px solid #61affe; border-radius: 4px; padding: 20px; margin-bottom: 30px; }
    input, textarea { width: 100%; padding: 8px; border: 1px solid #d9d9d9; border-radius: 4px; box-sizing: border-box; margin-bottom: 10px;}
    button { background: #61affe; color: white; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; cursor: pointer; }
    .card { background: #fff; border: 1px solid #e8e8e8; border-radius: 4px; margin-bottom: 15px; padding: 15px; }
    .method-badge { background: #61affe; color: #fff; padding: 4px 12px; border-radius: 3px; font-weight: bold; font-size: 12px; }
    table { width: 100%; border-collapse: collapse; background: white; margin-top: 20px; }
    th, td { border: 1px solid #e8e8e8; padding: 10px; text-align: left; }
</style>
"""

NAV_BAR = """
<nav>
    <a href="/">HOME</a>
    <a href="/scrapbook">SCRAPBOOK</a>
    <a href="/test">MY_TESTS</a>
    <a href="/docs">API_DOCS</a>
</nav>
"""

# --- FILTRATION ENGINE ---
def apply_filters(text: str):
    if not app_settings["filters_enabled"]:
        return text
    words = text.split()
    for i, word in enumerate(words):
        clean = re.sub(r'[^\w]', '', word).lower()
        if clean in app_settings["banned_words"]:
            words[i] = "[REDACTED]"
    return " ".join(words)

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def root():
    return f"""<html><head>{STYLE}</head><body>{NAV_BAR}<div class="container">
    <h1>Internet Scrapbook</h1>
    <p>Filter Status: <strong>{"ACTIVE" if app_settings['filters_enabled'] else "OFF"}</strong></p>
    <a href="/scrapbook" style="color:#61affe">View the Scrapbook &rarr;</a>
    </div></body></html>"""

@app.get("/scrapbook", response_class=HTMLResponse)
async def view_scrapbook(q: Optional[str] = None):
    results = db
    if q:
        results = [p for p in db if q.lower() in p['site_name'].lower() or q.lower() in p['comment'].lower()]
    
    cards = "".join([f"""<div class="card">
        <span class="method-badge">GET</span> <strong>{p['site_name']}</strong>
        <p>"{apply_filters(p['comment'])}"</p>
        <small>By: {p['added_by']} • {p['timestamp']}</small>
    </div>""" for p in reversed(results)])

    return f"""<html><head>{STYLE}</head><body>{NAV_BAR}<div class="container">
    <h1>Global Scrapbook</h1>
    <form class="search-box" action="/scrapbook" method="get">
        <input type="text" name="q" placeholder="Search sites or comments..." value="{q if q else ''}">
        <button type="submit">Search</button>
    </form>
    {cards if cards else "<p>No results found.</p>"}
    </div></body></html>"""

@app.get("/test", response_class=HTMLResponse)
async def view_test():
    my_name = "Prophet"
    my_pins = [p for p in db if p['added_by'].lower() == my_name.lower()]
    cards = "".join([f"""<div class="card"><strong>{p['site_name']}</strong><p>"{p['comment']}"</p></div>""" for p in reversed(my_pins)])
    
    return f"""<html><head>{STYLE}</head><body>{NAV_BAR}<div class="container">
    <h1>Submit Test</h1>
    <div class="form-container">
        <input type="text" id="s" placeholder="Site Name"><input type="text" id="u" placeholder="URL">
        <textarea id="c" placeholder="Comment"></textarea><input type="text" id="a" value="{my_name}">
        <button onclick="postData()">Submit</button>
    </div>
    {cards}</div>
    <script>
    async function postData() {{
        const d = {{
            site_name: document.getElementById('s').value, 
            url: document.getElementById('u').value, 
            comment: document.getElementById('c').value, 
            added_by: document.getElementById('a').value
        }};
        await fetch('/pins', {{
            method: 'POST', 
            headers: {{'Content-Type': 'application/json'}}, 
            body: JSON.stringify(d)
        }});
        location.reload();
    }}
    </script></body></html>"""

# --- ADMIN PANEL ---
@app.get("/admin-portal", response_class=HTMLResponse)
async def admin(pw: Optional[str] = None):
    if pw != ADMIN_PASSWORD:
        return f"<html><head>{STYLE}</head><body><div class='container'><h1>403 Forbidden</h1></div></body></html>"
    
    rows = "".join([f"""<tr>
        <td>{p['id']}</td>
        <td>{p['site_name']}</td>
        <td>{p['comment']}</td>
        <td><a href='/delete/{p['id']}?pw={pw}' style='color:red;'>Delete</a></td>
    </tr>""" for p in db])
    
    return f"""<html><head>{STYLE}</head><body>{NAV_BAR}<div class="container">
    <h1>Admin Console</h1>
    <p>Filters: {app_settings['filters_enabled']} | <a href="/toggle?pw={pw}">[Toggle]</a></p>
    <table>
        <tr><th>ID</th><th>Site</th><th>Comment</th><th>Action</th></tr>
        {rows}
    </table>
    </div></body></html>"""

@app.get("/toggle")
async def toggle(pw: str):
    if pw == ADMIN_PASSWORD:
        app_settings["filters_enabled"] = not app_settings["filters_enabled"]
    return RedirectResponse(url=f"/admin-portal?pw={pw}")

@app.get("/delete/{pid}")
async def delete(pid: int, pw: str):
    global db
    if pw == ADMIN_PASSWORD:
        db = [p for p in db if p['id'] != pid]
        save_db(db)
    return RedirectResponse(url=f"/admin-portal?pw={pw}")

# --- API ENDPOINTS ---
@app.get("/pins", response_model=List[Pin])
async def get_pins(): return db

@app.post("/pins", response_model=Pin)
async def create_pin(pin: Pin):
    new_pin = pin.dict()
    new_pin["id"] = len(db) + 1
    new_pin["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.append(new_pin)
    save_db(db)
    return new_pin