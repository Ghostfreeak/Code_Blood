import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from groq import Groq
import traceback

# Load env
load_dotenv()

app = Flask(__name__)

# Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 🔥 In-memory storage (user-wise)
user_chats = {}

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

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")


# ✅ GET USER HISTORY
@app.route("/history", methods=["POST"])
def get_history():
    data = request.get_json()
    username = data.get("username", "Student")

    return jsonify({
        "history": user_chats.get(username, [])
    })


# ✅ MAIN CHAT API
@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()

        user_message = data.get("message", "").strip()
        username = data.get("username", "Student")

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        # 🔥 Initialize user if not exists
        if username not in user_chats:
            user_chats[username] = []

        # Get last 10 messages for context
        history = user_chats[username][-10:]

        # Build messages
        messages = []

        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add new user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # System message
        system_message = {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nStudent name: {username}. Use their name sometimes."
        }

        # 🔥 GROQ API CALL
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[system_message] + messages
        )

        reply = response.choices[0].message.content

        # 🔥 SAVE CHAT (user-wise)
        user_chats[username].append({
            "role": "user",
            "content": user_message
        })

        user_chats[username].append({
            "role": "assistant",
            "content": reply
        })

        return jsonify({
            "reply": reply,
            "history": user_chats[username]
        })

    except Exception as e:
        print("🔥 ERROR:")
        traceback.print_exc()
        return jsonify({"error": "⚠️ Server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)