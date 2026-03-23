from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
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

def ask_ai_stream(question):
    """Stream AI response word by word"""
    try:
        stream = client.chat.completions.create(
            model="stepfun/step-3.5-flash:free",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert MCAT tutor.
                    Answer questions clearly and concisely.
                    Keep responses focused and brief.
                    Format with emojis and clear sections."""
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=300,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {str(e)}"

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
        .cursor {
            display: inline-block;
            width: 8px;
            height: 16px;
            background: #4ecca3;
            animation: blink 1s infinite;
            vertical-align: middle;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
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
        <button class="quick-btn" onclick="sendQuick('Explain DNA replication briefly')">🧬 DNA Replication</button>
        <button class="quick-btn" onclick="sendQuick('Explain Le Chatelier principle briefly')">⚗️ Le Chatelier</button>
        <button class="quick-btn" onclick="sendQuick('Give 3 biology practice questions')">📝 Biology Quiz</button>
        <button class="quick-btn" onclick="sendQuick('Create a brief 8 week MCAT study plan')">📅 Study Plan</button>
        <button class="quick-btn" onclick="sendQuick('Explain Freud theories for MCAT briefly')">🧠 Psychology</button>
        <button class="quick-btn" onclick="sendQuick('Explain oxidative phosphorylation briefly')">🔬 Biochemistry</button>
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
        let isStreaming = false;

        function addMessage(text, isUser) {
            const chatBox = document.getElementById('chatBox');
            const msg = document.createElement('div');
            msg.className = `message ${isUser ? 'user-msg' : 'bot-msg'}`;
            msg.textContent = text;
            chatBox.appendChild(msg);
            chatBox.scrollTop = chatBox.scrollHeight;
            return msg;
        }

        async function sendMessage() {
            if (isStreaming) return;
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            addMessage(message, true);
            input.value = '';
            isStreaming = true;

            // Disable send button
            document.getElementById('sendBtn').textContent = '...';
            document.getElementById('sendBtn').disabled = true;

            // Create bot message with cursor
            const chatBox = document.getElementById('chatBox');
            const botMsg = document.createElement('div');
            botMsg.className = 'message bot-msg';
            const cursor = document.createElement('span');
            cursor.className = 'cursor';
            botMsg.appendChild(cursor);
            chatBox.appendChild(botMsg);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const response = await fetch('/stream', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: message})
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullText = '';

                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value);
                    fullText += chunk;
                    botMsg.textContent = fullText;
                    botMsg.appendChild(cursor);
                    chatBox.scrollTop = chatBox.scrollHeight;
                }

                // Remove cursor when done
                botMsg.textContent = fullText;

            } catch (error) {
                botMsg.textContent = 'Error: Could not get response. Try again!';
            }

            isStreaming = false;
            document.getElementById('sendBtn').textContent = 'Send';
            document.getElementById('sendBtn').disabled = false;
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

@app.route('/stream', methods=['POST'])
def stream():
    data = request.json
    question = data.get('question', '')
    return Response(
        stream_with_context(ask_ai_stream(question)),
        mimetype='text/plain',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

# Keep old endpoint as backup
@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    try:
        response = client.chat.completions.create(
            model="stepfun/step-3.5-flash:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert MCAT tutor. Be concise."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=300
        )
        return jsonify({
            'answer': response.choices[0].message.content
        })
    except Exception as e:
        return jsonify({'answer': f"Error: {str(e)}"})

if __name__ == '__main__':
    print("="*50)
    print("MCAT Web App Starting...")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=False)