
# import os
# import tempfile
# import whisper
# from flask import Flask, render_template, request, send_file, jsonify
# from gtts import gTTS
# import google.generativeai as genai

# app = Flask(__name__)
# model = whisper.load_model("base")  # load Whisper on startup

# # Configure Gemini
# genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
# llm = genai.GenerativeModel("gemini-1.5-flash")

# log = []

# @app.route("/")
# def home():
#     return render_template("index.html")

# @app.route("/transcribe", methods=["POST"])
# def transcribe():
#     if "audio" not in request.files:
#         return "No audio file", 400

#     file = request.files["audio"]
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
#         file.save(temp_audio.name)
#         result = model.transcribe(temp_audio.name)
#         user_input = result["text"]

#     # Gemini response
#     chat = llm.generate_content([
# """You are a smart, warm, and confident AI being interviewed for a role at an AI-first startup.

# # Answer questions as if you are a human—casual, natural, and friendly. Keep responses engaging but concise.

# # Answer in:
# # - Short sentences
# # - Clear bullet points (if listing)
# # - Max 5-6 lines

# # Avoid sounding robotic or overly formal.""",
#         user_input
#     ])
#     response = chat.text.strip()

#     # Save voice response
#     tts = gTTS(response)
#     tts.save("static/response.mp3")

#     log.append((user_input, response))
#     return jsonify({"question": user_input, "answer": response})

# @app.route("/get_log")
# def get_log():
#     return jsonify(log)

# @app.route("/audio")
# def get_audio():
#     return send_file("static/response.mp3", mimetype="audio/mpeg")

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)

import os
import tempfile
import wave
import json
from flask import Flask, render_template, request, send_file, jsonify
from vosk import Model, KaldiRecognizer
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai
from pydub import AudioSegment
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load Vosk model (offline speech recognition)
vosk_model = Model("vosk-model-small-en-us-0.15")

# Configure Gemini (Google Generative AI)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
llm = genai.GenerativeModel("gemini-1.5-flash")

# Log to keep Q&A
log = []

# Function: transcribe using Vosk
def transcribe_with_vosk(audio_path):
    wf = wave.open(audio_path, "rb")

    if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
        raise ValueError("Audio must be mono WAV with 16-bit sample width.")

    rec = KaldiRecognizer(vosk_model, wf.getframerate())
    result = ""

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result += json.loads(rec.Result())["text"] + " "

    result += json.loads(rec.FinalResult())["text"]
    return result.strip()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return "No audio file", 400

    file = request.files["audio"]

    try:
        # Convert any file to proper WAV format
        audio = AudioSegment.from_file(file)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)  # 16-bit mono
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            audio.export(temp_wav.name, format="wav")
            user_input = transcribe_with_vosk(temp_wav.name)
    except Exception as e:
        print("Transcription Error:", e)
        return jsonify({"error": str(e)}), 500


    # Gemini AI response
    prompt = """You are a smart, warm, and confident AI being interviewed for a role at an AI-first startup.
- Answer casually like a human.
- Use bullets if listing.
- Stay within 6 lines.
- Avoid sounding robotic."""

    try:
        chat = llm.generate_content([prompt, user_input])
        response = chat.text.strip()
        tts = gTTS(response)
        tts.save("static/response.mp3")
    except Exception as e:
        print("Gemini or TTS Error:", e)
        return jsonify({"error": str(e)}), 500

    log.append((user_input, response))
    return jsonify({"question": user_input, "answer": response})

@app.route("/get_log")
def get_log():
    return jsonify(log)

@app.route("/audio")
def get_audio():
    return send_file("static/response.mp3", mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
