# 🧺 WhatsApp Laundry Bot  

**Do you forget your laundry in the washer and get those passive-aggressive nudges from your flatmates?**  
Yeah… we’ve been there too.  

Now there’s a fix. Meet **Laundry Bot** — a simple WhatsApp assistant that reminds you when your cycle’s done, keeps track of who’s using the machines, and keeps the peace in shared living spaces.  

No new app. No sign-ups. Just WhatsApp.  

---

## ✨ What It Does

Laundry Bot helps roommates, dorm residents, and co-living spaces **coordinate laundry time effortlessly**.  
It tracks when machines are in use, reminds people to remove clothes, and shows availability — all via WhatsApp messages.  

---

## 🧩 Example Commands

| Command | What it does |
|----------|--------------|
| `Washer start 45m` | Start a 45-minute wash cycle |
| `Dryer start 1h` | Start a 1-hour drying cycle |
| `Laundry status` | Check who’s using what |
| `Washer removed` | Mark the washer as free |
| `Dryer removed` | Mark the dryer as free |

---

## 💡 Features

✅ Automatic reminders when your laundry finishes  
✅ Prevents overlapping usage (1 washer, 1 dryer = no confusion)  
✅ “Laundry status” command to see live machine availability  
✅ Friendly WhatsApp interface — no app downloads or logins  
✅ Built with **Python + Flask + Twilio WhatsApp API**

---

## ⚙️ How It Works

1. Users send simple WhatsApp commands (like “washer start 45m”).  
2. The bot tracks who’s using which machine and when it’ll be done.  
3. When the timer ends, the bot sends a reminder.  
4. Once laundry is removed, others get notified that the machine’s free.  

Everything runs on a lightweight **Flask server**, using a background thread to check task timers.

---

## 🚀 Getting Started

```bash
git clone https://github.com/yourusername/laundry-bot.git
cd laundry-bot
pip install flask twilio
python app.py
```
---
Expose your local server

Use ngrok to make your local Flask server accessible to Twilio:
```bash
ngrok http 5000
```

Copy the generated URL and paste it into your Twilio WhatsApp Sandbox webhook settings — and you’re good to go 🚀

---
## 🧠 Tech Stack
- Python (Flask) — lightweight backend server
- Twilio WhatsApp API — message delivery and responses
- Threading — background reminders for cycle completion

---
## ❤️ Why It Exists

Because forgotten laundry shouldn’t ruin friendships.
Laundry Bot makes shared living a little smoother — one reminder at a time.
