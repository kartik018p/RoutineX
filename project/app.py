"""
RoutineX — Habit Tracking & Personalized Recommendation System
Main Flask application entry point.
"""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# ── Flask App ───────────────────────────────────────────────
app = Flask(__name__, static_folder="frontend", static_url_path="")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key")
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)

# ── MongoDB Connection ──────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/routinex")
client = MongoClient(MONGO_URI)
db = client.get_default_database() if "routinex" not in MONGO_URI else client["routinex"]

# ── Make db + bcrypt accessible to blueprints ───────────────
app.config["db"] = db
app.config["bcrypt"] = bcrypt
# ── Register Blueprints ────────────────────────────────────
from routes.auth import auth_bp
from routes.habits import habits_bp
from routes.recommendations import reco_bp
from routes.progress import progress_bp

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(habits_bp, url_prefix="/api")
app.register_blueprint(reco_bp, url_prefix="/api")
app.register_blueprint(progress_bp, url_prefix="/api")


# ── Serve Frontend ──────────────────────────────────────────
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# ── DB Index Setup ──────────────────────────────────────────
def setup_indexes():
    """Create MongoDB indexes for performance."""
    db.users.create_index("email", unique=True)
    db.habits.create_index("user_id")
    db.activity_logs.create_index([("user_id", 1), ("date", -1)])


# ── Run ─────────────────────────────────────────────────────
if __name__ == "__main__":
    setup_indexes()
    print("[*] RoutineX server running at http://localhost:5000")
    app.run(debug=True, port=5000)
