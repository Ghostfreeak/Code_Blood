# 🎓 ChatTutor — AI-Powered Tutor Website

A hackathon-ready, full-stack AI tutoring web app built with Flask + Claude API.
Dark navy theme, smooth animations, chat history, session management, and more.

---

## 📁 Folder Structure

```
chattutor/
├── app.py                  # Flask backend (main server)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── README.md
├── templates/
│   ├── login.html          # Login page (username only)
│   └── chat.html           # Main chat interface
└── static/
    ├── css/
    │   ├── login.css       # Login page styles
    │   └── chat.css        # Chat page styles
    └── js/
        ├── login.js        # Login logic
        └── chat.js         # Chat logic (sessions, API calls, markdown)
```

---

## ⚙️ Setup Instructions

### 1. Clone / Download the project

```bash
cd chattutor
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Activate (Mac/Linux):
source venv/bin/activate

# Activate (Windows):
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your Anthropic API key

```bash
cp .env.example .env
```

Open `.env` and replace `your_api_key_here` with your actual key from https://console.anthropic.com

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 5. Run the app

```bash
python app.py
```

Visit: **http://localhost:5000**

---

## 🚀 Features

| Feature | Details |
|---|---|
| Login page | Username-only, no password required |
| Chat UI | Deep navy dark theme, eye-friendly |
| Session history | Saved to localStorage, up to 20 sessions |
| Profile panel | Username + avatar, switch user, clear data |
| Reset button | Clears current session with confirmation modal |
| Context memory | Last 5 message pairs sent to Claude API |
| Typing indicator | Animated 3-dot bounce while AI responds |
| Markdown rendering | Bold, italic, code blocks, lists, headers |
| Suggestion chips | Quick-start prompts on the welcome screen |
| Sidebar | Collapsible, shows session history |
| Responsive | Works on mobile and desktop |

---

## 🔌 API Endpoint

### `POST /ask`

**Request body:**
```json
{
  "message": "Explain recursion",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "username": "Alex"
}
```

**Success response:**
```json
{ "reply": "Recursion is a technique where..." }
```

**Error response:**
```json
{ "error": "Message cannot be empty" }
```

---

## 🎨 Design System

- **Background**: `#080d18` (deep navy)
- **Sidebar**: `#0b1220`
- **Cards/Messages**: `#0e1628` / `#0f1a2e`
- **Accent Blue**: `#4fc3f7`
- **Accent Teal**: `#26a69a`
- **Font**: Sora (display) + JetBrains Mono (code)

---

## 🏆 Hackathon Tips

- Present the login → chat flow live
- Show session history persistence (refresh and history remains)
- Demo markdown rendering with a code explanation question
- Show mobile responsiveness
- Highlight the `/ask` API with Postman for judges

---

Built with ❤️ using Flask + Claude AI
