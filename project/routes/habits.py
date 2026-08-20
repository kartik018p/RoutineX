"""
Habit management routes — /add-habit, /edit-habit, /delete-habit, /get-habits, /track-habit
"""

from flask import Blueprint, request, jsonify, session, current_app
from bson.objectid import ObjectId
from datetime import datetime, timedelta

habits_bp = Blueprint("habits", __name__)


def get_user_id():
    uid = session.get("user_id")
    if not uid:
        return None
    return uid


@habits_bp.route("/add-habit", methods=["POST"])
def add_habit():
    db = current_app.config["db"]
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    name = data.get("name", "").strip()
    category = data.get("category", "general").strip()
    frequency = data.get("frequency", "daily")  # daily, weekly
    target_time = data.get("target_time", "")  # e.g. "08:00"
    description = data.get("description", "").strip()
    color = data.get("color", "#3B82F6")

    if not name:
        return jsonify({"error": "Habit name is required"}), 400

    habit = {
        "user_id": user_id,
        "name": name,
        "category": category,
        "frequency": frequency,
        "target_time": target_time,
        "description": description,
        "color": color,
        "created_at": datetime.utcnow(),
        "streak": 0,
        "best_streak": 0,
        "total_completions": 0,
        "is_active": True,
    }

    result = db.habits.insert_one(habit)
    habit["_id"] = str(result.inserted_id)

    return jsonify({"message": "Habit created", "habit": serialize_habit(habit)}), 201


@habits_bp.route("/edit-habit/<habit_id>", methods=["PUT"])
def edit_habit(habit_id):
    db = current_app.config["db"]
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    update_fields = {}

    for field in ["name", "category", "frequency", "target_time", "description", "color", "is_active"]:
        if field in data:
            update_fields[field] = data[field]

    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    result = db.habits.update_one(
        {"_id": ObjectId(habit_id), "user_id": user_id},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Habit not found"}), 404

    return jsonify({"message": "Habit updated"}), 200


@habits_bp.route("/delete-habit/<habit_id>", methods=["DELETE"])
def delete_habit(habit_id):
    db = current_app.config["db"]
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    result = db.habits.delete_one({"_id": ObjectId(habit_id), "user_id": user_id})

    if result.deleted_count == 0:
        return jsonify({"error": "Habit not found"}), 404

    # Also remove related activity logs
    db.activity_logs.delete_many({"habit_id": habit_id, "user_id": user_id})

    return jsonify({"message": "Habit deleted"}), 200


@habits_bp.route("/get-habits", methods=["GET"])
def get_habits():
    db = current_app.config["db"]
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    habits = list(db.habits.find({"user_id": user_id, "is_active": True}))
    today = datetime.utcnow().strftime("%Y-%m-%d")

    result = []
    for h in habits:
        habit_data = serialize_habit(h)
        # Check if completed today
        log = db.activity_logs.find_one({
            "habit_id": str(h["_id"]),
            "user_id": user_id,
            "date": today,
        })
        habit_data["completed_today"] = log is not None
        habit_data["completion_time"] = log["completed_at"] if log else None
        result.append(habit_data)

    return jsonify({"habits": result}), 200


@habits_bp.route("/track-habit", methods=["POST"])
def track_habit():
    db = current_app.config["db"]
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    habit_id = data.get("habit_id")

    if not habit_id:
        return jsonify({"error": "Habit ID is required"}), 400

    habit = db.habits.find_one({"_id": ObjectId(habit_id), "user_id": user_id})
    if not habit:
        return jsonify({"error": "Habit not found"}), 404

    today = datetime.utcnow().strftime("%Y-%m-%d")
    now = datetime.utcnow()

    existing_log = db.activity_logs.find_one({
        "habit_id": habit_id,
        "user_id": user_id,
        "date": today,
    })

    if existing_log:
        # Untrack: remove the log and decrement streak
        db.activity_logs.delete_one({"_id": existing_log["_id"]})

        new_streak = max(0, habit.get("streak", 1) - 1)
        db.habits.update_one(
            {"_id": ObjectId(habit_id)},
            {
                "$set": {"streak": new_streak},
                "$inc": {"total_completions": -1},
            }
        )

        return jsonify({"message": "Habit untracked", "completed": False, "streak": new_streak}), 200

    # Track: add log and increment streak
    log = {
        "user_id": user_id,
        "habit_id": habit_id,
        "date": today,
        "completed_at": now.isoformat(),
        "hour": now.hour,
        "day_of_week": now.weekday(),  # 0=Mon, 6=Sun
    }
    db.activity_logs.insert_one(log)

    # Calculate streak
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_log = db.activity_logs.find_one({
        "habit_id": habit_id,
        "user_id": user_id,
        "date": yesterday,
    })

    current_streak = habit.get("streak", 0)
    if yesterday_log:
        new_streak = current_streak + 1
    else:
        new_streak = 1

    best_streak = max(habit.get("best_streak", 0), new_streak)

    db.habits.update_one(
        {"_id": ObjectId(habit_id)},
        {
            "$set": {"streak": new_streak, "best_streak": best_streak},
            "$inc": {"total_completions": 1},
        }
    )

    return jsonify({
        "message": "Habit tracked",
        "completed": True,
        "streak": new_streak,
        "best_streak": best_streak,
    }), 200


def serialize_habit(h):
    return {
        "id": str(h["_id"]) if isinstance(h.get("_id"), ObjectId) else h.get("_id", ""),
        "name": h.get("name", ""),
        "category": h.get("category", ""),
        "frequency": h.get("frequency", "daily"),
        "target_time": h.get("target_time", ""),
        "description": h.get("description", ""),
        "color": h.get("color", "#3B82F6"),
        "streak": h.get("streak", 0),
        "best_streak": h.get("best_streak", 0),
        "total_completions": h.get("total_completions", 0),
        "created_at": h["created_at"].isoformat() if isinstance(h.get("created_at"), datetime) else str(h.get("created_at", "")),
        "is_active": h.get("is_active", True),
    }
