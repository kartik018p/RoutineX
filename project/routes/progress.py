"""
Progress routes — /progress
Returns daily, weekly, and monthly data for charts/analytics.
"""

from flask import Blueprint, request, jsonify, session, current_app
from bson.objectid import ObjectId
from datetime import datetime, timedelta

progress_bp = Blueprint("progress", __name__)


@progress_bp.route("/progress", methods=["GET"])
def get_progress():
    db = current_app.config["db"]
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    period = request.args.get("period", "weekly")  # daily, weekly, monthly
    now = datetime.utcnow()

    if period == "daily":
        days = 1
    elif period == "monthly":
        days = 30
    else:
        days = 7

    start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")

    # Get all habits for user
    habits = list(db.habits.find({"user_id": user_id, "is_active": True}))
    total_habits = len(habits)

    if total_habits == 0:
        return jsonify({
            "period": period,
            "total_habits": 0,
            "daily_data": [],
            "overall_completion_rate": 0,
            "habit_stats": [],
            "streaks": {"current_best": 0, "overall_best": 0},
        }), 200

    # Get activity logs in range
    logs = list(db.activity_logs.find({
        "user_id": user_id,
        "date": {"$gte": start_date, "$lte": today},
    }))

    # Build daily data
    daily_data = []
    for i in range(days, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        day_logs = [l for l in logs if l["date"] == day]
        completed = len(day_logs)
        rate = round((completed / total_habits) * 100, 1) if total_habits > 0 else 0
        daily_data.append({
            "date": day,
            "completed": completed,
            "total": total_habits,
            "rate": rate,
        })

    # Habit-specific stats
    habit_stats = []
    for h in habits:
        hid = str(h["_id"])
        h_logs = [l for l in logs if l["habit_id"] == hid]
        completion_rate = round((len(h_logs) / (days + 1)) * 100, 1)
        habit_stats.append({
            "id": hid,
            "name": h["name"],
            "color": h.get("color", "#3B82F6"),
            "completions": len(h_logs),
            "possible": days + 1,
            "rate": completion_rate,
            "streak": h.get("streak", 0),
            "best_streak": h.get("best_streak", 0),
        })

    # Streaks
    current_best = max((h.get("streak", 0) for h in habits), default=0)
    overall_best = max((h.get("best_streak", 0) for h in habits), default=0)

    # Overall completion rate
    total_possible = total_habits * (days + 1)
    total_completed = len(logs)
    overall_rate = round((total_completed / total_possible) * 100, 1) if total_possible > 0 else 0

    return jsonify({
        "period": period,
        "total_habits": total_habits,
        "daily_data": daily_data,
        "overall_completion_rate": overall_rate,
        "habit_stats": habit_stats,
        "streaks": {"current_best": current_best, "overall_best": overall_best},
    }), 200


@progress_bp.route("/activity-heatmap", methods=["GET"])
def activity_heatmap():
    """Return 90 days of daily completion counts for a heatmap."""
    db = current_app.config["db"]
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    now = datetime.utcnow()
    start_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")

    logs = list(db.activity_logs.find({
        "user_id": user_id,
        "date": {"$gte": start_date},
    }))

    heatmap = {}
    for log in logs:
        d = log["date"]
        heatmap[d] = heatmap.get(d, 0) + 1

    data = []
    for i in range(90, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        data.append({"date": day, "count": heatmap.get(day, 0)})

    return jsonify({"heatmap": data}), 200
