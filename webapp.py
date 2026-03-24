from flask import Flask, request, jsonify, render_template_string
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# OpenRouter AI Brain
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def ask_ai(question):
    try:
        response = client.chat.completions.create(
            model="stepfun/step-3.5-flash:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are an MCAT tutor. Be brief and clear. Max 3 sentences per section."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=250,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>MCAT Study Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #1a1a2e;
            color: white;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: #16213e;
            padding: 15px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            color: #4ecca3;
        }
        .chat-box {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .message {
            padding: 12px 15px;
            border-radius: 15px;
            max-width: 85%;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .user-msg {
            background: #4ecca3;
            color: #1a1a2e;
            align-self: flex-end;
            border-bottom-right-radius: 3px;
        }
        .bot-msg {
            background: #16213e;
            color: white;
            align-self: flex-start;
            border-bottom-left-radius: 3px;
        }
        .thinking {
            background: #16213e;
            color: #4ecca3;
            padding: 10px 15px;
            border-radius: 15px;
            align-self: flex-start;
            font-style: italic;
        }
        .quick-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            padding: 10px;
        }
        .quick-btn {
            background: #16213e;
            color: #4ecca3;
            border: 1px solid #4ecca3;
            padding: 10px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 13px;
            text-align: center;
        }
        .quick-btn:active {
            background: #4ecca3;
            color: #1a1a2e;
        }
        .input-area {
            display: flex;
            padding: 10px;
            gap: 8px;
            background: #16213e;
        }
        .input-area input {
            flex: 1;
            padding: 12px;
            border-radius: 25px;
            border: 1px solid #4ecca3;
            background: #1a1a2e;
            color: white;
            font-size: 15px;
            outline: none;
        }
        .input-area button {
            background: #4ecca3;
            color: #1a1a2e;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            font-size: 15px;
            min-width: 70px;
        }
        .input-area button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="header">🎓 MCAT Study Agent</div>

    <div class="chat-box" id="chatBox">
        <div class="message bot-msg">
👋 Welcome to MCAT Study Agent!

📚 All MCAT subjects
📝 Practice questions
📅 Study plan
❓ Any MCAT question

Type your question or tap a button below!
        </div>
    </div>

    <div class="quick-buttons">
        <button class="quick-btn" onclick="sendQuick('Explain DNA replication')">🧬 DNA</button>
        <button class="quick-btn" onclick="sendQuick('Explain Le Chatelier principle')">⚗️ Chemistry</button>
        <button class="quick-btn" onclick="sendQuick('Give 3 biology practice questions')">📝 Quiz</button>
        <button class="quick-btn" onclick="sendQuick('Create 8 week MCAT study plan')">📅 Plan</button>
        <button class="quick-btn" onclick="sendQuick('Explain Freud theories')">🧠 Psychology</button>
        <button class="quick-btn" onclick="sendQuick('Explain oxidative phosphorylation')">🔬 Biochem</button>
    </div>

    <div class="input-area">
        <input
            type="text"
            id="userInput"
            placeholder="Ask any MCAT question..."
            onkeypress="handleKey(event)"
        />
        <button onclick="sendMessage()" id="sendBtn">Send</button>
    </div>

    <script>
        let isWaiting = false;
        let thinkingEl = null;

        function addMessage(text, isUser) {
            const chatBox = document.getElementById('chatBox');
            const msg = document.createElement('div');
            msg.className = `message ${isUser ? 'user-msg' : 'bot-msg'}`;
            msg.textContent = text;
            chatBox.appendChild(msg);
            chatBox.scrollTop = chatBox.scrollHeight;
            return msg;
        }

        function showThinking() {
            const chatBox = document.getElementById('chatBox');
            thinkingEl = document.createElement('div');
            thinkingEl.className = 'thinking';
            thinkingEl.textContent = '⏳ Thinking...';
            chatBox.appendChild(thinkingEl);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function hideThinking() {
            if (thinkingEl) {
                thinkingEl.remove();
                thinkingEl = null;
            }
        }

        async function sendMessage() {
            if (isWaiting) return;
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            addMessage(message, true);
            input.value = '';
            isWaiting = true;
            showThinking();

            const btn = document.getElementById('sendBtn');
            btn.disabled = true;
            btn.textContent = '...';

            try:
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: message})
                });
                const data = await response.json();
                hideThinking();
                addMessage(data.answer, false);
            } catch (error) {
                hideThinking();
                addMessage('Error: Try again!', false);
            }

            isWaiting = false;
            btn.disabled = false;
            btn.textContent = 'Send';
        }

        function sendQuick(message) {
            if (isWaiting) return;
            document.getElementById('userInput').value = message;
            sendMessage();
        }

        function handleKey(event) {
            if (event.key === 'Enter') sendMessage();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    answer = ask_ai(question)
    return jsonify({'answer': answer})

if __name__ == '__main__':
    print("="*50)
    print("MCAT Web App Starting...")
    print("="*50)
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
