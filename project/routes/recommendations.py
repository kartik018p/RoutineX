"""
Recommendation routes — /get-recommendations, /retrain-model
"""

from flask import Blueprint, jsonify, session, current_app
from datetime import datetime, timedelta

reco_bp = Blueprint("recommendations", __name__)


@reco_bp.route("/get-recommendations", methods=["GET"])
def get_recommendations():
    db = current_app.config["db"]
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    from ml.predictor import predictor

    habits = list(db.habits.find({"user_id": user_id, "is_active": True}))

    if not habits:
        return jsonify({
            "recommendations": [],
            "general_tips": ["📝 Start by adding some habits to track!"],
            "model_trained": False,
        }), 200

    # Get ALL activity logs for comprehensive pattern analysis
    activity_logs = list(db.activity_logs.find({
        "user_id": user_id,
    }))

    if len(activity_logs) < 5:
        # Not enough data — return basic tips
        tips = [
            "📊 Keep tracking your habits for a few more days so we can generate personalized recommendations.",
            "💡 Tip: Try completing habits at the same time each day to build consistency.",
            "🎯 Focus on building streaks — even small ones help!",
        ]
        basic_recs = []
        for h in habits:
            basic_recs.append({
                "habit_id": str(h["_id"]),
                "habit_name": h["name"],
                "habit_color": h.get("color", "#3B82F6"),
                "success_probability": 50.0,
                "suggestions": [f"📝 Keep tracking '{h['name']}' to get personalized insights."],
                "best_time": h.get("target_time", "9:00 AM") or "9:00 AM",
                "time_period": "morning",
                "priority": "medium",
            })

        return jsonify({
            "recommendations": basic_recs,
            "general_tips": tips,
            "model_trained": False,
        }), 200

    # Train the model and get recommendations
    predictor.train(activity_logs, habits)
    result = predictor.generate_recommendations(activity_logs, habits)

    return jsonify(result), 200


@reco_bp.route("/retrain-model", methods=["POST"])
def retrain_model():
    db = current_app.config["db"]
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    from ml.predictor import predictor

    habits = list(db.habits.find({"user_id": user_id, "is_active": True}))
    # Fetch ALL activity logs for full pattern analysis
    activity_logs = list(db.activity_logs.find({
        "user_id": user_id,
    }))

    success = predictor.train(activity_logs, habits)

    return jsonify({
        "message": "Model retrained" if success else "Not enough data to train",
        "success": success,
    }), 200
