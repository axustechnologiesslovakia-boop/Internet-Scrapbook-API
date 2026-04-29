import time
import os
import json
import re
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

app = FastAPI(title="The Internet Scrapbook")

# --- SETTINGS ---
# All files should be in the 'internet-scrapbook' folder
DATA_FILE = "data.json"
BLOCKED_FILE = "blocked.txt"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Prophet-Admin-Secret-2026")

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

def get_blocked_words():
    """Reads blocked.txt for the filter."""
    if os.path.exists(BLOCKED_FILE):
        with open(BLOCKED_FILE, "r") as f:
            return [line.strip().lower() for line in f if line.strip()]
    return []

db = load_db()
app_settings = {"filters_enabled": True}

class Pin(BaseModel):
    site_name: str
    url: str
    comment: str

# --- CLASSIC STYLE ---
STYLE = """
<style>
    body { font-family: sans-serif; background: #fafafa; color: #3b4151; margin: 0; padding: 0; }
    nav { background: #1b1b1b; padding: 10px 20px; display: flex; gap: 20px; align-items: center; }
    nav a { color: #fff; text-decoration: none; font-weight: bold; font-size: 14px; }
    .container { max-width: 800px; margin: 40px auto; padding: 20px; }
    .card { background: #fff; border: 1px solid #e8e8e8; border-radius: 4px; margin-bottom: 15px; padding: 20px; }
    .card strong { color: #61affe; font-size: 1.2em; }
    input, textarea { width: 100%; padding: 10px; border: 1px solid #d9d9d9; border-radius: 4px; margin-bottom: 10px; font-size: 14px; box-sizing: border-box; }
    button { background: #61affe; color: white; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; cursor: pointer; }
    .censored { color: #e74c3c; font-weight: bold; border-bottom: 1px dashed #e74c3c; }
    .error-msg { color: white; background: #e74c3c; padding: 10px; border-radius: 4px; margin-bottom: 15px; display: none; }
    table { width: 100%; border-collapse: collapse; background: white; margin-top: 20px; }
    th, td { border: 1px solid #e8e8e8; padding: 10px; text-align: left; }
</style>
"""

NAV_BAR = """<nav><a href="/">HOME</a><a href="/scrapbook">SCRAPBOOK</a><a href="/test">ADD PIN</a><a href="/docs">API DOCS</a></nav>"""

def apply_filters(text: str):
    if not app_settings["filters_enabled"]:
        return text
    blocked = get_blocked_words()
    filtered_text = text
    for word in blocked:
        # Case-insensitive replacement
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        filtered_text = pattern.sub('<span class="censored">[CENSORED]</span>', filtered_text)
    return filtered_text

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def root():
    return f"<html><head>{STYLE}</head><body>{NAV_BAR}<div class='container'><h1>Scrapbook</h1><p>Local Server Active.</p></div></body></html>"

@app.get("/scrapbook", response_class=HTMLResponse)
async def view_scrapbook(q: Optional[str] = None):
    results = [p for p in db if q.lower() in p['site_name'].lower() or q.lower() in p['comment'].lower()] if q else db
    cards = ""
    for p in reversed(results):
        clean_comment = apply_filters(p['comment'])
        cards += f"<div class='card'><strong>{p['site_name']}</strong><p>{clean_comment}</p></div>"
    return f"<html><head>{STYLE}</head><body>{NAV_BAR}<div class='container'><h1>Archive</h1>{cards if cards else '<p>Empty.</p>'}</div></body></html>"

@app.get("/test", response_class=HTMLResponse)
async def view_test():
    return f"""
    <html><head>{STYLE}</head><body>{NAV_BAR}
    <div class='container'>
        <h1>New Entry</h1>
        <div id="error-box" class="error-msg">You must fill out every single box!</div>
        <input type='text' id='s' placeholder='Site Name'>
        <input type='text' id='u' placeholder='URL'>
        <textarea id='c' placeholder='Comment'></textarea>
        <button onclick='postData()'>Submit Pin</button>
    </div>
    <script>
    async function postData() {{
        const s = document.getElementById('s').value.trim();
        const u = document.getElementById('u').value.trim();
        const c = document.getElementById('c').value.trim();
        const err = document.getElementById('error-box');

        if (!s || !u || !c) {{
            err.style.display = 'block';
            return;
        }}
        
        err.style.display = 'none';
        await fetch('/pins', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{ site_name: s, url: u, comment: c }})
        }});
        location.href='/scrapbook';
    }}
    </script></body></html>
    """

@app.post("/pins")
async def create_pin(pin: Pin):
    global db
    new_pin = pin.dict()
    new_pin["id"] = len(db) + 1
    new_pin["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.append(new_pin)
    save_db(db)
    return new_pin

@app.get("/admin-portal", response_class=HTMLResponse)
async def admin(pw: Optional[str] = None):
    if pw != ADMIN_PASSWORD: return "Forbidden"
    rows = "".join([f"<tr><td>{p['id']}</td><td>{p['site_name']}</td><td>{p['comment']}</td><td><a href='/delete/{p['id']}?pw={pw}'>Delete</a></td></tr>" for p in db])
    return f"<html><head>{STYLE}</head><body>{NAV_BAR}<div class='container'><h1>Admin</h1><table><tr><th>ID</th><th>Site</th><th>Comment</th><th>Action</th></tr>{rows}</table></div></body></html>"

@app.get("/delete/{pid}")
async def delete(pid: int, pw: str):
    global db
    if pw == ADMIN_PASSWORD:
        db = [p for p in db if p['id'] != pid]
        save_db(db)
    return RedirectResponse(url=f"/admin-portal?pw={pw}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)