"""
Machine Learning module for RoutineX
Uses Linear Regression to predict habit success and generate recommendations.
Analyses ALL available historical data to learn user patterns.
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta


class HabitPredictor:
    """
    Predicts habit completion probability and generates personalized recommendations
    using Linear Regression on ALL user activity data.
    """

    def __init__(self):
        self.model = LinearRegression()
        self.is_trained = False

    def _get_date_range(self, activity_logs):
        """Get the full date range covered by the activity logs."""
        if not activity_logs:
            return None, None, 0
        all_dates = sorted(set(l["date"] for l in activity_logs))
        first = datetime.strptime(all_dates[0], "%Y-%m-%d")
        last = datetime.strptime(all_dates[-1], "%Y-%m-%d")
        span_days = max((last - first).days, 1)
        return first, last, span_days

    def prepare_features(self, activity_logs, habits):
        """
        Build feature matrix from ALL available activity logs.

        Features per habit (11 total):
        - overall_completion_rate:  completions / total days tracked
        - recent_completion_rate:   completions in the last 25% of the tracking period
        - avg_hour:                 average hour of completion (normalized 0-1)
        - hour_consistency:         1 / (1 + std of hours) — tighter = higher
        - day_consistency:          fraction of completions on the most-common weekday
        - weekend_rate:             completion rate on weekends vs weekdays
        - freq_regularity:          1 / (1 + std of gaps between completions)
        - streak_ratio:             current streak / best streak
        - total_completions_norm:   total completions (normalized, capped)
        - trend:                    improvement trend (recent rate − older rate)
        - active_days_ratio:        how many unique days have any log / total span
        """
        if not activity_logs or not habits:
            return None, None, None

        first_date, last_date, span_days = self._get_date_range(activity_logs)
        if first_date is None:
            return None, None, None

        habit_map = {str(h["_id"]): h for h in habits}
        features = []
        targets = []
        habit_ids = []

        for hid, habit in habit_map.items():
            h_logs = [l for l in activity_logs if l.get("habit_id") == hid]

            if len(h_logs) < 2:
                continue

            # ── Overall completion rate (across full data span) ─────
            overall_rate = min(len(h_logs) / max(span_days, 1), 1.0)

            # ── Split data into halves for trend detection ──────────
            mid_date = first_date + timedelta(days=span_days // 2)
            mid_str = mid_date.strftime("%Y-%m-%d")
            first_half = [l for l in h_logs if l["date"] < mid_str]
            second_half = [l for l in h_logs if l["date"] >= mid_str]
            half_days = max(span_days // 2, 1)
            first_rate = len(first_half) / half_days
            second_rate = len(second_half) / half_days
            trend = np.clip(second_rate - first_rate, -1, 1)

            # ── Recent completion rate (last 25% of tracking period) ─
            recent_span = max(span_days // 4, 7)  # at least 7 days
            recent_cutoff = (last_date - timedelta(days=recent_span)).strftime("%Y-%m-%d")
            recent_logs = [l for l in h_logs if l["date"] >= recent_cutoff]
            recent_rate = min(len(recent_logs) / recent_span, 1.0)

            # ── Hour analysis ──────────────────────────────────────
            hours = [l.get("hour", 12) for l in h_logs]
            avg_hour = np.mean(hours) if hours else 12
            hour_std = np.std(hours) if len(hours) > 1 else 6
            hour_consistency = 1.0 / (1.0 + hour_std)

            # ── Day of week consistency ────────────────────────────
            days_of_week = [l.get("day_of_week", 0) for l in h_logs]
            if days_of_week:
                most_common_day = max(set(days_of_week), key=days_of_week.count)
                day_consistency = days_of_week.count(most_common_day) / len(days_of_week)
            else:
                day_consistency = 0

            # ── Weekend vs weekday rate ────────────────────────────
            weekend_logs = [l for l in h_logs if l.get("day_of_week", 0) >= 5]
            weekday_logs = [l for l in h_logs if l.get("day_of_week", 0) < 5]
            weekend_rate = len(weekend_logs) / max(len(weekend_logs) + len(weekday_logs), 1)

            # ── Frequency regularity (gap std) ─────────────────────
            dates = sorted([l["date"] for l in h_logs])
            if len(dates) > 1:
                gaps = []
                for i in range(1, len(dates)):
                    d1 = datetime.strptime(dates[i - 1], "%Y-%m-%d")
                    d2 = datetime.strptime(dates[i], "%Y-%m-%d")
                    gaps.append((d2 - d1).days)
                freq_regularity = 1.0 / (1.0 + np.std(gaps))
            else:
                freq_regularity = 0.5

            # ── Streak metrics ─────────────────────────────────────
            streak = habit.get("streak", 0)
            best_streak = habit.get("best_streak", 1)
            streak_ratio = streak / max(best_streak, 1)

            # ── Total completions normalized ───────────────────────
            total_comp = min(habit.get("total_completions", 0) / max(span_days, 1), 1.0)

            # ── Active days ratio ──────────────────────────────────
            unique_dates = len(set(l["date"] for l in h_logs))
            active_days_ratio = unique_dates / max(span_days, 1)

            feature_vec = [
                overall_rate,
                recent_rate,
                avg_hour / 24.0,
                hour_consistency,
                day_consistency,
                weekend_rate,
                freq_regularity,
                streak_ratio,
                total_comp,
                trend,
                active_days_ratio,
            ]

            features.append(feature_vec)

            # Target: use recent completion rate as the ground truth
            # This represents the user's current momentum
            targets.append(min(recent_rate, 1.0))
            habit_ids.append(hid)

        if not features:
            return None, None, None

        return np.array(features), np.array(targets), habit_ids

    def train(self, activity_logs, habits):
        """Train the Linear Regression model on ALL available data."""
        X, y, habit_ids = self.prepare_features(activity_logs, habits)

        if X is None or len(X) < 2:
            self.is_trained = False
            return False

        self.model.fit(X, y)
        self.is_trained = True
        return True

    def predict(self, activity_logs, habits):
        """Predict success probability for each habit."""
        X, _, habit_ids = self.prepare_features(activity_logs, habits)

        if X is None:
            return {}

        if not self.is_trained:
            self.train(activity_logs, habits)

        if not self.is_trained:
            return {}

        predictions = self.model.predict(X)
        # Clamp to 0-1
        predictions = np.clip(predictions, 0, 1)

        return {hid: float(pred) for hid, pred in zip(habit_ids, predictions)}

    def generate_recommendations(self, activity_logs, habits):
        """
        Generate personalized recommendations based on ML predictions
        and deep activity pattern analysis across ALL historical data.
        """
        predictions = self.predict(activity_logs, habits)
        habit_map = {str(h["_id"]): h for h in habits}

        _, last_date, span_days = self._get_date_range(activity_logs)
        recommendations = []

        for hid, prob in predictions.items():
            habit = habit_map.get(hid)
            if not habit:
                continue

            h_logs = [l for l in activity_logs if l.get("habit_id") == hid]
            habit_name = habit.get("name", "this habit")

            # ── Time pattern analysis ─────────────────────────────
            hours = [l.get("hour", 12) for l in h_logs]
            if hours:
                avg_hour = np.mean(hours)
                if avg_hour < 10:
                    time_period = "morning"
                elif avg_hour < 14:
                    time_period = "midday"
                elif avg_hour < 18:
                    time_period = "afternoon"
                else:
                    time_period = "evening"

                best_hour = int(round(avg_hour))
                am_pm = "AM" if best_hour < 12 else "PM"
                display_hour = best_hour if best_hour <= 12 else best_hour - 12
                if display_hour == 0:
                    display_hour = 12
            else:
                time_period = "morning"
                display_hour = 9
                am_pm = "AM"
                best_hour = 9

            # Generate recommendation based on probability
            rec = {
                "habit_id": hid,
                "habit_name": habit_name,
                "habit_color": habit.get("color", "#3B82F6"),
                "success_probability": round(prob * 100, 1),
                "suggestions": [],
                "best_time": f"{display_hour}:00 {am_pm}",
                "time_period": time_period,
                "priority": "low",
                "data_points": len(h_logs),
                "days_tracked": span_days,
            }

            if prob < 0.3:
                rec["priority"] = "high"
                rec["suggestions"].append(
                    f"⚠️ '{habit_name}' needs more attention — your predicted success is only {rec['success_probability']}%."
                )
                rec["suggestions"].append(
                    f"💡 Try doing '{habit_name}' in the {time_period} around {display_hour}:00 {am_pm} when you're most consistent."
                )
                rec["suggestions"].append(
                    f"🔄 Consider reducing the frequency of '{habit_name}' to build momentum first."
                )
            elif prob < 0.6:
                rec["priority"] = "medium"
                rec["suggestions"].append(
                    f"📊 You're building momentum with '{habit_name}' — predicted success at {rec['success_probability']}%."
                )
                rec["suggestions"].append(
                    f"⏰ You're most consistent in the {time_period}. Best time: around {display_hour}:00 {am_pm}."
                )
                if habit.get("streak", 0) > 0:
                    rec["suggestions"].append(
                        f"🔥 Keep your {habit.get('streak', 0)}-day streak alive!"
                    )
            else:
                rec["priority"] = "low"
                rec["suggestions"].append(
                    f"🌟 Great job with '{habit_name}'! You have a {rec['success_probability']}% predicted success rate."
                )
                rec["suggestions"].append(
                    f"⏰ You perform best in the {time_period} around {display_hour}:00 {am_pm}."
                )
                if habit.get("best_streak", 0) > 5:
                    rec["suggestions"].append(
                        f"🏆 Your best streak is {habit.get('best_streak', 0)} days — keep pushing!"
                    )

            # ── Trend analysis (from all data) ────────────────────
            if last_date and span_days > 14:
                mid_date = last_date - timedelta(days=span_days // 2)
                mid_str = mid_date.strftime("%Y-%m-%d")
                first_half = [l for l in h_logs if l["date"] < mid_str]
                second_half = [l for l in h_logs if l["date"] >= mid_str]
                half_days = max(span_days // 2, 1)
                old_rate = len(first_half) / half_days
                new_rate = len(second_half) / half_days

                if new_rate > old_rate * 1.15:
                    rec["suggestions"].append(
                        f"📈 Your consistency with '{habit_name}' has been improving! Keep it up."
                    )
                elif new_rate < old_rate * 0.85:
                    rec["suggestions"].append(
                        f"📉 Your '{habit_name}' consistency has been declining. Try to re-commit."
                    )

            # ── Day-of-week analysis ──────────────────────────────
            days_of_week = [l.get("day_of_week", 0) for l in h_logs]
            if days_of_week:
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                best_day = max(set(days_of_week), key=days_of_week.count)
                worst_day = min(set(days_of_week), key=days_of_week.count)
                if best_day != worst_day:
                    rec["suggestions"].append(
                        f"📅 You're strongest on {day_names[best_day]}s. Consider extra focus on {day_names[worst_day]}s."
                    )

            # ── Weekend analysis ──────────────────────────────────
            weekend_logs = [l for l in h_logs if l.get("day_of_week", 0) >= 5]
            weekday_logs = [l for l in h_logs if l.get("day_of_week", 0) < 5]
            if weekday_logs and weekend_logs:
                wd_rate = len(weekday_logs) / max(span_days * 5 / 7, 1)
                we_rate = len(weekend_logs) / max(span_days * 2 / 7, 1)
                if we_rate < wd_rate * 0.6:
                    rec["suggestions"].append(
                        f"🏖️ Your weekend completion for '{habit_name}' is notably lower. Try setting weekend reminders."
                    )

            recommendations.append(rec)

        # Sort by priority (high first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 2))

        # Add general recommendations
        general = []
        if predictions:
            avg_success = np.mean(list(predictions.values()))
            if avg_success > 0.7:
                general.append("🎉 Overall, you're doing excellent! Keep up the great work.")
            elif avg_success > 0.4:
                general.append("💪 You're making good progress. Focus on the highlighted habits to improve.")
            else:
                general.append("🌱 You're just getting started. Try focusing on fewer habits to build consistency.")

            # Check for too many habits
            if len(habits) > 7:
                general.append("📌 You have many habits tracked. Consider focusing on 3-5 key habits for better results.")

            total_logs = len(activity_logs)
            general.append(f"📊 Analysis based on {total_logs} data points across {span_days} days of tracking.")

        return {
            "recommendations": recommendations,
            "general_tips": general,
            "model_trained": self.is_trained,
        }


# Singleton instance
predictor = HabitPredictor()
