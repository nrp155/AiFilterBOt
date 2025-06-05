
import re
import openai
import os
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import Message

# MongoDB setup using environment variables
DATABASE_NAME = os.environ.get('DATABASE_NAME', "Cluster0")
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'Cluster0')
MONGO_URI = os.environ.get('DATABASE_URI', "mongodb+srv://subscenelkbatch:subscenelkbatch@cluster0.bbbnzwo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

client = MongoClient(MONGO_URI)
collection = client[DATABASE_NAME][COLLECTION_NAME]

# OpenAI API setup
openai.api_key = os.environ.get("OPENAI_API_KEY", "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")

# Safe suggestion logic
def get_suggested_title(query):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Suggest the correct or closest movie title for user input."},
                {"role": "user", "content": f"Find a matching movie title for: {query}"}
            ],
            max_tokens=25,
            temperature=0.5
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("AI suggestion failed:", e)
        return None

def search_movie(title):
    return collection.find_one({"title": {"$regex": f"^{re.escape(title)}$", "$options": "i"}})

@Client.on_message(filters.command("ai") & filters.private)
async def ai_filter(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❗ Please provide a movie name to search.")
        return

    query = message.text.split(None, 1)[1]

    # Try AI spell-check suggestion
    suggested_title = get_suggested_title(query)

    # Fallback to original if AI fails
    search_title = suggested_title if suggested_title else query

    movie = search_movie(search_title)
    if movie:
        reply = f"🎬 **Title**: {movie.get('title')}
📁 **File ID**: `{movie.get('file_id', 'N/A')}`"
    else:
        reply = f"❌ Movie not found.
🧠 AI Suggestion: `{suggested_title}`" if suggested_title else "❌ Movie not found."

    await message.reply_text(reply)
