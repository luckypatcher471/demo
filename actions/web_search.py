import re
from serpapi import GoogleSearch 
from tts import edge_speak
from memory.config_manager import get_serpapi_key

MAX_NEWS_ITEMS = 3

def clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\(.*?\)|\[.*?\]", "", text)
    text = text.strip()
    text = re.sub(r"\.{2,}", ".")
    text = re.sub(r"\s*—\s*", " - ", text)
    return text

def is_trash(text: str) -> bool:
    t = text.lower()
    spam_keywords = [
        "click here", "read more", "advertisement", "sponsored",
        "subscribe", "newsletter", "sign up",
        "official website", "visit our", "learn more",
        "top 10"
    ]
    return any(keyword in t for keyword in spam_keywords)

def extract_clean_news(result: dict) -> str:
    title = clean(result.get("title", ""))
    snippet = clean(result.get("snippet", ""))
    if not title:
        return ""
    if snippet.startswith(title[:30]) or snippet == title:
        return title
    if len(snippet) > 120:
        snippet = snippet[:120]
        last_period = snippet.rfind(".")
        last_space = snippet.rfind(" ")
        if last_period > 80:
            snippet = snippet[:last_period + 1]
        elif last_space > 80:
            snippet = snippet[:last_space] + "..."
        return f"{title}. {snippet}"
    return title

def format_news_output(news_items: list) -> str:
    if len(news_items) == 1:
        return news_items[0]
    elif len(news_items) == 2:
        return f"{news_items[0]}. Also, {news_items[1]}"
    else:
        result = news_items[0]
        for item in news_items[1:-1]:
            result += f". {item}"
        result += f". Additionally, {news_items[-1]}"
        return result
    
def serpapi_search(query: str) -> str:
    api_key = get_serpapi_key()
    if not api_key:
        return "Sir, the web search system is not configured."

    clean_query = query
    if "campus" not in query.lower() and "library" not in query.lower() and "event" not in query.lower():
        clean_query = f"campus {query}"

    params = {
        "q": clean_query,
        "engine": "google_news",
        "hl": "en",
        "gl": "us",
        "num": 15,
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        data = search.get_dict()
        results = data.get("news_results", [])
    except Exception:
        params["engine"] = "google"
        try:
            search = GoogleSearch(params)
            data = search.get_dict()
            results = data.get("organic_results", [])
        except Exception:
            return "Sir, I couldn't connect to the search service."

    if not results:
        return "Sir, I couldn't find any recent news about that."

    news_items = []
    for result in results:
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        if is_trash(title) or is_trash(snippet):
            continue
        news_text = extract_clean_news(result)
        if news_text and len(news_text.split()) >= 6:
            news_items.append(news_text)
        if len(news_items) >= MAX_NEWS_ITEMS:
            break

    if not news_items:
        return "Sir, I found some results but they weren't clear news stories."

    return format_news_output(news_items)

def web_search(parameters, player=None, session_memory=None):
    query = (parameters or {}).get("query", "").strip()
    if not query:
        msg = "Sir, I couldn't understand the campus search request."
        edge_speak(msg)
        return msg

    answer = serpapi_search(query)

    if player:
        player.write_log(f"AI: {answer}")

    edge_speak(answer)

    if session_memory:
        session_memory.set_last_search(query, answer)

    return answer