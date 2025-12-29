import os
import sys

# Load environment variables if not already loaded
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
except ImportError:
    pass

from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
import uuid
import time
# Email imports removed as per requirements

from interviewer import Interviewer
from model.stt import WhisperSTT
from database.db_helper import init_db, save_transcript, get_transcript, save_answer, get_session
# Unused utility imports removed as per requirements
from utils.answer_verifier import verify_transcript, verify_session
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "model", "models"))
DB_PATH = os.path.join(BASE_DIR, "database", "interviews.db")
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

# Email configuration removed as per requirements

# Hugging Face API Key Configuration
HF_API_KEY = os.getenv("HF_API_KEY", "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")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
CORS(app,origin="*")

# Ensure DB exists
init_db(DB_PATH)

# Create the interviewer engine
interviewer = Interviewer(model_dir=MODEL_DIR, db_path=DB_PATH)
stt_engine = WhisperSTT()

def synthesize_tts(text, session_id):
    if not text:
        return None
    try:
        media_dir = os.path.join(STATIC_DIR, "media", "tts", session_id)
        os.makedirs(media_dir, exist_ok=True)
        filename = f"tts_{int(time.time())}.wav"
        full_path = os.path.join(media_dir, filename)
        import pyttsx3
        engine = pyttsx3.init()
        
        # Set voice to female if possible (based on user preference)
        voices = engine.getProperty('voices')
        for voice in voices:
            # Look for female voices
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
            elif 'woman' in voice.name.lower() or 'girl' in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        
        # Set reasonable speech rate
        engine.setProperty('rate', 130)
        engine.setProperty('rate', 130)
        
        engine.save_to_file(text, full_path)
        engine.runAndWait()
        return f"/media/tts/{session_id}/{filename}"
    except Exception as e:
        print(f"TTS Error: {e}")
        return None
    # Root and health endpoints
@app.route("/", methods=["GET"])
def index():
    return send_from_directory(FRONTEND_DIR, "interviewer.html")

@app.route("/interview", methods=["GET"])
def interview_page():
    return send_from_directory(FRONTEND_DIR, "interviewer.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"healthy","time": int(time.time())})

# Register route removed as per requirements

@app.route("/start", methods=["POST"])
def start():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    
    if not session_id:
        # Fallback: create new session if not provided
        track = data.get("track") or data.get("role") or "Software Engineer"
        candidate_name = data.get("candidate_name") or data.get("name") or ""
        session_id = str(uuid.uuid4())
    else:
        # Get existing session details
        session = get_session(DB_PATH, session_id)
        if session:
            track = session.get("track") or "Software Engineer"
            candidate_name = session.get("candidate_name") or ""
        else:
            track = data.get("track") or "Software Engineer"
            candidate_name = data.get("candidate_name") or ""

    # Ensure a media directory exists for this session
    media_dir = os.path.join(STATIC_DIR, "media", session_id)
    os.makedirs(media_dir, exist_ok=True)

    first_question = interviewer.start_session(session_id=session_id, role=track, candidate_name=candidate_name)

    bot_video_path = os.path.join(STATIC_DIR, "media", "bot.mp4")
    bot_video_url = "/media/bot.mp4" if os.path.exists(bot_video_path) else None
    bot_image_url = "/media/bot.svg"
    tts_url = synthesize_tts(first_question, session_id)

    return jsonify({
        "session_id": session_id,
        "question": first_question,
        "bot_video_url": bot_video_url,
        "bot_image_url": bot_image_url,
        "tts_url": tts_url
    })


@app.route("/answer", methods=["POST"])
def answer():
    session_id = None
    answer_text = ""
    saved_media_path = None

    # Prefer form fields if present
    if request.form:
        session_id = request.form.get("session_id") or session_id
        answer_text = request.form.get("answer") or request.form.get("answer_text") or answer_text


    # Handle file upload if any, regardless of content-type header quirks
    file = None
    try:
        file = request.files.get("media")
    except Exception:
        file = None
    if file:
        sid = session_id or (request.form.get("session_id") if request.form else None)
        if sid:
            media_dir = os.path.join(STATIC_DIR, "media", "answers", sid)
            os.makedirs(media_dir, exist_ok=True)
            filename = f"{int(time.time())}.webm"
            full_path = os.path.join(media_dir, filename)
            file.save(full_path)
            saved_media_path = f"/media/answers/{sid}/{filename}"
            session_id = sid

    # Fallback to JSON body if session_id still missing
    if not session_id:
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")
        answer_text = data.get("answer") or data.get("answer_text") or answer_text


    # If media exists and text is empty or placeholder, transcribe
    def _needs_stt(text):
        t = (text or "").strip().lower()
        return (t == "" or t == "[video_answer]")

    if saved_media_path and _needs_stt(answer_text):
        answer_text = "[video_answer]"
        full_path = None
        try:
            rel = saved_media_path.replace("/", "", 1)
            full_path = os.path.join(STATIC_DIR, rel.replace("/", os.sep))
        except Exception:
            full_path = None
        if full_path and stt_engine:
            t = stt_engine.transcribe_file(full_path)
            if t and t.strip():
                answer_text = t.strip()

    if not session_id:
        return jsonify({"error": "session_id missing"}), 400

    resp = interviewer.handle_answer(session_id, answer_text)

    # Include media info and bot assets in response
    resp = dict(resp or {})
    resp["media_path"] = saved_media_path
    bot_video_path = os.path.join(STATIC_DIR, "media", "bot.mp4")
    resp["bot_video_url"] = "/media/bot.mp4" if os.path.exists(bot_video_path) else None
    resp["bot_image_url"] = "/media/bot.svg"
    # Generate TTS for next question if available
    next_q = resp.get("next_question")
    resp["tts_url"] = synthesize_tts(next_q, session_id) if next_q else None

    # Persist this answer with media and scoring
    try:
        save_answer(DB_PATH, session_id, answer_text, saved_media_path, resp.get("score"), resp.get("feedback"))
    except Exception:
        pass

    return jsonify(resp)


@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json() or {}
    text = data.get("text") or ""
    session_id = data.get("session_id") or str(uuid.uuid4())
    url = synthesize_tts(text, session_id)
    return jsonify({"tts_url": url})

@app.route("/transcript/<session_id>", methods=["GET"])
def transcript(session_id):
    t = get_transcript(DB_PATH, session_id)
    return jsonify({"transcript": t or ""})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7860, debug=False, use_reloader=False)
#python backend/app.py

