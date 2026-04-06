# 🎓 ChatTutor v2 — AI Tutor with Google Login, Quizzes & Progress Tracking

A full-stack AI tutoring app with per-user data, Google OAuth, auto-generated quizzes, and a progress dashboard.

---

## 📁 Folder Structure

```
chattutor/
├── app.py                  # Flask backend
├── requirements.txt
├── .env.example            # Copy to .env and fill in
├── chattutor.db            # SQLite DB (auto-created on first run)
├── README.md
└── templates/
    ├── login.html          # Google OAuth login page
    └── chat.html           # Chat + sidebar with quiz/track record
```

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up environment
```bash
cp .env.example .env
```

Fill in `.env`:
```
GROQ_API_KEY=gsk_...              # from console.groq.com
SECRET_KEY=some-random-string     # any long random string
GOOGLE_CLIENT_ID=...              # from Google Cloud Console
GOOGLE_CLIENT_SECRET=...          # from Google Cloud Console
```

### 3. Set up Google OAuth (for real login)
1. Go to https://console.cloud.google.com
2. Create a project → **APIs & Services** → **Credentials**
3. Click **Create Credentials** → **OAuth 2.0 Client ID**
4. Application type: **Web application**
5. Add Authorized redirect URI: `http://localhost:5000/auth/callback`
6. Copy Client ID and Client Secret into `.env`

> **Skip this for testing!** Just use the **⚡ Try Demo** button on the login page — no Google setup needed.

### 4. Run
```bash
python app.py
```
Visit: **http://localhost:5000**

---

## 🚀 Features

| Feature | Details |
|---|---|
| Google OAuth Login | Secure per-user accounts via Google |
| Demo Mode | Test instantly without Google setup |
| Per-user chat history | SQLite, isolated per account |
| Quiz Generator | AI generates MCQs on any topic |
| Difficulty levels | Easy / Medium / Hard |
| Answer explanations | Shown after each question |
| Track Record sidebar | Accuracy %, total quizzes, per-topic scores |
| Recent quiz history | Score badges in sidebar |
| Session history | Chat sessions listed in sidebar |
| Markdown rendering | Bold, code, lists, headers |
| Typing indicator | Animated while AI responds |

---

## 🔌 API Endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/api/me` | Current user info |
| GET | `/api/sessions` | List user's chat sessions |
| GET | `/api/sessions/<id>` | Get messages in a session |
| POST | `/api/ask` | Send a chat message |
| POST | `/api/quiz/generate` | Generate a quiz |
| POST | `/api/quiz/submit` | Submit answers, get score |
| GET | `/api/quiz/history` | List past quiz attempts |
| GET | `/api/quiz/stats` | Aggregated stats by topic |

---

## 🎨 Design

- **Background**: `#060b14` deep navy
- **Accent**: `#4fc3f7` sky blue + `#26a69a` teal
- **Font**: Sora + JetBrains Mono
- Sidebar: Quiz dashboard → Track record → Recent chats

---

Built with Flask + Groq (Llama 3.1) + SQLite + Authlib