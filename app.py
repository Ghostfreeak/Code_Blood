import os
import json
import sqlite3
import traceback
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from dotenv import load_dotenv
from groq import Groq
from authlib.integrations.flask_client import OAuth

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chattutor-secret-dev-key-change-in-prod")

# ─── Groq client ───────────────────────────────────────────────────────────────
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ─── Google OAuth ──────────────────────────────────────────────────────────────
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# ─── Database ──────────────────────────────────────────────────────────────────
DB_PATH = "chattutor.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT UNIQUE,
            email TEXT UNIQUE,
            name TEXT,
            avatar TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            topic TEXT,
            difficulty TEXT,
            score INTEGER,
            total INTEGER,
            questions_json TEXT,
            answers_json TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ─── Auth helpers ──────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if "user_id" not in session:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return dict(user) if user else None

# ─── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are ChatTutor, an expert AI tutor designed to help students learn effectively.

Your personality:
- Encouraging, patient, and supportive
- Clear and concise explanations
- Use examples and analogies
- Break things step-by-step
- Ask follow-up questions

Teaching style:
1. Start simple
2. Break into steps
3. Use examples
4. Encourage thinking

Always end explanations with:
"Does that make sense? Want me to clarify any part?"
"""

QUIZ_SYSTEM_PROMPT = """You are a quiz generator. Generate exactly {count} multiple-choice questions about "{topic}" at {difficulty} difficulty level.

Return ONLY valid JSON in this exact format, no other text:
{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
      "correct": "A",
      "explanation": "Brief explanation of why A is correct."
    }}
  ]
}}
"""

# ─── Auth routes ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("chat"))
    return render_template("login.html")

@app.route("/login/google")
def login_google():
    redirect_uri = url_for("auth_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/callback")
def auth_callback():
    try:
        token = google.authorize_access_token()
        userinfo = token.get("userinfo")
        if not userinfo:
            return redirect(url_for("index"))

        google_id = userinfo["sub"]
        email = userinfo["email"]
        name = userinfo.get("name", email.split("@")[0])
        avatar = userinfo.get("picture", "")

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE google_id = ?", (google_id,)).fetchone()
        if existing:
            user_id = existing["id"]
            conn.execute("UPDATE users SET name=?, avatar=? WHERE id=?", (name, avatar, user_id))
        else:
            cur = conn.execute(
                "INSERT INTO users (google_id, email, name, avatar) VALUES (?,?,?,?)",
                (google_id, email, name, avatar)
            )
            user_id = cur.lastrowid
        conn.commit()
        conn.close()

        session["user_id"] = user_id
        session["user_name"] = name
        session["user_email"] = email
        session["user_avatar"] = avatar
        return redirect(url_for("chat"))
    except Exception as e:
        print("Auth error:", e)
        traceback.print_exc()
        return redirect(url_for("index"))

@app.route("/login/demo")
def login_demo():
    """Demo login without Google OAuth - for local testing"""
    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@chattutor.com",)).fetchone()
    if existing:
        user_id = existing["id"]
    else:
        cur = conn.execute(
            "INSERT INTO users (google_id, email, name, avatar) VALUES (?,?,?,?)",
            ("demo_user", "demo@chattutor.com", "Demo Student", "")
        )
        user_id = cur.lastrowid
    conn.commit()
    conn.close()

    session["user_id"] = user_id
    session["user_name"] = "Demo Student"
    session["user_email"] = "demo@chattutor.com"
    session["user_avatar"] = ""
    return redirect(url_for("chat"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ─── Main chat page ────────────────────────────────────────────────────────────
@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect(url_for("index"))
    user = get_current_user()
    return render_template("chat.html", user=user)

# ─── API: user info ────────────────────────────────────────────────────────────
@app.route("/api/me")
@login_required
def me():
    return jsonify(get_current_user())

# ─── API: chat sessions ────────────────────────────────────────────────────────
@app.route("/api/sessions")
@login_required
def get_sessions():
    conn = get_db()
    rows = conn.execute("""
        SELECT session_id, MIN(content) as preview, MAX(created_at) as last_at, COUNT(*) as msg_count
        FROM messages
        WHERE user_id = ? AND role = 'user'
        GROUP BY session_id
        ORDER BY last_at DESC
        LIMIT 20
    """, (session["user_id"],)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/sessions/<sid>")
@login_required
def get_session_messages(sid):
    conn = get_db()
    rows = conn.execute("""
        SELECT role, content, created_at FROM messages
        WHERE user_id = ? AND session_id = ?
        ORDER BY created_at ASC
    """, (session["user_id"], sid)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ─── API: ask ──────────────────────────────────────────────────────────────────
@app.route("/api/ask", methods=["POST"])
@login_required
def ask():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        session_id = data.get("session_id", "default")

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        user_id = session["user_id"]
        user_name = session.get("user_name", "Student")

        # Load last 10 messages for context
        conn = get_db()
        history = conn.execute("""
            SELECT role, content FROM messages
            WHERE user_id = ? AND session_id = ?
            ORDER BY created_at DESC LIMIT 10
        """, (user_id, session_id)).fetchall()
        history = list(reversed(history))

        messages = [{"role": r["role"], "content": r["content"]} for r in history]
        messages.append({"role": "user", "content": user_message})

        system_msg = {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nStudent name: {user_name}. Use their name occasionally."}

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[system_msg] + messages
        )
        reply = response.choices[0].message.content

        # Save both messages
        conn.execute("INSERT INTO messages (user_id, session_id, role, content) VALUES (?,?,?,?)",
                     (user_id, session_id, "user", user_message))
        conn.execute("INSERT INTO messages (user_id, session_id, role, content) VALUES (?,?,?,?)",
                     (user_id, session_id, "assistant", reply))
        conn.commit()
        conn.close()

        return jsonify({"reply": reply})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500

# ─── API: generate quiz ────────────────────────────────────────────────────────
@app.route("/api/quiz/generate", methods=["POST"])
@login_required
def generate_quiz():
    try:
        data = request.get_json()
        topic = data.get("topic", "General Knowledge").strip()
        difficulty = data.get("difficulty", "medium")
        count = min(int(data.get("count", 5)), 10)

        prompt = QUIZ_SYSTEM_PROMPT.format(topic=topic, difficulty=difficulty, count=count)

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a JSON-only quiz generator. Return only valid JSON, no markdown, no explanation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        quiz_data = json.loads(raw)
        return jsonify({"quiz": quiz_data})

    except json.JSONDecodeError as e:
        return jsonify({"error": "Failed to parse quiz JSON", "raw": raw}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to generate quiz"}), 500

# ─── API: submit quiz ──────────────────────────────────────────────────────────
@app.route("/api/quiz/submit", methods=["POST"])
@login_required
def submit_quiz():
    try:
        data = request.get_json()
        topic = data.get("topic", "Unknown")
        difficulty = data.get("difficulty", "medium")
        questions = data.get("questions", [])
        user_answers = data.get("answers", {})  # {question_id: "A"}

        score = 0
        results = []
        for q in questions:
            qid = str(q["id"])
            user_ans = user_answers.get(qid, "")
            correct = q["correct"]
            is_correct = user_ans == correct
            if is_correct:
                score += 1
            results.append({
                "id": q["id"],
                "question": q["question"],
                "user_answer": user_ans,
                "correct_answer": correct,
                "is_correct": is_correct,
                "explanation": q.get("explanation", "")
            })

        user_id = session["user_id"]
        conn = get_db()
        conn.execute("""
            INSERT INTO quiz_attempts (user_id, topic, difficulty, score, total, questions_json, answers_json)
            VALUES (?,?,?,?,?,?,?)
        """, (user_id, topic, difficulty, score, len(questions),
              json.dumps(questions), json.dumps(user_answers)))
        conn.commit()
        conn.close()

        return jsonify({"score": score, "total": len(questions), "results": results})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to submit quiz"}), 500

# ─── API: quiz history ─────────────────────────────────────────────────────────
@app.route("/api/quiz/history")
@login_required
def quiz_history():
    conn = get_db()
    rows = conn.execute("""
        SELECT id, topic, difficulty, score, total, created_at
        FROM quiz_attempts
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    """, (session["user_id"],)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ─── API: quiz stats ───────────────────────────────────────────────────────────
@app.route("/api/quiz/stats")
@login_required
def quiz_stats():
    conn = get_db()
    rows = conn.execute("""
        SELECT topic, difficulty,
               COUNT(*) as attempts,
               SUM(score) as total_score,
               SUM(total) as total_questions,
               AVG(CAST(score AS FLOAT)/total*100) as avg_pct
        FROM quiz_attempts
        WHERE user_id = ?
        GROUP BY topic, difficulty
        ORDER BY attempts DESC
    """, (session["user_id"],)).fetchall()

    overall = conn.execute("""
        SELECT COUNT(*) as total_attempts,
               SUM(score) as total_correct,
               SUM(total) as total_questions
        FROM quiz_attempts WHERE user_id = ?
    """, (session["user_id"],)).fetchone()
    conn.close()

    return jsonify({
        "by_topic": [dict(r) for r in rows],
        "overall": dict(overall) if overall else {}
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)