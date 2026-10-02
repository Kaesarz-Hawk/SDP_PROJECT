"""Comprehensive Automated Verification Suite for Momentum.

Validates:
1. Streak calculator logic (0%, 100%, gap recovery)
2. Database schema, CRUD, foreign keys, upserts, task rollover
3. Seed data generation & volume
4. Path helper and asset resolution
5. UI frame instantiation with real data AND zero-data empty states
6. Analytics chart generation & empty placeholders
7. Clean database shutdown
"""

import os
import sys
from datetime import date, timedelta
import customtkinter as ctk

# Ensure workspace root in path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.db_manager import DBManager
from models.habit import Habit
from models.plan import Plan
from models.task import Task
from models.track import Track
from ui.analytics_frame import AnalyticsFrame
from ui.calendar_frame import CalendarFrame
from ui.dashboard_frame import DashboardFrame
from ui.habit_tracker_frame import HabitTrackerFrame
from ui.onboarding_frame import OnboardingFrame
from ui.settings_frame import SettingsFrame
from ui.sidebar import Sidebar
from ui.todo_frame import TodoFrame
from utils.path_helper import get_asset_path, get_base_path, get_db_path, get_writable_data_path
from utils.seed_data import populate_seed_data_if_empty
from utils.streak_calculator import compute_best_streak, compute_current_streak, get_streak_flame_level


def test_streak_calculation():
    print("[1/6] Testing Streak Calculation...")
    today = date.today()

    # Never completed
    assert compute_current_streak([]) == 0
    assert compute_best_streak([]) == 0

    # 5 consecutive days up to today
    five_days = [today - timedelta(days=i) for i in range(5)]
    assert compute_current_streak(five_days) == 5
    assert compute_best_streak(five_days) == 5

    # Gap in the middle: today, yesterday, gap, 5 days ago
    gap_dates = [today, today - timedelta(days=1), today - timedelta(days=4), today - timedelta(days=5)]
    assert compute_current_streak(gap_dates) == 2
    assert compute_best_streak(gap_dates) == 2

    # Flame level helper
    assert get_streak_flame_level(0)[0] == "⚡"
    assert get_streak_flame_level(5)[0] == "🔥"
    assert get_streak_flame_level(25)[0] == "🔥"
    print("      [OK] Streak calculator verified successfully.")


def test_database_and_crud():
    print("[2/6] Testing Database & CRUD...")
    test_db_file = os.path.join(ROOT_DIR, "test_verify.db")
    if os.path.exists(test_db_file):
        os.remove(test_db_file)

    db = DBManager(test_db_file)

    # 1. Track CRUD
    tid = db.create_track("Testing Track", "Productivity", "#7C5CFC", "🎯")
    tracks = db.get_all_tracks()
    assert len(tracks) == 1
    assert tracks[0].name == "Testing Track"

    # 2. Habit CRUD & Soft delete
    hid = db.create_habit(tid, "Daily Practice", "⚡", 5)
    habits = db.get_active_habits()
    assert len(habits) == 1
    assert habits[0].name == "Daily Practice"

    db.deactivate_habit(hid)
    assert len(db.get_active_habits()) == 0

    # Reactivate for further tests
    db.update_habit(hid, is_active=1)
    assert len(db.get_active_habits()) == 1

    # 3. Daily Logs Upsert
    today_iso = date.today().isoformat()
    db.toggle_completion(hid, today_iso, True)
    assert db.is_habit_completed(hid, today_iso) is True
    db.toggle_completion(hid, today_iso, False)
    assert db.is_habit_completed(hid, today_iso) is False
    db.toggle_completion(hid, today_iso, True)

    # 4. Tasks & Rollover
    past_date = (date.today() - timedelta(days=2)).isoformat()
    task_id = db.create_task("Old Overdue Task", past_date, "High", tid)
    tasks_yesterday = db.get_tasks_for_date(past_date)
    assert len(tasks_yesterday) == 1

    rolled = db.roll_over_incomplete_tasks(to_date=today_iso)
    assert rolled >= 1
    tasks_today = db.get_tasks_for_date(today_iso)
    assert any(t.id == task_id and t.carried_over == 1 for t in tasks_today)

    # 5. Plan CRUD
    end_date = (date.today() + timedelta(days=90)).isoformat()
    pid = db.create_plan(tid, today_iso, end_date, 5, "Test notes")
    plans = db.get_plans_for_track(tid)
    assert len(plans) == 1
    assert plans[0].weekly_target == 5

    db.close()
    if os.path.exists(test_db_file):
        os.remove(test_db_file)
    print("      [OK] Database and CRUD verified successfully.")


def test_seed_data_generation():
    print("[3/6] Testing Seed Data Generator...")
    test_db_file = os.path.join(ROOT_DIR, "test_seed.db")
    if os.path.exists(test_db_file):
        os.remove(test_db_file)

    db = DBManager(test_db_file)
    seeded = populate_seed_data_if_empty(db)
    assert seeded is True

    tracks = db.get_all_tracks()
    assert len(tracks) >= 4

    habits = db.get_active_habits()
    assert len(habits) >= 8

    # Check 30 days logs exist
    thirty_ago = (date.today() - timedelta(days=29)).isoformat()
    today_iso = date.today().isoformat()
    heatmap = db.get_overall_heatmap_data(thirty_ago, today_iso)
    assert len(heatmap) > 0
    # Check variation in heatmap
    ratios = list(heatmap.values())
    assert any(r > 0.0 for r in ratios)

    tasks = db.get_tasks_for_date(today_iso)
    assert len(tasks) > 0

    plans = db.get_all_plans()
    assert len(plans) >= 1

    db.close()
    if os.path.exists(test_db_file):
        os.remove(test_db_file)
    print("      [OK] Seed data verified successfully.")


def test_path_helper_and_assets():
    print("[4/6] Testing Path Helper and Assets...")
    base_p = get_base_path()
    assert os.path.exists(base_p)

    writable_p = get_writable_data_path()
    assert os.path.exists(writable_p)

    db_p = get_db_path()
    assert "momentum.db" in db_p

    icon_p = get_asset_path("icon.ico")
    assert os.path.exists(icon_p)
    print(f"      [OK] Paths and asset files verified at: {icon_p}")


def test_ui_screens_rendering():
    print("[5/6] Testing All 7 UI Screens Rendering...")
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.withdraw()  # Headless mode for automated verification

    test_db_file = os.path.join(ROOT_DIR, "test_ui.db")
    if os.path.exists(test_db_file):
        os.remove(test_db_file)

    db = DBManager(test_db_file)
    populate_seed_data_if_empty(db)

    # 1. Sidebar
    sidebar = Sidebar(root, on_navigate=lambda k: None)
    sidebar.pack()

    # 2. Dashboard
    dash = DashboardFrame(root, db=db)
    dash.refresh()

    # 3. Habit Tracker
    ht = HabitTrackerFrame(root, db=db)
    ht.refresh()

    # 4. Calendar
    cal = CalendarFrame(root, db=db)
    cal.refresh()

    # 5. Todo
    todo = TodoFrame(root, db=db)
    todo.refresh()

    # 6. Analytics
    ana = AnalyticsFrame(root, db=db)
    ana.refresh()

    # 7. Onboarding / Plan Builder
    onb = OnboardingFrame(root, db=db)
    onb.refresh()

    # 8. Settings
    sett = SettingsFrame(root, db=db)
    sett.refresh()

    print("      [OK] All 7 screens instantiated and rendered cleanly with seed data.")

    # Test Zero-Data Edge Case
    print("[6/6] Testing Zero-Data Edge Case Handling...")
    db.reset_all_data()

    # Verify zero data doesn't crash any frame
    dash.refresh()
    ht.refresh()
    cal.refresh()
    todo.refresh()
    ana.refresh()
    onb.refresh()
    sett.refresh()

    print("      [OK] All 7 screens handled zero-data state cleanly without error.")

    db.close()
    if os.path.exists(test_db_file):
        os.remove(test_db_file)
    root.destroy()


if __name__ == "__main__":
    print("==================================================")
    print("Running Momentum Full Verification Suite...")
    print("==================================================")
    test_streak_calculation()
    test_database_and_crud()
    test_seed_data_generation()
    test_path_helper_and_assets()
    test_ui_screens_rendering()
    print("==================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")
