import logging
import telegram
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from rapidfuzz import fuzz
from groq import Groq
from django.conf import settings
from asgiref.sync import sync_to_async
from faq.models import FAQ
from feedback.models import Feedback

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
STAFF_CHAT_ID = "719361466"
client = Groq(api_key=settings.GROQ_API_KEY)


pending_questions = {}
@sync_to_async
def find_similar_faq(user_question):
    faqs = FAQ.objects.all()
    best_match, highest_score = None, 0
    for faq in faqs:
        score = fuzz.partial_ratio(user_question.lower(), faq.question.lower())
        if score > highest_score:
            highest_score, best_match = score, faq
    return best_match.answer if highest_score > 80 else None

@sync_to_async
def build_prompt(user_question):
    faqs = FAQ.objects.all()
    prompt = "\n".join([f"Q: {faq.question}\nA: {faq.answer}" for faq in faqs])
    return f"""You are a helpful resort assistant. Only answer based on the FAQ.
If unknown, respond: "I'm not sure about that. Let me ask a staff member to help you."

FAQs:
{prompt}

Now, answer this:
Q: {user_question}"""

@sync_to_async
def save_feedback(feedback_text, feedback_type, sector):
    feedback = Feedback(
        feedback_text=feedback_text,
        feedback_type=feedback_type,
        sector=sector
    )
    feedback.save()

@sync_to_async
def save_faq(question, answer):
    faq = FAQ(question = question, answer = answer)
    faq.save()

async def analyze_sentiment_and_sector(feedback_text):
    sentiment_prompt = f"Classify the sentiment of the following feedback as either 'Positive' or 'Negative'. Respond with only 'Positive' or 'Negative':\n{feedback_text}"

    
    try:
        sentiment_response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": sentiment_prompt}],
            max_tokens=50,
        )
        sentiment = sentiment_response.choices[0].message.content.strip().lower()
        if sentiment not in ['positive', 'negative']:
            print("chatgpt")
            sentiment = 'negative'

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        sentiment = 'negative'  

    
    sector_prompt = f"Classify the following feedback into one of these sectors: 'Customer Service', 'Housekeeping', 'Food & Beverage', 'Maintenance', 'General'. Respond with only the sector name.\n{feedback_text}"
    
    try:
        sector_response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": sector_prompt}],
            max_tokens=50,
        )
        sector = sector_response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Sector classification failed: {e}")
        sector = "General"

    return sentiment, sector

async def get_gpt_response(user_question):
    prompt = await build_prompt(user_question)
    try:
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print("🔥 GROQ ERROR:", e)
        return "There was a problem reaching the assistant."

# Bot logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Question", "Feedback"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Welcome! What would you like to do?", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = update.message.from_user.id

    if user_input.lower() == "question":
        context.user_data["mode"] = "question"
        await update.message.reply_text("Please type your question.")
    elif user_input.lower() == "feedback":
        context.user_data["mode"] = "feedback"
        await update.message.reply_text("We're listening. Please type your feedback.")
    else:
        mode = context.user_data.get("mode")
        if mode == "feedback":
            await forward_feedback_to_staff(update, context,user_input, user_id)
            
        else:
            await handle_question(update, context, user_input, user_id)

async def handle_question(update:Update, context:ContextTypes.DEFAULT_TYPE, user_question, user_id):
    answer = await find_similar_faq(user_question)
    if not answer:
        answer = await get_gpt_response(user_question)
        answer += "\n(This is GPT responding)"
        if "I'm not sure" in answer:
            await update.message.reply_text("Let me escalate this to a staff member.")
            pending_questions[user_id] = user_question
            await forward_to_staff(user_question, user_id)
            return
    await update.message.reply_text(answer)

async def forward_to_staff(question, user_id):
    bot = telegram.Bot(token=settings.TELEGRAM_API_KEY)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Reply to User", callback_data=f"reply_{user_id}")]
    ])
    await bot.send_message(chat_id=STAFF_CHAT_ID, text=f"New Question:\n{question}", reply_markup=reply_markup)

async def forward_feedback_to_staff(update:Update, context:ContextTypes.DEFAULT_TYPE,feedback, user_id):
    bot = telegram.Bot(token=settings.TELEGRAM_API_KEY)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Reply to User", callback_data=f"reply_{user_id}")]
    ])

    sentiment, sector = await analyze_sentiment_and_sector(feedback)

    
    await save_feedback(feedback, sentiment, sector)
    message = f"New Feedback:\nSentiment: {sentiment}\nSector: {sector}\nFeedback: {feedback}"
    await bot.send_message(chat_id=STAFF_CHAT_ID, text=message,reply_markup=reply_markup)
    await update.message.reply_text("Thank you for your feedback!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("reply_"):
        user_id = int(data.split("_")[1])
        context.user_data["reply_to_user_id"] = user_id
        await query.message.reply_text("Type your reply to the user.")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("reply_to_user_id")
    if user_id:
        bot = telegram.Bot(token=settings.TELEGRAM_API_KEY)
        await bot.send_message(chat_id=user_id, text=f"Staff reply: {update.message.text}")
        await update.message.reply_text("Reply sent to user.")
        question = pending_questions.get(user_id)
        answer = update.message.text
        if question:
            await save_faq(question,answer)
            del pending_questions[user_id]
        
        del context.user_data["reply_to_user_id"]
        


from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Runs the Telegram bot"

    def handle(self, *args, **kwargs):
        app = Application.builder().token(settings.TELEGRAM_API_KEY).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & filters.User(user_id=int(STAFF_CHAT_ID)), handle_admin_reply))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        app.run_polling()
