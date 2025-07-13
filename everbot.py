import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# === CONFIG ===
TELEGRAM_TOKEN = "8181440373:AAErYCdjo9SK9--FPs3_DRJUPXlu6KPSsFU"
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "mistralai/mixtral-8x7b-instruct"

# Optional in-memory memory (basic)
user_histories = {}

# === AI REQUEST FUNCTION ===
def ask_mixtral(user_id, user_input):
    # Get history for this user
    history = user_histories.get(user_id, [])
    # Prepare messages list (system + past + current)
    messages = [{"role": "system", "content": "You are a wise spiritual guide like Alexander Bratchikov. Give soulful, clear, and deep advice rooted in body awareness and presence."}]
    messages += history[-5:]  # keep last 5 turns for memory
    messages.append({"role": "user", "content": user_input})

    # Request
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://t.me/ever_bot",  # change if needed
        "Content-Type": "application/json"
    }

    data = {
        "model": OPENROUTER_MODEL,
        "messages": messages
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    reply = response.json()["choices"][0]["message"]["content"]

    # Store history
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": reply})
    user_histories[user_id] = history[-10:]  # keep memory trimmed

    return reply

# === TELEGRAM HANDLER ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = update.message.chat_id
    reply = ask_mixtral(user_id, user_input)
    await update.message.reply_text(reply)

# === MAIN ===
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
