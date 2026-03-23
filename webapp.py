from flask import Flask, request, jsonify, render_template_string
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def ask_ai(question):
    try:
        prompt = f"""You are an expert MCAT tutor.
        Answer this question clearly and concisely:
        {question}
        Format with emojis and clear sections."""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# HTML Template
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
        .quick-btn:active { background: #4ecca3; color: #1a1a2e; }
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
        }
        .typing {
            background: #16213e;
            color: #4ecca3;
            padding: 10px 15px;
            border-radius: 15px;
            align-self: flex-start;
            display: none;
        }
    </style>
</head>
<body>
    <div class="header">🎓 MCAT Study Agent</div>

    <div class="chat-box" id="chatBox">
        <div class="message bot-msg">
            👋 Welcome to your MCAT Study Agent!
            
I can help you with:
📚 All MCAT subjects
📝 Practice questions
📅 Study plan
❓ Any MCAT question

Choose a topic below or type your question!
        </div>
    </div>

    <div class="quick-buttons">
        <button class="quick-btn" onclick="sendQuick('Explain DNA replication')">🧬 DNA Replication</button>
        <button class="quick-btn" onclick="sendQuick('Explain Le Chatelier principle')">⚗️ Le Chatelier</button>
        <button class="quick-btn" onclick="sendQuick('Generate 3 biology practice questions')">📝 Biology Quiz</button>
        <button class="quick-btn" onclick="sendQuick('Create an 8 week MCAT study plan')">📅 Study Plan</button>
        <button class="quick-btn" onclick="sendQuick('Explain Freud theories for MCAT')">🧠 Psychology</button>
        <button class="quick-btn" onclick="sendQuick('Explain oxidative phosphorylation')">🔬 Biochemistry</button>
    </div>

    <div class="typing" id="typing">Agent is thinking... ⏳</div>

    <div class="input-area">
        <input
            type="text"
            id="userInput"
            placeholder="Ask any MCAT question..."
            onkeypress="handleKey(event)"
        />
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        function addMessage(text, isUser) {
            const chatBox = document.getElementById('chatBox');
            const msg = document.createElement('div');
            msg.className = `message ${isUser ? 'user-msg' : 'bot-msg'}`;
            msg.textContent = text;
            chatBox.appendChild(msg);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function showTyping(show) {
            document.getElementById('typing').style.display = show ? 'block' : 'none';
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            addMessage(message, true);
            input.value = '';
            showTyping(true);

            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: message})
                });
                const data = await response.json();
                showTyping(false);
                addMessage(data.answer, false);
            } catch (error) {
                showTyping(false);
                addMessage('Error: Could not get response. Try again!', false);
            }
        }

        function sendQuick(message) {
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
    print("Open on phone: http://YOUR-IP:5000")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=False)