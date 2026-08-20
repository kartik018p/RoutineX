"""
MongoDB Schema Setup for RoutineX
Run this script to initialize the database with indexes
and optionally seed with sample data.

Usage:
    python setup_db.py          # Create indexes only
    python setup_db.py --seed   # Create indexes + sample data
"""

import sys
import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/routinex")
client = MongoClient(MONGO_URI)
db = client["routinex"]


def create_indexes():
    """Create MongoDB indexes for performance."""
    print("📦  Creating indexes...")

    # Users collection
    db.users.create_index("email", unique=True)
    print("   ✅ users.email (unique)")

    # Habits collection
    db.habits.create_index("user_id")
    db.habits.create_index([("user_id", 1), ("is_active", 1)])
    print("   ✅ habits.user_id")
    print("   ✅ habits.(user_id, is_active)")

    # Activity Logs collection
    db.activity_logs.create_index([("user_id", 1), ("date", -1)])
    db.activity_logs.create_index([("habit_id", 1), ("date", -1)])
    db.activity_logs.create_index([("user_id", 1), ("habit_id", 1), ("date", 1)], unique=True)
    print("   ✅ activity_logs.(user_id, date)")
    print("   ✅ activity_logs.(habit_id, date)")
    print("   ✅ activity_logs.(user_id, habit_id, date) — unique")

    print("\n✅  All indexes created!\n")


def print_schema():
    """Display the MongoDB schema documentation."""
    schema = """
╔══════════════════════════════════════════════════════════════╗
║                  RoutineX MongoDB Schema                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📁 Collection: users                                        ║
║  ├── _id          : ObjectId (auto)                          ║
║  ├── name         : String                                   ║
║  ├── email        : String (unique, indexed)                 ║
║  ├── password     : String (bcrypt hash)                     ║
║  ├── created_at   : DateTime                                 ║
║  └── preferences  : Object                                   ║
║      ├── theme         : String ("dark" | "light")           ║
║      └── notifications : Boolean                             ║
║                                                              ║
║  📁 Collection: habits                                       ║
║  ├── _id              : ObjectId (auto)                      ║
║  ├── user_id          : String (indexed)                     ║
║  ├── name             : String                               ║
║  ├── category         : String                               ║
║  ├── frequency        : String ("daily" | "weekly")          ║
║  ├── target_time      : String (e.g. "08:00")               ║
║  ├── description      : String                               ║
║  ├── color            : String (hex)                         ║
║  ├── created_at       : DateTime                             ║
║  ├── streak           : Integer                              ║
║  ├── best_streak      : Integer                              ║
║  ├── total_completions: Integer                              ║
║  └── is_active        : Boolean                              ║
║                                                              ║
║  📁 Collection: activity_logs                                ║
║  ├── _id          : ObjectId (auto)                          ║
║  ├── user_id      : String (indexed)                         ║
║  ├── habit_id     : String (indexed)                         ║
║  ├── date         : String (YYYY-MM-DD, indexed)             ║
║  ├── completed_at : String (ISO timestamp)                   ║
║  ├── hour         : Integer (0-23)                           ║
║  └── day_of_week  : Integer (0=Mon, 6=Sun)                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(schema)


def seed_data(force=False):
    """
    Seed the database with rich, realistic sample data for ML training.
    Generates 90 days of activity logs across 8 habits with varied patterns.
    """
    import random
    from flask_bcrypt import Bcrypt
    from flask import Flask

    temp_app = Flask(__name__)
    bcrypt = Bcrypt(temp_app)

    print("🌱  Seeding rich sample data for ML training...\n")

    # If force mode, wipe existing demo data
    if force:
        existing = db.users.find_one({"email": "demo@routinex.com"})
        if existing:
            uid = str(existing["_id"])
            db.activity_logs.delete_many({"user_id": uid})
            db.habits.delete_many({"user_id": uid})
            db.users.delete_one({"_id": existing["_id"]})
            print("   🗑️  Cleared existing demo data.")
    else:
        if db.users.find_one({"email": "demo@routinex.com"}):
            print("   ⚠️  Demo user already exists. Run with --reseed to wipe and recreate.\n")
            return

    # ── Create demo user ────────────────────────────────────
    hashed_pw = bcrypt.generate_password_hash("demo123").decode("utf-8")
    user = {
        "name": "Demo User",
        "email": "demo@routinex.com",
        "password": hashed_pw,
        "created_at": datetime.utcnow() - timedelta(days=90),
        "preferences": {"theme": "dark", "notifications": True},
    }
    user_result = db.users.insert_one(user)
    user_id = str(user_result.inserted_id)
    print(f"   ✅ Created demo user: demo@routinex.com / demo123")

    # ── Create 8 diverse habits ─────────────────────────────
    habits_data = [
        {
            "name": "Morning Meditation",
            "category": "mindfulness",
            "color": "#3B82F6",
            "target_time": "07:00",
            "description": "10 minutes of guided breathing",
            "base_prob": 0.88,         # high consistency
            "preferred_hour": 7,
            "hour_variance": 1,
            "weekend_drop": 0.05,      # barely drops on weekends
            "trend": "stable",
        },
        {
            "name": "Exercise",
            "category": "fitness",
            "color": "#EF4444",
            "target_time": "08:00",
            "description": "30 min workout or run",
            "base_prob": 0.55,
            "preferred_hour": 8,
            "hour_variance": 2,
            "weekend_drop": 0.20,      # much less on weekends
            "trend": "improving",      # getting better over time
        },
        {
            "name": "Read 30 Pages",
            "category": "learning",
            "color": "#F59E0B",
            "target_time": "21:00",
            "description": "Read before sleep",
            "base_prob": 0.72,
            "preferred_hour": 21,
            "hour_variance": 1,
            "weekend_drop": -0.10,     # actually better on weekends
            "trend": "stable",
        },
        {
            "name": "Drink 2L Water",
            "category": "health",
            "color": "#10B981",
            "target_time": "",
            "description": "Stay hydrated throughout the day",
            "base_prob": 0.92,
            "preferred_hour": 14,
            "hour_variance": 4,        # very spread out timing
            "weekend_drop": 0.02,
            "trend": "stable",
        },
        {
            "name": "Journal Writing",
            "category": "creativity",
            "color": "#EC4899",
            "target_time": "22:00",
            "description": "Reflect on the day",
            "base_prob": 0.45,
            "preferred_hour": 22,
            "hour_variance": 1,
            "weekend_drop": 0.15,
            "trend": "declining",      # struggling with this one
        },
        {
            "name": "Learn Spanish",
            "category": "learning",
            "color": "#06B6D4",
            "target_time": "19:00",
            "description": "15 min Duolingo session",
            "base_prob": 0.65,
            "preferred_hour": 19,
            "hour_variance": 2,
            "weekend_drop": 0.10,
            "trend": "improving",
        },
        {
            "name": "No Social Media Before Noon",
            "category": "productivity",
            "color": "#8B5CF6",
            "target_time": "12:00",
            "description": "Digital detox mornings",
            "base_prob": 0.50,
            "preferred_hour": 11,
            "hour_variance": 1,
            "weekend_drop": 0.25,      # hard on weekends
            "trend": "improving",
        },
        {
            "name": "Healthy Meal Prep",
            "category": "health",
            "color": "#F97316",
            "target_time": "18:00",
            "description": "Cook a healthy dinner",
            "base_prob": 0.60,
            "preferred_hour": 18,
            "hour_variance": 2,
            "weekend_drop": -0.05,     # slightly better on weekends
            "trend": "stable",
        },
    ]

    now = datetime.utcnow()
    total_days = 90
    total_logs = 0

    habit_ids = []
    for h in habits_data:
        habit = {
            "user_id": user_id,
            "name": h["name"],
            "category": h["category"],
            "frequency": "daily",
            "target_time": h["target_time"],
            "description": h["description"],
            "color": h["color"],
            "created_at": now - timedelta(days=total_days),
            "streak": 0,
            "best_streak": 0,
            "total_completions": 0,
            "is_active": True,
        }
        result = db.habits.insert_one(habit)
        habit_ids.append(str(result.inserted_id))
        print(f"   ✅ Created habit: {h['name']}")

    # ── Generate 90 days of realistic activity logs ─────────
    print(f"\n   ⏳ Generating {total_days} days of activity logs...")

    for day_offset in range(total_days, 0, -1):
        day = now - timedelta(days=day_offset)
        date_str = day.strftime("%Y-%m-%d")
        is_weekend = day.weekday() >= 5  # Saturday=5, Sunday=6
        day_progress = 1.0 - (day_offset / total_days)  # 0.0 → 1.0

        for i, habit_id in enumerate(habit_ids):
            h = habits_data[i]

            # Calculate probability for this specific day
            prob = h["base_prob"]

            # Weekend adjustment
            if is_weekend:
                prob -= h["weekend_drop"]

            # Trend adjustment (improving/declining over the 90 days)
            if h["trend"] == "improving":
                prob += day_progress * 0.25  # gets up to 25% better
            elif h["trend"] == "declining":
                prob -= day_progress * 0.20  # gets up to 20% worse

            # Add small daily randomness
            prob += random.uniform(-0.08, 0.08)

            # Clamp
            prob = max(0.05, min(0.98, prob))

            if random.random() < prob:
                # Varied completion hour
                hour = h["preferred_hour"] + random.randint(
                    -h["hour_variance"], h["hour_variance"]
                )
                # On weekends, shift time later
                if is_weekend:
                    hour += random.randint(0, 2)
                hour = max(0, min(23, hour))

                log = {
                    "user_id": user_id,
                    "habit_id": habit_id,
                    "date": date_str,
                    "completed_at": day.replace(hour=hour, minute=random.randint(0, 59)).isoformat(),
                    "hour": hour,
                    "day_of_week": day.weekday(),
                }

                try:
                    db.activity_logs.insert_one(log)
                    total_logs += 1
                except Exception:
                    pass  # Skip duplicate

    # ── Update streak and total counts ──────────────────────
    print(f"   ✅ Generated {total_logs} activity logs across {total_days} days\n")
    print("   📊 Habit Statistics:")

    for i, habit_id in enumerate(habit_ids):
        logs = list(db.activity_logs.find({"habit_id": habit_id}).sort("date", -1))
        total = len(logs)

        # Calculate current streak
        streak = 0
        for j, log in enumerate(logs):
            expected_date = (now - timedelta(days=j)).strftime("%Y-%m-%d")
            if log["date"] == expected_date:
                streak += 1
            else:
                break

        # Calculate best streak from all logs
        all_dates = sorted([l["date"] for l in logs])
        best_streak = 0
        current_run = 1
        for k in range(1, len(all_dates)):
            d1 = datetime.strptime(all_dates[k - 1], "%Y-%m-%d")
            d2 = datetime.strptime(all_dates[k], "%Y-%m-%d")
            if (d2 - d1).days == 1:
                current_run += 1
                best_streak = max(best_streak, current_run)
            else:
                current_run = 1
        best_streak = max(best_streak, current_run, streak)

        db.habits.update_one(
            {"_id": db.habits.find_one({"user_id": user_id, "name": habits_data[i]["name"]})["_id"]},
            {"$set": {"streak": streak, "best_streak": best_streak, "total_completions": total}}
        )

        rate = round((total / total_days) * 100, 1)
        trend_icon = {"stable": "➡️", "improving": "📈", "declining": "📉"}.get(habits_data[i]["trend"], "")
        print(f"      {habits_data[i]['name']:30s} | {total:3d} logs | {rate:5.1f}% | streak: {streak:2d} | best: {best_streak:2d} | {trend_icon} {habits_data[i]['trend']}")

    print(f"\n🎉  Seed complete! Login with:")
    print(f"    Email:    demo@routinex.com")
    print(f"    Password: demo123\n")
    print(f"    → Visit 'AI Insights' to see ML recommendations immediately!\n")


if __name__ == "__main__":
    print_schema()
    create_indexes()

    if "--reseed" in sys.argv:
        seed_data(force=True)
    elif "--seed" in sys.argv:
        seed_data()
    else:
        print("💡  Run with --seed to add sample data:    python setup_db.py --seed")
        print("💡  Run with --reseed to wipe and reseed:  python setup_db.py --reseed\n")
