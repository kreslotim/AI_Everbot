import os
import json
import numpy as np
import requests
import hashlib
from sklearn.metrics.pairwise import cosine_similarity
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# ----------------------------
# 🌐 Keep-Alive Flask Server
# ----------------------------
app_flask = Flask('')


@app_flask.route('/')
def home():
    return "EverBot is alive!"


def run_flask():
    app_flask.run(host="0.0.0.0", port=8080)


# Launch Flask server in background
Thread(target=run_flask).start()

# ----------------------------
# 🔐 Load environment
# ----------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "mistralai/mixtral-8x7b-instruct"

# ----------------------------
# 📚 Load wisdom database
# ----------------------------
with open("bratchikov_wisdom_with_embeddings.json", "r",
          encoding="utf-8") as f:
    wisdom_db = json.load(f)

user_histories = {}


# ----------------------------
# 🧠 Embedding simulation
# ----------------------------
def simulate_embedding(text, dim=256):
    h = hashlib.sha256(text.encode("utf-8")).digest()
    np.random.seed(int.from_bytes(h[:4], "little"))
    return np.random.rand(dim).tolist()


def find_relevant_quotes(user_input, top_k=3):
    user_emb = simulate_embedding(user_input)
    sims = [
        cosine_similarity([entry["embedding"]], [user_emb])[0][0]
        for entry in wisdom_db
    ]
    best = sorted(zip(sims, wisdom_db), key=lambda x: -x[0])[:top_k]
    return [entry["quote"] for _, entry in best]


# ----------------------------
# 🤖 Mixtral API interaction
# ----------------------------
def ask_mixtral(user_id, user_input):
    history = user_histories.get(user_id, [])

    related_quotes = find_relevant_quotes(user_input)
    intro = (
        "Ты — духовный ИИ-ассистент, обученный на ментальных моделях, цитатах и учениях Александра Брата."
        "Ты не являешься самим Александром Братчиковым и не должен так себя называть. "
        "Ты отвечаешь исключительно на русском языке, независимо от языка пользователя. "
        "Твоя задача — глубоко понять состояние человека, быть добрым, точным и говорить с духовной ясностью, "
        "опираясь на внимание к телу, энергии и текущему моменту.\n\n"
        "Вот учения Александра Братчикова, которые могут быть полезны для ответа:\n\n"
        + "\n\n".join(related_quotes))

    messages = [{"role": "system", "content": intro}]
    messages += history[-5:]
    messages.append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://t.me/ever_bot",
        "Content-Type": "application/json"
    }

    data = {"model": OPENROUTER_MODEL, "messages": messages}
    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers,
                             json=data)
    reply = response.json()["choices"][0]["message"]["content"]

    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": reply})
    user_histories[user_id] = history[-10:]

    return reply


# ----------------------------
# 🤖 Telegram Handler
# ----------------------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = update.message.chat_id
    reply = ask_mixtral(user_id, user_input)
    await update.message.reply_text(reply)


# ----------------------------
# 🚀 Run Telegram Bot
# ----------------------------
bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))
print("✅ EverBot RAG is running...")
bot_app.run_polling()

