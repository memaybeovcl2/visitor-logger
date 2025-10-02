from flask import Flask, request, g, render_template, redirect, url_for, send_file
import sqlite3
from datetime import datetime
import csv
import io
import os

DB_PATH = "visitors.db"

app = Flask(__name__)

# --- DB helpers ---
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        need_init = not os.path.exists(DB_PATH)
        db = g._database = sqlite3.connect(DB_PATH, check_same_thread=False)
        if need_init:
            init_db(db)
    return db

def init_db(db):
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT NOT NULL,
        user_agent TEXT,
        referer TEXT,
        path TEXT,
        ts TEXT NOT NULL
    );
    """)
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def insert_visit(ip, ua, referer, path):
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO visitors (ip, user_agent, referer, path, ts) VALUES (?, ?, ?, ?, ?)",
                (ip, ua, referer, path, datetime.utcnow().isoformat()))
    db.commit()

def query_visits(limit=200):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, ip, user_agent, referer, path, ts FROM visitors ORDER BY id DESC LIMIT ?", (limit,))
    return cur.fetchall()

# --- Routes ---
@app.route("/")
def index():
    # A simple landing page. It will call /log via JS to record visitor's IP/info on the server.
    # You can also directly hit /log from client or server side.
    return render_template("index.html")

@app.route("/log", methods=["POST", "GET"])
def log_visit():
    # This endpoint records the requester's IP and info.
    # If behind a proxy/load balancer, you may want to obtain IP from X-Forwarded-For (see note below).
    if request.headers.get("X-Forwarded-For"):
        # take the first address in X-Forwarded-For
        ip = request.headers.get("X-Forwarded-For").split(",")[0].strip()
    else:
        ip = request.remote_addr or "unknown"

    user_agent = request.headers.get("User-Agent", "")
    referer = request.headers.get("Referer", "")
    path = request.args.get("path", request.path)

    insert_visit(ip, user_agent, referer, path)

    # Return JSON so client fetch can know success
    return {"status": "ok", "ip": ip}

@app.route("/visit")
def visit_and_redirect():
    # convenience: log then show a simple page
    _ = log_visit()
    return "<h2>Thanks — your visit was logged.</h2>"

@app.route("/logs")
def view_logs():
    # Admin page to view logged IPs
    rows = query_visits(limit=1000)
    return render_template("logs.html", rows=rows)

@app.route("/export.csv")
def export_csv():
    rows = query_visits(limit=10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "ip", "user_agent", "referer", "path", "ts"])
    for r in rows[::-1]:  # old -> new
        writer.writerow(r)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8")),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="visitors.csv")

if __name__ == "__main__":
    # For local testing only. For production use gunicorn/uwsgi behind proxy.
    app.run(host="0.0.0.0", port=5000, debug=True)
