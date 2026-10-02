"""Seed data generator for Momentum.

Populates initial realistic sample tracks, habits, 4 weeks of historical daily logs
with varied consistency patterns, tasks with mixed priorities/statuses, and a 3-month Plan.
Ensures every screen looks populated and alive on first run.
"""

from datetime import date, timedelta
import random
from database.db_manager import DBManager


def populate_seed_data_if_empty(db: DBManager) -> bool:
    """Checks if database is empty. If no tracks exist, seeds sample data."""
    existing_tracks = db.get_all_tracks()
    if existing_tracks:
        return False  # Already populated

    today = date.today()

    # 1. Create Tracks
    tracks_spec = [
        ("Fitness & Health", "Fitness", "#10B981", "🏋️"),
        ("Academics & CS", "Academics", "#3B82F6", "📚"),
        ("Productivity & Skills", "Productivity", "#F59E0B", "💻"),
        ("Deep Reading & Mind", "Reading", "#8B5CF6", "📖"),
    ]
    track_ids = []
    for name, cat, col, ico in tracks_spec:
        tid = db.create_track(name=name, category=cat, color_hex=col, icon=ico)
        track_ids.append((name, tid))

    t_map = dict(track_ids)

    # 2. Create Habits under each Track
    # (name, icon, target_freq, track_id, completion_probability, streak_style)
    habits_spec = [
        # Fitness & Health
        ("Morning Workout / Gym", "🏋️", 5, t_map["Fitness & Health"], 0.80, "consistent"),
        ("Drink 2.5L Water", "💧", 7, t_map["Fitness & Health"], 0.90, "high_streak"),
        ("Sleep by 11:30 PM", "😴", 7, t_map["Fitness & Health"], 0.65, "mixed"),

        # Academics & CS
        ("Competitive Programming", "⚡", 5, t_map["Academics & CS"], 0.75, "building_streak"),
        ("Database Systems Study", "💾", 4, t_map["Academics & CS"], 0.70, "mixed"),
        ("Review Lecture Notes", "📝", 5, t_map["Academics & CS"], 0.60, "partial"),

        # Productivity & Skills
        ("Build 'Momentum' Project", "🚀", 6, t_map["Productivity & Skills"], 0.85, "high_streak"),
        ("Clean Desktop & Inbox Zero", "🧹", 5, t_map["Productivity & Skills"], 0.55, "mixed"),
        ("Learn System Architecture", "🧠", 4, t_map["Productivity & Skills"], 0.65, "building_streak"),

        # Deep Reading & Mind
        ("Read 20 Pages Non-Fiction", "📖", 7, t_map["Deep Reading & Mind"], 0.82, "consistent"),
        ("Evening Meditation", "🧘", 7, t_map["Deep Reading & Mind"], 0.70, "mixed"),
    ]

    habit_ids = []
    for hname, hicon, freq, tid, prob, style in habits_spec:
        hid = db.create_habit(track_id=tid, name=hname, icon=hicon, target_frequency=freq)
        habit_ids.append((hid, prob, style))

    # 3. Generate 30 days of realistic daily logs up to today
    # Seed deterministic random for reproducible realistic data
    rng = random.Random(42)

    for hid, base_prob, style in habit_ids:
        # Generate 30 days history: today - 29 days up to today
        for offset in range(29, -1, -1):
            log_d = today - timedelta(days=offset)
            iso_d = log_d.isoformat()

            # Tailor probability based on day of week and style
            day_of_week = log_d.weekday()  # 0=Monday, 6=Sunday
            is_weekend = day_of_week in (5, 6)

            prob = base_prob
            if is_weekend:
                prob = prob * 0.85 if "Workout" in str(hid) else prob * 1.05

            # Recent days logic to guarantee active streaks for demo
            if offset in (0, 1, 2, 3):
                if style in ("high_streak", "consistent", "building_streak"):
                    prob = 0.98

            # Decide completion
            completed = rng.random() < prob
            # Guarantee at least some completions and some gaps
            if offset == 0 and style == "high_streak":
                completed = True
            elif offset == 4 and style == "building_streak":
                completed = False  # introduce a deliberate gap 4 days ago

            db.toggle_completion(habit_id=hid, log_date=iso_d, completed=completed)

    # 4. Create 7 sample Tasks
    tasks_spec = [
        ("Submit SDP Milestone Architecture Document", today.isoformat(), "High", t_map["Academics & CS"], "Pending", 0),
        ("Finalize Tkinter UI Dark Mode theme palette", (today - timedelta(days=1)).isoformat(), "High", t_map["Productivity & Skills"], "Done", 0),
        ("Push git commits for project demo", today.isoformat(), "Medium", t_map["Productivity & Skills"], "Pending", 0),
        ("Leg day & 20 min HIIT cardio session", today.isoformat(), "Medium", t_map["Fitness & Health"], "Done", 0),
        ("Read Chapter 4 of 'Designing Data-Intensive Applications'", (today + timedelta(days=1)).isoformat(), "Medium", t_map["Deep Reading & Mind"], "Pending", 0),
        ("Prepare 3 questions for Academic Advisor meeting", (today + timedelta(days=2)).isoformat(), "Low", t_map["Academics & CS"], "Pending", 0),
        ("Restock protein powder & vitamins", (today - timedelta(days=2)).isoformat(), "Low", t_map["Fitness & Health"], "Pending", 1), # Carried over
    ]

    for title, due, priority, tid, status, carried in tasks_spec:
        task_id = db.create_task(title=title, due_date=due, priority=priority, linked_track_id=tid)
        if status == "Done":
            db.update_task_status(task_id, "Done")
        if carried:
            conn = db.get_connection()
            with conn:
                conn.execute("UPDATE tasks SET carried_over = 1 WHERE id = ?", (task_id,))

    # 5. Create Sample Plan (3-Month Productivity Mastery)
    plan_start = today.isoformat()
    plan_end = (today + timedelta(days=90)).isoformat()
    db.create_plan(
        track_id=t_map["Productivity & Skills"],
        start_date=plan_start,
        end_date=plan_end,
        weekly_target=5,
        notes="3-Month Intensive Skill Sprint: CP problem-solving, advanced SQL database mastery, desktop GUI architectural patterns, and high-performance algorithms."
    )

    return True
