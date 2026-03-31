# MARK Voice Assistant — Setup Guide

## Files
- `mark_backend.py`  → Flask API server (bridge between UI and your Python logic)
- `mark_ui.html`     → Frontend dashboard (open in any browser)
- `Mark.py`          → Your original assistant logic (unchanged)

---

## Step 1 — Install Dependencies

```bash
pip install flask flask-cors pyttsx3 SpeechRecognition wikipedia pyjokes GoogleNews requests pyautogui
```

**Windows extra for pyaudio (needed for microphone):**
```bash
pip install pipwin
pipwin install pyaudio
```

---

## Step 2 — Start the Backend

```bash
python mark_backend.py
```

You should see:
```
  MARK Voice Assistant Backend
  Running at http://localhost:5000
```

---

## Step 3 — Open the UI

Simply open `mark_ui.html` in your browser (double-click or drag into Chrome/Edge/Firefox).

The status chip in the top-right will turn **green** when the backend is reachable.

---

## Using the Interface

| Feature | How to use |
|---|---|
| **Text command** | Type in the input box, press Enter |
| **Voice command** | Click the 🎤 button, speak, it auto-sends |
| **Quick commands** | Click any pill button below the chat |
| **News** | Click 📰 News tab or "Fetch Latest News" |
| **Save a note** | Click Notes tab → type → Save Note |
| **Rename MARK** | Left sidebar → Rename → type name → Set |
| **Command logs** | Right panel → Logs tab |

---

## Supported Voice / Text Commands

| You say | MARK does |
|---|---|
| `what is the time` | Speaks current time |
| `what is the date` | Speaks today's date |
| `wikipedia [topic]` | Searches Wikipedia |
| `open youtube` | Opens YouTube |
| `open google` | Opens Google |
| `open facebook` | Opens Facebook |
| `weather` | Opens weather for your city |
| `news` | Fetches top 5 India headlines |
| `tell me a joke` | Tells a joke |
| `how are you` | Greets |
| `who are you` | Introduces itself |
| `where is [place]` | Opens Google Maps |
| `minimize the window` | Win+D hotkey |
| `close` | Alt+F4 |
| `open calculator` | Opens calc.exe |
| `write a note` | Use the Notes panel |
| `exit` / `goodbye` | Farewell message |

---

## API Endpoints (for developers)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/status` | Get name, time, date, greeting |
| POST | `/api/command` | Send `{ "query": "..." }` |
| POST | `/api/listen` | Trigger microphone (server-side) |
| GET | `/api/joke` | Get a random joke |
| GET | `/api/news` | Get top headlines |
| POST | `/api/note` | Save `{ "note": "..." }` |
| POST | `/api/name` | Rename `{ "name": "..." }` |
| GET | `/api/logs` | Get command history |

---

## Troubleshooting

**"OFFLINE" chip in UI**
→ Backend is not running. Run `python mark_backend.py` first.

**Microphone not working**
→ Install pyaudio: `pipwin install pyaudio` (Windows) or `brew install portaudio && pip install pyaudio` (Mac)

**pyttsx3 voice not working**
→ On Windows, make sure SAPI5 voices are installed. On Mac, use `say` engine.

**GoogleNews error**
→ Run `pip install GoogleNews --upgrade`
