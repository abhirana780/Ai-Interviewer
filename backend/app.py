import os

# Load environment variables if not already loaded
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
except ImportError:
    pass

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import uuid
import time
from datetime import timedelta

from interviewer import Interviewer
from model.stt import WhisperSTT
from database.db_helper import init_db, save_transcript, get_transcript, save_answer, get_session
from database.auth_helper import (
    init_auth_db, create_user, get_user_by_email, 
    get_user_by_id, verify_password, link_session_to_user
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "model", "models"))
DB_PATH = os.path.join(BASE_DIR, "database", "interviews.db")
AUTH_DB_PATH = os.path.join(BASE_DIR, "database", "auth.db")
# Use single variable for frontend directory
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

# JWT Configuration - REQUIRED in production
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required")

# Hugging Face API Key Configuration - REQUIRED
HF_API_KEY = os.getenv("HF_API_KEY")
if not HF_API_KEY:
    raise ValueError("HF_API_KEY environment variable is required")

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB default

# SECURITY: Use specific origins, not wildcard
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)
jwt = JWTManager(app)

# Ensure DBs exist
init_db(DB_PATH)
init_auth_db(AUTH_DB_PATH)

# Create the interviewer engine
interviewer = Interviewer(model_dir=MODEL_DIR, db_path=DB_PATH)
stt_engine = WhisperSTT()

def synthesize_tts(text, session_id):
    if not text:
        return None
    try:
        media_dir = os.path.join(FRONTEND_DIR, "media", "tts", session_id)
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

# Authentication routes
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Name, email, and password are required"}), 400
    
    # Check if user already exists
    existing_user = get_user_by_email(AUTH_DB_PATH, data['email'])
    if existing_user:
        return jsonify({"message": "User with this email already exists"}), 409
    
    # Create user
    user = create_user(AUTH_DB_PATH, data['name'], data['email'], data['password'])
    if not user:
        return jsonify({"message": "Failed to create user"}), 500
    
    # Generate JWT token
    access_token = create_access_token(identity=user['id'])
    
    return jsonify({
        "token": access_token,
        "user": {
            "id": user['id'],
            "name": user['name'],
            "email": user['email']
        }
    }), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400
    
    # Get user
    user = get_user_by_email(AUTH_DB_PATH, data['email'])
    if not user:
        return jsonify({"message": "Invalid email or password"}), 401
    
    # Verify password
    if not verify_password(data['password'], user['password_hash']):
        return jsonify({"message": "Invalid email or password"}), 401
    
    # Generate JWT token
    access_token = create_access_token(identity=user['id'])
    
    return jsonify({
        "token": access_token,
        "user": {
            "id": user['id'],
            "name": user['name'],
            "email": user['email']
        }
    }), 200

@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = get_user_by_id(AUTH_DB_PATH, user_id)
    
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    return jsonify({
        "user": {
            "id": user['id'],
            "name": user['name'],
            "email": user['email']
        }
    }), 200

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
    media_dir = os.path.join(FRONTEND_DIR, "media", session_id)
    os.makedirs(media_dir, exist_ok=True)

    first_question = interviewer.start_session(session_id=session_id, role=track, candidate_name=candidate_name)

    bot_video_path = os.path.join(FRONTEND_DIR, "media", "bot.mp4")
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


    # Handle file upload if any
    file = None
    try:
        file = request.files.get("media")
    except Exception:
        file = None
        
    if file:
        sid = session_id or (request.form.get("session_id") if request.form else None)
        if sid:
            # We no longer save video permanently to save space
            # Instead, save to temp file -> transcribe -> delete
            import tempfile
            
            # Determine extension
            ext = ".webm"
            if file.filename and "." in file.filename:
                ext = "." + file.filename.rsplit(".", 1)[1]
                
            fd, temp_path = tempfile.mkstemp(suffix=ext)
            os.close(fd)
            
            try:
                file.save(temp_path)
                
                # Transcribe using improved STT
                if stt_engine:
                    transcribed = stt_engine.transcribe_file(temp_path)
                    if transcribed and transcribed.strip():
                        answer_text = transcribed.strip()
            except Exception as e:
                print(f"Processing error: {e}")
            finally:
                # Always clean up temp file to save space
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
            
            # Do NOT save audio/video path to DB
            saved_media_path = None

    # Fallback to JSON body if session_id still missing
    if not session_id:
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")
        answer_text = data.get("answer") or data.get("answer_text") or answer_text

    # Skip old STT logic as we handled it above
    
    if not session_id:
        return jsonify({"error": "session_id missing"}), 400



    resp = interviewer.handle_answer(session_id, answer_text)

    # Include media info and bot assets in response
    resp = dict(resp or {})
    resp["media_path"] = saved_media_path
    bot_video_path = os.path.join(FRONTEND_DIR, "media", "bot.mp4")
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

