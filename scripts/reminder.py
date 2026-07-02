#!/usr/bin/env python3
# Запускается каждые 15 минут — отправляет напоминание за 30 минут до события
import json, urllib.request, datetime

BOT_TOKEN = "8618486662:AAFg6kEECi5U3su0lt6FvL60noj_8j2bCzM"
CHAT_ID = "652009128"
CREDS = "/root/claude-agent/google/token.json"
SENT_FILE = "/root/claude-agent/scripts/sent_reminders.json"

def send_telegram(text):
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

def get_token():
    with open(CREDS) as f:
        return json.load(f)["access_token"]

def load_sent():
    try:
        with open(SENT_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

token = get_token()
now_utc = datetime.datetime.utcnow()
window_start = now_utc + datetime.timedelta(minutes=25)
window_end = now_utc + datetime.timedelta(minutes=35)

url = ("https://www.googleapis.com/calendar/v3/calendars/primary/events"
       "?timeMin=" + window_start.isoformat() + "Z"
       + "&timeMax=" + window_end.isoformat() + "Z"
       + "&singleEvents=true&orderBy=startTime")
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
events = json.loads(urllib.request.urlopen(req).read()).get("items", [])

sent = load_sent()
for e in events:
    eid = e.get("id", "")
    if eid in sent:
        continue
    start = e.get("start", {}).get("dateTime", "")
    if start:
        t = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
        hour = (t.hour + 7) % 24
        time_str = str(hour).zfill(2) + ":" + str(t.minute).zfill(2)
    else:
        time_str = "весь день"
    summary = e.get("summary", "?")
    send_telegram("Напоминание: через 30 минут - " + summary + " в " + time_str)
    sent[eid] = now_utc.isoformat()

# Чистим старые записи (старше 1 дня)
cutoff = (now_utc - datetime.timedelta(days=1)).isoformat()
sent = {k: v for k, v in sent.items() if v > cutoff}
save_sent(sent)
