"""
Authentication routes — /register, /login, /logout, /me
"""

from flask import Blueprint, request, jsonify, session, current_app
from bson.objectid import ObjectId
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    db = current_app.config["db"]
    bcrypt = current_app.config["bcrypt"]
    data = request.get_json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if db.users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

    user = {
        "name": name,
        "email": email,
        "password": hashed_pw,
        "created_at": datetime.utcnow(),
        "preferences": {
            "theme": "dark",
            "notifications": True,
        },
    }

    result = db.users.insert_one(user)
    session["user_id"] = str(result.inserted_id)

    return jsonify({
        "message": "Registration successful",
        "user": {
            "id": str(result.inserted_id),
            "name": name,
            "email": email,
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    db = current_app.config["db"]
    bcrypt = current_app.config["bcrypt"]
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = db.users.find_one({"email": email})

    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = str(user["_id"])

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "preferences": user.get("preferences", {}),
        }
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    db = current_app.config["db"]
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "preferences": user.get("preferences", {}),
            "created_at": user["created_at"].isoformat(),
        }
    }), 200


@auth_bp.route("/update-preferences", methods=["PUT"])
def update_preferences():
    db = current_app.config["db"]
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"preferences": data.get("preferences", {})}}
    )

    return jsonify({"message": "Preferences updated"}), 200
