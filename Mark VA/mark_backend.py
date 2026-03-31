"""
MARK Voice Assistant - Flask Backend
Run: pip install flask flask-cors pyttsx3 speechrecognition wikipedia pyjokes GoogleNews requests pyautogui
Then: python mark_backend.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import threading
import os
import webbrowser
import wikipedia
import pyjokes
import time

# ── optional heavy imports (graceful fallback) ──────────────────────────────
try:
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1)
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except Exception:
    SR_AVAILABLE = False

try:
    import pyautogui
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False

try:
    from gnews import GNews
    NEWS_AVAILABLE = True
except Exception:
    NEWS_AVAILABLE = False

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# In-memory log
command_log = []

def add_log(cmd, response, status="success"):
    command_log.insert(0, {
        "command": cmd,
        "response": response,
        "status": status,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    })
    if len(command_log) > 50:
        command_log.pop()

def speak_async(text):
    if TTS_AVAILABLE:
        def _speak():
            engine.say(text)
            engine.runAndWait()
        threading.Thread(target=_speak, daemon=True).start()

def load_name():
    try:
        with open("assistant_name.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "MARK"

# ────────────────────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────────────────────

@app.route("/api/status", methods=["GET"])
def status():
    now = datetime.datetime.now()
    hour = now.hour
    if 4 <= hour < 12:
        greeting = "Good Morning"
    elif 12 <= hour < 16:
        greeting = "Good Afternoon"
    elif 16 <= hour < 24:
        greeting = "Good Evening"
    else:
        greeting = "Good Night"
    return jsonify({
        "name": load_name(),
        "time": now.strftime("%I:%M:%S %p"),
        "date": now.strftime("%d %B %Y"),
        "greeting": greeting,
        "tts": TTS_AVAILABLE,
        "stt": SR_AVAILABLE,
    })

@app.route("/api/command", methods=["POST"])
def handle_command():
    data = request.json or {}
    query = data.get("query", "").lower().strip()

    if not query:
        return jsonify({"response": "No command received.", "status": "error"}), 400

    response = process_command(query)
    add_log(query, response["response"], response.get("status", "success"))
    if TTS_AVAILABLE:
        speak_async(response["response"])
    return jsonify(response)

@app.route("/api/listen", methods=["POST"])
def listen():
    if not SR_AVAILABLE:
        return jsonify({"response": "Speech recognition not available.", "status": "error"}), 503
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.pause_threshold = 1
            audio = r.listen(source, timeout=5)
        query = r.recognize_google(audio, language="en-in")
        return jsonify({"query": query.lower(), "status": "success"})
    except sr.WaitTimeoutError:
        return jsonify({"response": "Timeout. Please try again.", "status": "error"}), 408
    except sr.UnknownValueError:
        return jsonify({"response": "Could not understand audio.", "status": "error"}), 422
    except Exception as e:
        return jsonify({"response": str(e), "status": "error"}), 500

@app.route("/api/name", methods=["POST"])
def set_name():
    data = request.json or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"response": "Name cannot be empty.", "status": "error"}), 400
    with open("assistant_name.txt", "w") as f:
        f.write(name)
    msg = f"Assistant renamed to {name}."
    speak_async(msg)
    add_log("set name", msg)
    return jsonify({"response": msg, "status": "success"})

@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(command_log)

@app.route("/api/joke", methods=["GET"])
def get_joke():
    joke = pyjokes.get_joke(language='en', category='all')
    speak_async(joke)
    add_log("tell me a joke", joke)
    return jsonify({"response": joke, "status": "success"})

@app.route("/api/news", methods=["GET"])
def get_news():
    if not NEWS_AVAILABLE:
        return jsonify({"response": "News module not available.", "headlines": [], "status": "error"}), 503
    try:
        gn = GNews(language='en')
        results = gn.get_news('India')[:5]
        headlines = [r.get('title', '') for r in results]
        speak_async("Here are the latest headlines. " + ". ".join(headlines))
        add_log("news", f"Fetched {len(headlines)} headlines")
        return jsonify({"headlines": headlines, "status": "success"})
    except Exception as e:
        return jsonify({"response": str(e), "headlines": [], "status": "error"}), 500

@app.route("/api/note", methods=["POST"])
def save_note():
    data = request.json or {}
    content = data.get("note", "").strip()
    if not content:
        return jsonify({"response": "Note is empty.", "status": "error"}), 400
    with open("note.txt", "a") as f:
        f.write(content + "\n")
    msg = "Note saved."
    speak_async(msg)
    add_log("write note", msg)
    return jsonify({"response": msg, "status": "success"})

# ────────────────────────────────────────────────────────────────────────────
# Command processor (mirrors Mark.py logic)
# ────────────────────────────────────────────────────────────────────────────

def process_command(query):
    now = datetime.datetime.now()

    if 'time' in query:
        t = now.strftime("%I:%M:%S %p")
        return {"response": f"The current time is {t}", "action": "time"}

    if 'date' in query or 'today' in query:
        d = now.strftime("%d %B %Y")
        return {"response": f"Today is {d}", "action": "date"}

    if 'wikipedia' in query:
        topic = query.replace("wikipedia", "").strip()
        if not topic:
            return {"response": "Please specify a topic to search on Wikipedia.", "status": "error"}
        try:
            summary = wikipedia.summary(topic, sentences=2)
            return {"response": f"According to Wikipedia: {summary}", "action": "wikipedia"}
        except Exception as e:
            return {"response": f"Wikipedia error: {e}", "status": "error"}

    if 'open youtube' in query:
        webbrowser.open("https://www.youtube.com")
        return {"response": "Opening YouTube.", "action": "browser"}

    if 'open google' in query:
        webbrowser.open("https://www.google.com")
        return {"response": "Opening Google.", "action": "browser"}

    if 'open facebook' in query:
        webbrowser.open("https://www.facebook.com")
        return {"response": "Opening Facebook.", "action": "browser"}

    if 'open chrome' in query or 'open browser' in query:
        webbrowser.open("https://www.google.com")
        return {"response": "Opening browser.", "action": "browser"}

    if 'weather' in query:
        return {"response": "Opening weather for Bengaluru.", "action": "weather",
                "url": "https://www.accuweather.com/en/in/bengaluru/204108/weather-forecast/204108"}

    if 'news' in query:
        return {"response": "Fetching news. Use /api/news endpoint.", "action": "news"}

    if 'joke' in query:
        joke = pyjokes.get_joke()
        return {"response": joke, "action": "joke"}

    if 'hello' in query or 'hi' in query:
        return {"response": f"Hello sir! How can I assist you today?", "action": "greet"}

    if 'how are you' in query:
        return {"response": "I'm functioning perfectly, sir. Ready to assist!", "action": "greet"}

    if 'who are you' in query:
        return {"response": f"I am {load_name()}, your personal AI assistant.", "action": "greet"}

    if 'where is' in query:
        place = query.replace("where is", "").strip()
        url = f"https://www.google.com/maps/place/{place}"
        webbrowser.open(url)
        return {"response": f"Opening map for {place}.", "action": "maps", "url": url}

    if 'minimize' in query or 'minimise' in query:
        if GUI_AVAILABLE:
            pyautogui.hotkey('win', 'd')
        return {"response": "Minimizing all windows.", "action": "system"}

    if 'close' in query:
        if GUI_AVAILABLE:
            pyautogui.hotkey('alt', 'f4')
        return {"response": "Closing active window.", "action": "system"}

    if 'shutdown' in query or 'sleep my' in query:
        os.system("shutdown /h")
        return {"response": "Shutting down the system.", "action": "system"}

    if 'restart' in query:
        os.system('shutdown /r')
        return {"response": "Restarting the system.", "action": "system"}

    if 'calculator' in query:
        import subprocess
        try:
            subprocess.Popen("calc.exe")
        except Exception:
            pass
        return {"response": "Opening calculator.", "action": "system"}

    if 'note' in query:
        return {"response": "Use the Notes panel to save a note.", "action": "note"}

    if 'exit' in query or 'terminate' in query or 'goodbye' in query or 'bye' in query:
        return {"response": "Goodbye, sir! MARK is going offline. See you later.", "action": "exit"}

    if 'mark' in query:
        return {"response": f"I'm at your service, sir!", "action": "greet"}

    return {"response": f"I heard: \"{query}\". I'm not sure how to handle that yet.", "status": "unknown"}


if __name__ == "__main__":
    print("="*50)
    print("  MARK Voice Assistant Backend")
    print("  Running at http://localhost:5000")
    print("="*50)
    app.run(debug=True, port=5000)
