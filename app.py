
import os
import tempfile
import whisper
from flask import Flask, render_template, request, send_file, jsonify
from gtts import gTTS
import google.generativeai as genai

app = Flask(__name__)
model = whisper.load_model("base")  # load Whisper on startup

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
llm = genai.GenerativeModel("gemini-1.5-flash")

log = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return "No audio file", 400

    file = request.files["audio"]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        file.save(temp_audio.name)
        result = model.transcribe(temp_audio.name)
        user_input = result["text"]

    # Gemini response
    chat = llm.generate_content([
"""You are a smart, warm, and confident AI being interviewed for a role at an AI-first startup.

# Answer questions as if you are a human—casual, natural, and friendly. Keep responses engaging but concise.

# Answer in:
# - Short sentences
# - Clear bullet points (if listing)
# - Max 5-6 lines

# Avoid sounding robotic or overly formal.""",
        user_input
    ])
    response = chat.text.strip()

    # Save voice response
    tts = gTTS(response)
    tts.save("static/response.mp3")

    log.append((user_input, response))
    return jsonify({"question": user_input, "answer": response})

@app.route("/get_log")
def get_log():
    return jsonify(log)

@app.route("/audio")
def get_audio():
    return send_file("static/response.mp3", mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(debug=True)

