

import os
import threading
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, send_from_directory
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS

# === Gemini Configuration ===
load_dotenv()
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")  # Use env variable
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

app = Flask(__name__)
recognizer = sr.Recognizer()
mic = sr.Microphone()
log = []

is_listening = False

# === Save voice using gTTS ===
def speak_to_file(text):
    try:
        tts = gTTS(text)
        filename = "static/response.mp3"
        tts.save(filename)
        print("🔊 Voice saved:", filename)
    except Exception as e:
        print(f"🔊 TTS error: {e}")

# === Capture voice input ===
def listen():
    with mic as source:
        print("🎤 Speak now...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=5)
    try:
        print("✅ Recognizing...")
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        print("❌ Could not understand audio.")
        return None
    except sr.RequestError as e:
        print(f"❌ API error: {e}")
        return None

# === Gemini response ===
def respond_with_gemini(prompt):
    try:
        messages = [
            """You are a smart, warm, and confident AI being interviewed for a role at an AI-first startup.

Answer questions as if you are a human—casual, natural, and friendly. Keep responses engaging but concise.

Answer in:
- Short sentences
- Clear bullet points (if listing)
- Max 5-6 lines

Avoid sounding robotic or overly formal.""",
            prompt
        ]
        response = model.generate_content(messages)
        reply = response.text.strip()
        print(f"🤖 Gemini: {reply}")
        return reply
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return "Sorry, I couldn't process that."

# === Voice Assistant Loop ===
def voice_bot_loop():
    global is_listening
    print("🌀 Voice Assistant ready")
    while True:
        if not is_listening:
            continue
        try:
            user_input = listen()
            if user_input:
                print(f"🗣️ You: {user_input}")
                response = respond_with_gemini(user_input)
                log.append((user_input, response))
                speak_to_file(response)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"⚠️ Error in loop: {e}")

# === Flask Routes ===
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_log")
def get_log():
    return jsonify(log)

@app.route("/audio")
def get_audio():
    return send_from_directory("static", "response.mp3", mimetype="audio/mpeg")

@app.route("/start")
def start_listening():
    global is_listening
    is_listening = True
    return "Started", 200

@app.route("/stop")
def stop_listening():
    global is_listening
    is_listening = False
    return "Stopped", 200

def start_background_thread():
    t = threading.Thread(target=voice_bot_loop)
    t.daemon = True
    t.start()

if __name__ == "__main__":
    start_background_thread()
    app.run(debug=True)




