#!/usr/bin/env python3
import json, urllib.request, urllib.parse, datetime

BOT_TOKEN = "8618486662:AAFg6kEECi5U3su0lt6FvL60noj_8j2bCzM"
CHAT_ID = "652009128"
CREDS = "/root/claude-agent/google/token.json"
LABS_STATE = "/root/.claude/projects/-root-claude-agent/labs/state.json"

def send_telegram(text):
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

def refresh_google_token():
    with open(CREDS) as f:
        creds = json.load(f)
    data = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    resp = json.loads(urllib.request.urlopen(req).read())
    creds["access_token"] = resp["access_token"]
    with open(CREDS, "w") as f:
        json.dump(creds, f)
    return resp["access_token"]

def get_today_events(token):
    now = datetime.datetime.utcnow()
    today_start = datetime.datetime(now.year, now.month, now.day).isoformat() + "Z"
    today_end = (datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)).isoformat() + "Z"
    url = ("https://www.googleapis.com/calendar/v3/calendars/primary/events"
           "?timeMin=" + today_start + "&timeMax=" + today_end +
           "&singleEvents=true&orderBy=startTime")
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    return json.loads(urllib.request.urlopen(req).read()).get("items", [])

def check_labs_updates():
    try:
        with open(LABS_STATE) as f:
            state = json.load(f)
        token = state.get("access_token", "")
        last = state.get("last_checked", datetime.datetime.utcnow().isoformat() + "Z")
        url = "https://labs.mariafonina.ru/api/agent/updates?since=" + last
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
        resp = json.loads(urllib.request.urlopen(req).read())
        announcements = resp.get("announcements", [])
        state["last_checked"] = resp.get("generated_at", datetime.datetime.utcnow().isoformat())
        with open(LABS_STATE, "w") as f:
            json.dump(state, f, indent=2)
        return announcements
    except Exception as e:
        return []

# Получаем токен и события
token = refresh_google_token()
events = get_today_events(token)

# Время по Барнаулу (UTC+7)
now_barnaul = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
date_str = now_barnaul.strftime("%d.%m.%Y")

msg = "Доброе утро! Расписание на " + date_str + ":\n\n"

if not events:
    msg += "Событий нет - свободный день!\n"
else:
    for e in events:
        start = e.get("start", {})
        dt = start.get("dateTime", "")
        if dt:
            t = datetime.datetime.fromisoformat(dt.replace("Z", "+00:00"))
            barnaul = datetime.timezone(datetime.timedelta(hours=7))
            t_local = t.astimezone(barnaul)
            time_str = t_local.strftime("%H:%M")
        else:
            time_str = "весь день"
        msg += time_str + " - " + e.get("summary", "?") + "\n"

# Проверяем ЛАБС
announcements = check_labs_updates()
if announcements:
    msg += "\nНовости ЛАБС:\n"
    for a in announcements[:3]:
        title = a.get("title", "")
        body = (a.get("body", "") or "")[:100]
        msg += "- " + title + ": " + body + "\n"

send_telegram(msg)
