import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from openai import OpenAI

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ─────────────────────────────
# OPENROUTER AI BRAIN
# ─────────────────────────────
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# ─────────────────────────────
# MCAT SUBJECTS
# ─────────────────────────────
MCAT_SUBJECTS = {
    "1": "Biology & Biochemistry",
    "2": "Chemistry & Physics",
    "3": "Psychology & Sociology",
    "4": "Critical Analysis & Reading",
    "5": "Full Practice Test",
    "6": "Study Plan",
    "7": "Progress Tracker"
}

# Store user progress
user_progress = {}

# ─────────────────────────────
# AI FUNCTIONS
# ─────────────────────────────
def ask_mcat_ai(question: str, subject: str = "general") -> str:
    """Ask AI a MCAT related question"""
    try:
        response = client.chat.completions.create(
            model="stepfun/step-3.5-flash:free",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert MCAT tutor 
                    specializing in {subject}.
                    You help students prepare for the MCAT exam.
                    Always:
                    1. Give clear detailed explanations
                    2. Use simple language
                    3. Give relevant examples
                    4. End with a practice question
                    5. Keep responses focused and organized
                    Format your response with:
                    📚 EXPLANATION:
                    💡 EXAMPLE:
                    ❓ PRACTICE QUESTION:"""
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def generate_practice_questions(subject: str, difficulty: str = "medium") -> str:
    """Generate MCAT practice questions"""
    try:
        response = client.chat.completions.create(
            model="stepfun/step-3.5-flash:free",
            messages=[
                {
                    "role": "system",
                    "content": """You are an MCAT exam expert.
                    Generate realistic MCAT style questions.
                    Format each question as:
                    Question number and text
                    A) option
                    B) option
                    C) option
                    D) option
                    ✅ Answer: correct letter
                    📖 Explanation: why it is correct"""
                },
                {
                    "role": "user",
                    "content": f"""Generate 3 {difficulty} difficulty 
                    MCAT practice questions for {subject}.
                    Make them realistic MCAT style."""
                }
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def generate_study_plan(weeks: int = 8) -> str:
    """Generate a 2 month MCAT study plan"""
    try:
        response = client.chat.completions.create(
            model="stepfun/step-3.5-flash:free",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert MCAT coach.
                    Create detailed realistic study plans.
                    Format as:
                    WEEK number:
                    Monday - Friday: specific topics
                    Weekend: review and practice tests
                    Daily study time recommendation"""
                },
                {
                    "role": "user",
                    "content": f"""Create a detailed {weeks} week 
                    MCAT study plan covering all sections:
                    - Biology and Biochemistry
                    - Chemistry and Physics
                    - Psychology and Sociology
                    - Critical Analysis and Reading
                    Include daily goals and weekly milestones."""
                }
            ],
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def get_topic_summary(topic: str) -> str:
    """Get a quick summary of an MCAT topic"""
    try:
        response = client.chat.completions.create(
            model="stepfun/step-3.5-flash:free",
            messages=[
                {
                    "role": "system",
                    "content": """You are an MCAT tutor.
                    Give concise topic summaries.
                    Format as:
                    📌 KEY CONCEPTS:
                    🔑 IMPORTANT FACTS:
                    ⚠️ COMMON MISTAKES:
                    📝 QUICK TIPS:"""
                },
                {
                    "role": "user",
                    "content": f"Give me a quick MCAT summary of: {topic}"
                }
            ],
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# ─────────────────────────────
# PROGRESS TRACKING
# ─────────────────────────────
def update_progress(user_id: int, subject: str):
    """Track user study progress"""
    if user_id not in user_progress:
        user_progress[user_id] = {
            "sessions": 0,
            "subjects_studied": [],
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "last_study": ""
        }
    user_progress[user_id]["sessions"] += 1
    if subject not in user_progress[user_id]["subjects_studied"]:
        user_progress[user_id]["subjects_studied"].append(subject)
    user_progress[user_id]["last_study"] = datetime.now().strftime("%Y-%m-%d %H:%M")

def get_progress(user_id: int) -> str:
    """Get user progress report"""
    if user_id not in user_progress:
        return "No study sessions recorded yet. Start studying!"

    progress = user_progress[user_id]
    subjects = ", ".join(progress["subjects_studied"]) or "None yet"

    return (
        f"📊 YOUR STUDY PROGRESS\n\n"
        f"📅 Started: {progress['start_date']}\n"
        f"🕐 Last Study: {progress['last_study']}\n"
        f"📚 Total Sessions: {progress['sessions']}\n"
        f"✅ Subjects Covered:\n{subjects}\n\n"
        f"Keep it up! Consistency is key! 💪"
    )

# ─────────────────────────────
# TELEGRAM HANDLERS
# ─────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    keyboard = [
        ["📚 Biology & Biochemistry", "⚗️ Chemistry & Physics"],
        ["🧠 Psychology & Sociology", "📖 Critical Analysis"],
        ["📝 Practice Questions", "📅 Study Plan"],
        ["📊 My Progress", "❓ Ask Anything"]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Welcome to your MCAT Study Agent!\n\n"
        "I will help you prepare for the MCAT exam "
        "in 2 months!\n\n"
        "I can help you with:\n"
        "📚 All MCAT subjects\n"
        "📝 Practice questions\n"
        "📅 Personalized study plan\n"
        "📊 Progress tracking\n"
        "❓ Answer any MCAT question\n\n"
        "Choose a subject or ask me anything! 👇",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message"""
    await update.message.reply_text(
        "📚 MCAT STUDY AGENT HELP\n\n"
        "Commands:\n"
        "/start - Main menu\n"
        "/plan - Get 2 month study plan\n"
        "/practice - Get practice questions\n"
        "/progress - See your progress\n"
        "/summary <topic> - Get topic summary\n\n"
        "Or just type any MCAT question!\n\n"
        "Examples:\n"
        "• Explain DNA replication\n"
        "• What is Le Chatelier principle?\n"
        "• Explain Freud theories\n"
        "• Give me biology questions\n"
        "• What should I study today?"
    )

async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate study plan"""
    await update.message.reply_text(
        "📅 Generating your 2 month study plan...\n"
        "Please wait ⏳"
    )
    plan = generate_study_plan(8)
    # Split if too long for Telegram
    if len(plan) > 4000:
        parts = [plan[i:i+4000] for i in range(0, len(plan), 4000)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(plan)

async def practice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate practice questions menu"""
    keyboard = [
        ["🔬 Biology Questions", "⚗️ Chemistry Questions"],
        ["🔭 Physics Questions", "🧠 Psychology Questions"],
        ["📖 Reading Questions", "🎯 Mixed Questions"]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )
    await update.message.reply_text(
        "📝 Choose a subject for practice questions:",
        reply_markup=reply_markup
    )

async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show progress"""
    user_id = update.effective_user.id
    progress = get_progress(user_id)
    await update.message.reply_text(progress)

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get topic summary"""
    if context.args:
        topic = ' '.join(context.args)
        await update.message.reply_text(
            f"📌 Getting summary for: {topic}...\n"
            "Please wait ⏳"
        )
        summary = get_topic_summary(topic)
        await update.message.reply_text(summary)
    else:
        await update.message.reply_text(
            "Please provide a topic!\n"
            "Example: /summary DNA replication"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all messages"""
    user_message = update.message.text
    user_id = update.effective_user.id

    # Show typing
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # Route based on button clicks
    if "Biology" in user_message:
        update_progress(user_id, "Biology")
        response = generate_practice_questions(
            "Biology and Biochemistry"
        )

    elif "Chemistry & Physics" in user_message or "Chemistry Questions" in user_message:
        update_progress(user_id, "Chemistry")
        response = generate_practice_questions(
            "General Chemistry and Physics"
        )

    elif "Psychology" in user_message:
        update_progress(user_id, "Psychology")
        response = generate_practice_questions(
            "Psychology and Sociology"
        )

    elif "Critical Analysis" in user_message or "Reading Questions" in user_message:
        update_progress(user_id, "Critical Analysis")
        response = generate_practice_questions(
            "Critical Analysis and Reading"
        )

    elif "Practice Questions" in user_message or "Mixed Questions" in user_message:
        update_progress(user_id, "Mixed")
        response = generate_practice_questions(
            "Mixed MCAT topics"
        )

    elif "Study Plan" in user_message:
        await update.message.reply_text(
            "📅 Generating your 2 month study plan...\n"
            "Please wait ⏳"
        )
        response = generate_study_plan(8)

    elif "My Progress" in user_message:
        response = get_progress(user_id)

    elif "Physics Questions" in user_message:
        update_progress(user_id, "Physics")
        response = generate_practice_questions("Physics")

    elif "Ask Anything" in user_message:
        response = (
            "Sure! Ask me any MCAT question!\n\n"
            "Examples:\n"
            "• Explain DNA replication\n"
            "• What is oxidative phosphorylation?\n"
            "• Explain Pavlovian conditioning\n"
            "• What is Boyle law?\n"
            "• How does enzyme kinetics work?"
        )

    else:
        # Send to AI for any other question
        update_progress(user_id, "General")
        response = ask_mcat_ai(user_message)

    # Handle long responses
    if len(response) > 4000:
        parts = [
            response[i:i+4000]
            for i in range(0, len(response), 4000)
        ]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(response)

# ─────────────────────────────
# MAIN
# ─────────────────────────────
def main():
    print("="*50)
    print("MCAT Study Agent Starting...")
    print("Open Telegram and message your bot!")
    print("Press Ctrl+C to stop")
    print("="*50)

    app = Application.builder().token(
        os.getenv("TELEGRAM_BOT_TOKEN")
    ).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("plan", plan_command))
    app.add_handler(CommandHandler("practice", practice_command))
    app.add_handler(CommandHandler("progress", progress_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()