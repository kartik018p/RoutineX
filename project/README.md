# RoutineX — Smart Habit Tracker with AI Recommendations 🚀

A full-stack web application for tracking habits, building streaks, and receiving **AI-powered personalized recommendations** using machine learning.

![RoutineX](https://img.shields.io/badge/RoutineX-Habit_Tracker-6C63FF?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-Flask-10B981?style=for-the-badge)
![MongoDB](https://img.shields.io/badge/MongoDB-Database-F59E0B?style=for-the-badge)
![ML](https://img.shields.io/badge/ML-Linear_Regression-EC4899?style=for-the-badge)

---

## 📁 Project Structure

```
project/
├── app.py                    # Main Flask server
├── requirements.txt          # Python dependencies
├── setup_db.py               # MongoDB schema setup + seeder
├── .env                      # Environment variables
├── .env.example              # Environment template
├── routes/
│   ├── __init__.py
│   ├── auth.py               # /register, /login, /logout, /me
│   ├── habits.py             # /add-habit, /edit-habit, /delete-habit, /get-habits, /track-habit
│   ├── progress.py           # /progress, /activity-heatmap
│   └── recommendations.py    # /get-recommendations, /retrain-model
├── ml/
│   ├── __init__.py
│   └── predictor.py          # Linear Regression ML model
└── frontend/
    ├── index.html             # Single-page application
    ├── styles.css             # Design system + all styles
    └── app.js                 # Frontend logic + API integration
```

---

## 🛠️ Tech Stack

| Layer       | Technology      | Purpose                           |
| ----------- | --------------- | --------------------------------- |
| Frontend    | HTML/CSS/JS     | UI with Chart.js visualizations   |
| Backend     | Python Flask    | REST API server                   |
| Database    | MongoDB         | Data persistence                  |
| ML          | scikit-learn    | Linear Regression recommendations |
| Auth        | Flask-Bcrypt    | Password hashing                  |
| Charts      | Chart.js        | Interactive visualizations        |

---

## 🚀 How to Run Locally

### Prerequisites
- **Python 3.8+** installed
- **MongoDB** installed and running on `localhost:27017`
  - [Install MongoDB Community](https://www.mongodb.com/docs/manual/installation/)
  - Start MongoDB service before running the app

### Step 1: Install Python Dependencies

```bash
cd project
pip install -r requirements.txt
```

### Step 2: Setup MongoDB (create indexes)

```bash
python setup_db.py
```

**With sample data (recommended for testing):**

```bash
python setup_db.py --seed
```

This creates a demo account: `demo@routinex.com` / `demo123`

### Step 3: Start the Server

```bash
python app.py
```

The app will be available at: **http://localhost:5000**

---

## 📡 API Endpoints

| Method   | Endpoint              | Description                    |
| -------- | --------------------- | ------------------------------ |
| `POST`   | `/api/register`       | Create new user account        |
| `POST`   | `/api/login`          | Login with email/password      |
| `POST`   | `/api/logout`         | End user session               |
| `GET`    | `/api/me`             | Get current user info          |
| `POST`   | `/api/add-habit`      | Create a new habit             |
| `PUT`    | `/api/edit-habit/:id` | Update a habit                 |
| `DELETE` | `/api/delete-habit/:id`| Delete a habit                |
| `GET`    | `/api/get-habits`     | Get all user habits            |
| `POST`   | `/api/track-habit`    | Toggle habit completion today  |
| `GET`    | `/api/progress`       | Get progress analytics         |
| `GET`    | `/api/activity-heatmap`| Get 90-day activity heatmap   |
| `GET`    | `/api/get-recommendations` | Get ML recommendations    |
| `POST`   | `/api/retrain-model`  | Retrain the ML model           |

---

## 🧠 Machine Learning Details

The recommendation engine uses **Linear Regression** from scikit-learn:

### Input Features (per habit):
1. **Completion rate** — fraction of days completed (last 30 days)
2. **Average hour** — typical time of day the habit is completed
3. **Hour standard deviation** — consistency of completion time
4. **Day consistency** — preference for certain days of the week
5. **Frequency regularity** — how evenly spaced completions are
6. **Streak ratio** — current streak / best streak
7. **Total completions** (normalized)

### Output:
- **Predicted success probability** (0–100%) for each habit

### Recommendations Include:
- 🕐 Best time of day to perform habits
- ⚠️ Which habits need more attention
- 🔥 Streak-based motivation
- 📅 Day-of-week performance analysis
- 💡 Actionable improvement suggestions

---

## 🎨 Features

- ✅ **User Authentication** — Signup, login, sessions
- ✅ **Habit CRUD** — Add, edit, delete, color-code habits
- ✅ **Daily Tracking** — One-click toggle with streak tracking
- ✅ **Dashboard** — Stats, today's habits, weekly chart
- ✅ **Progress Analytics** — Line charts, doughnut charts, data tables
- ✅ **AI Recommendations** — ML-powered personalized insights
- ✅ **Dark/Light Mode** — Theme toggle with persistence
- ✅ **Responsive Design** — Works on mobile, tablet, desktop
- ✅ **Glassmorphism UI** — Premium modern design

---

## 📊 MongoDB Schema

### Users Collection
```json
{
  "_id": "ObjectId",
  "name": "John Doe",
  "email": "john@example.com",
  "password": "$2b$12$...",
  "created_at": "2024-01-01T00:00:00",
  "preferences": {
    "theme": "dark",
    "notifications": true
  }
}
```

### Habits Collection
```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "name": "Morning Meditation",
  "category": "mindfulness",
  "frequency": "daily",
  "target_time": "07:00",
  "description": "10 min guided meditation",
  "color": "#3B82F6",
  "created_at": "2024-01-01T00:00:00",
  "streak": 5,
  "best_streak": 12,
  "total_completions": 45,
  "is_active": true
}
```

### Activity Logs Collection
```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "habit_id": "string",
  "date": "2024-01-15",
  "completed_at": "2024-01-15T07:30:00",
  "hour": 7,
  "day_of_week": 0
}
```

---

## 📄 License

MIT License — free to use and modify.
