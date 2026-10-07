"""
database.py
------------
All SQLite access for SignBridge AI lives here, so app.py stays a thin
routing layer. Tracks quiz results (per student) and two-way messages,
and derives adaptive-learning stats (accuracy, streak, weak signs).
"""
import os
import sqlite3
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "signbridge.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quiz_type TEXT NOT NULL,
            sign_word TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            phrase TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Quiz results
# ---------------------------------------------------------------------------
def record_quiz_result(student_name, category, quiz_type, sign_word, is_correct):
    now = datetime.now()
    conn = get_connection()
    conn.execute(
        """INSERT INTO quiz_results
           (student_name, category, quiz_type, sign_word, is_correct, created_at, created_date)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (student_name, category, quiz_type, sign_word, int(is_correct),
         now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d")),
    )
    conn.commit()
    conn.close()


def get_progress(student_name):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM quiz_results WHERE student_name = ? ORDER BY id DESC",
        (student_name,),
    ).fetchall()
    conn.close()

    total = len(rows)
    correct = sum(r["is_correct"] for r in rows)
    accuracy = round((correct / total) * 100, 1) if total else 0.0

    signs_learned = sorted({r["sign_word"] for r in rows if r["is_correct"]})

    # weak signs: attempted >=1, wrong more than right (or only ever wrong)
    per_sign = {}
    for r in rows:
        s = per_sign.setdefault(r["sign_word"], {"correct": 0, "wrong": 0, "category": r["category"]})
        if r["is_correct"]:
            s["correct"] += 1
        else:
            s["wrong"] += 1
    weak_signs = [
        {"word": word, "correct": s["correct"], "wrong": s["wrong"], "category": s["category"]}
        for word, s in per_sign.items() if s["wrong"] > s["correct"]
    ]
    weak_signs.sort(key=lambda s: s["wrong"] - s["correct"], reverse=True)

    completed_categories = sorted({r["category"] for r in rows})

    # streak: consecutive days (including today or yesterday) with >=1 attempt
    dates = sorted({r["created_date"] for r in rows}, reverse=True)
    streak = 0
    if dates:
        today = datetime.now().date()
        expected = today
        for d_str in dates:
            d = datetime.strptime(d_str, "%Y-%m-%d").date()
            if d == expected:
                streak += 1
                expected = expected - timedelta(days=1)
            elif d == expected + timedelta(days=1):
                continue
            else:
                break

    recommended_practice = [w["word"] for w in weak_signs[:5]]
    if not recommended_practice:
        # nothing weak yet -> suggest unattempted signs isn't DB's job (needs sign list);
        # caller (ai_service/app) will fill this in if empty.
        recommended_practice = []

    return {
        "student_name": student_name,
        "total_attempts": total,
        "correct_attempts": correct,
        "accuracy": accuracy,
        "signs_learned": signs_learned,
        "signs_learned_count": len(signs_learned),
        "weak_signs": weak_signs[:8],
        "completed_categories": completed_categories,
        "streak": streak,
        "recommended_practice": recommended_practice,
    }


# ---------------------------------------------------------------------------
# Two-way messages
# ---------------------------------------------------------------------------
def add_message(sender, phrase):
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (sender, phrase, created_at) VALUES (?, ?, ?)",
        (sender, phrase, datetime.now().strftime("%H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_recent_messages(limit=30):
    conn = get_connection()
    rows = conn.execute(
        "SELECT sender, phrase, created_at FROM messages ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
