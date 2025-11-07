from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
import sqlite3
import requests
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_to_a_random_secret")
bcrypt = Bcrypt(app)

# -------------------------
# ThingSpeak Configuration
# -------------------------
THINGSPEAK_CHANNEL_ID = "3117457"
THINGSPEAK_READ_API_KEY = "O1MK5ODEM3Z7SKTE"

FIELD_MAP = {
    1: "LDR1 (V)",
    2: "LDR2 (Cm)",
    3: "LDR3",
    4: "LDR4 (V)",
    5: "Dust Level (Cm)",
    6: "Panel Output (V)",
    7: "Dust Level (Cm)",
    8: "Cleaning Status"
}

# -------------------------
# Database setup
# -------------------------
DB_PATH = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------------------------
# ThingSpeak helper functions
# -------------------------
def fetch_thingspeak_field(field, results=50):
    if not THINGSPEAK_CHANNEL_ID:
        return []
    url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/fields/{field}.json"
    params = {"api_key": THINGSPEAK_READ_API_KEY, "results": results}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        feeds = data.get("feeds", [])
        key = f"field{field}"
        return [
            {
                "created_at": feed.get("created_at"),
                "value": float(feed.get(key)) if feed.get(key) not in (None, "") else None
            }
            for feed in feeds
        ]
    except Exception as e:
        print("ThingSpeak fetch error:", e)
        return []

def fetch_latest_feeds(results=1):
    if not THINGSPEAK_CHANNEL_ID:
        return []
    url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"
    params = {"api_key": THINGSPEAK_READ_API_KEY, "results": results}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json().get("feeds", [])
    except Exception as e:
        print("ThingSpeak latest fetch error:", e)
        return []

# -------------------------
# Routes
# -------------------------

# ✅ Home route — redirects to login or dashboard
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# ✅ Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Provide username and password.", "danger")
            return render_template("signup.html")
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")
        finally:
            conn.close()
    return render_template("signup.html")

# ✅ Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db_connection()
        row = conn.execute("SELECT id, password FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if row and bcrypt.check_password_hash(row["password"], password):
            session["user_id"] = row["id"]
            session["username"] = username
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

# ✅ Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# ✅ Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    latest = fetch_latest_feeds(results=1)
    latest_entry = latest[-1] if latest else None
    return render_template("dashboard.html", latest=latest_entry, field_map=FIELD_MAP)

# ✅ Simulation
@app.route("/simulation")
def simulation():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("simulation.html")

# ✅ Details
@app.route("/details/<int:field>")
def details(field):
    if "user_id" not in session:
        return redirect(url_for("login"))
    if field not in FIELD_MAP:
        flash("Invalid field.", "danger")
        return redirect(url_for("dashboard"))
    history = fetch_thingspeak_field(field, results=100)
    return render_template("details.html", field=field, title=FIELD_MAP[field], history=history)

# ✅ API endpoint
@app.route("/api/field/<int:field>")
def api_field(field):
    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401
    results = request.args.get("results", 50, type=int)
    data = fetch_thingspeak_field(field, results=results)
    labels = [entry["created_at"] for entry in data]
    values = [entry["value"] for entry in data]
    return jsonify({"labels": labels, "values": values})

# ✅ About and health
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/health")
def health():
    return "OK", 200

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
