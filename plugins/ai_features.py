import re
import difflib
import requests
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import Message

# MongoDB connection (configure if needed)
client = MongoClient("mongodb://localhost:27017/")
db = client['movie_database']
collection = db['movies']

# DeepSearch API
DEEPSEARCH_API_KEY = os.getenv("OPENAI_API_KEY_1")
DEEPSEARCH_URL = "https://deepsearch-api.openai.com/v1/search"

# Subtitle Sources Priority
SUB_SOURCES = [
    "https://subscenelk.com",
    "https://cineru.lk",
    "https://baiscope.lk",
    "https://zoom.lk"
]

def search_movie_in_db(title):
    movie = collection.find_one({"title": {"$regex": f"^{title}$", "$options": "i"}})
    if movie:
        return movie
    all_titles = [doc['title'] for doc in collection.find({}, {"title": 1})]
    closest = difflib.get_close_matches(title, all_titles, n=1, cutoff=0.6)
    if closest:
        return collection.find_one({"title": closest[0]})
    return None

def query_subtitles(title, lang_keywords):
    results = []
    for site in SUB_SOURCES:
        url = f"{site}/search?query={title}+{'%20'.join(lang_keywords)}"
        results.append(url)
    return results

def deepsearch_suggest(query):
    headers = os.getenv("OPENAI_API_KEY_1")
    payload = {
        "query": query,
        "top_k": 1
    }
    try:
        response = requests.post(DEEPSEARCH_URL, json=payload, headers=headers)
        if response.ok:
            result = response.json()
            return result.get("results", [{}])[0].get("text", query)
    except Exception as e:
        print("DeepSearch error:", e)
    return query

@Client.on_message(filters.private & filters.text)
async def ai_filter(client: Client, message: Message):
    text = message.text.lower()

    lang_keywords = []
    if "sinhala sub" in text or "sinhala subtitle" in text:
        lang_keywords = ["sinhala"]
    elif "english sub" in text or "english subtitle" in text:
        lang_keywords = ["english"]

    if re.search(r"marco(?:\\s+2024)?", text, re.IGNORECASE):
        title = "Marco 2024" if "2024" in text else "Marco"
        movie = search_movie_in_db(title)
        if movie:
            await message.reply_document(movie["file_id"], caption=f"🎬 Found: {movie['title']}")
        else:
            await message.reply_text("❌ Marco movie not found in database.")
        return

    suggested_title = deepsearch_suggest(message.text.strip())
    movie = search_movie_in_db(suggested_title)
    if movie:
        await message.reply_document(movie["file_id"], caption=f"🎬 Found: {movie['title']}")
        return

    if lang_keywords:
        sub_links = query_subtitles(suggested_title, lang_keywords)
        reply_text = f"🔍 Subtitles for **{suggested_title}**:\n\n" + "\n".join(sub_links)
        await message.reply_text(reply_text)
    else:
        await message.reply_text("❌ Sorry, movie not found. Try using correct title or subtitle format.")
