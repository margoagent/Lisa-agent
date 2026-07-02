#!/usr/bin/env python3
# Сбор медицинских новостей для утреннего отчёта
import feedparser, json, urllib.request, datetime

BOT_TOKEN = "8618486662:AAFg6kEECi5U3su0lt6FvL60noj_8j2bCzM"
CHAT_ID = "896792354"

FEEDS = [
    ("Медвестник", "https://medvestnik.ru/rss"),
    ("Vrachirf", "https://vrachirf.ru/rss.xml"),
    ("Medportal", "https://medportal.ru/rss/"),
    ("Vademecum (частные клиники)", "https://vademec.ru/rss/news/"),
]

KEYWORDS = [
    "уролог", "репродукт", "протокол лечен", "бесплоди", "ЭКО",
    "частн", "клиника", "медицин", "здравоохранен", "лечени"
]

def send_telegram(text):
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

now = datetime.datetime.utcnow()
yesterday = now - datetime.timedelta(hours=24)

all_news = []
for source, url in FEEDS:
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")[:200]
            link = entry.get("link", "")
            published = entry.get("published_parsed")

            # Только свежие новости (последние 24 часа)
            if published:
                pub_dt = datetime.datetime(*published[:6])
                if pub_dt < yesterday:
                    continue

            # Фильтр по ключевым словам
            text_lower = (title + " " + summary).lower()
            relevant = any(kw.lower() in text_lower for kw in KEYWORDS)

            if relevant or len(all_news) < 3:
                all_news.append((source, title, summary))

            if len(all_news) >= 8:
                break
    except Exception as e:
        pass

if not all_news:
    # Если нет свежих — берём просто последние без фильтра по дате
    for source, url in FEEDS[:2]:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")[:150]
                all_news.append((source, title, summary))
        except:
            pass

msg = "Медицинские новости:\n\n"
for source, title, summary in all_news[:6]:
    msg += "[" + source + "] " + title + "\n"
    if summary:
        msg += summary[:100] + "...\n"
    msg += "\n"

send_telegram(msg)
