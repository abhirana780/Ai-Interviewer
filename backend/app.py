from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
import uuid
import time
import os

from interviewer import Interviewer
from database.db_helper import init_db, save_transcript, get_transcript, save_answer, save_resume, save_ats_score, save_assessment, save_schedule, save_offer, save_course_enroll, save_lab_submission, get_latest_resume_text
from utils.ats_scoring import compute_ats_score
from utils.coding_judge import pick_problem, grade_code
from utils.scheduler import normalize_slot, is_valid_slot
from utils.offer_generator import generate_offer
from utils.lms import enroll_message
from utils.labs import pick_lab, grade_lab_code

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "model", "models"))
DB_PATH = os.path.join(BASE_DIR, "database", "interviews.db")
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "static"))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
CORS(app)

# Ensure DB exists
init_db(DB_PATH)

# Create the interviewer engine
interviewer = Interviewer(model_dir=MODEL_DIR, db_path=DB_PATH)

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
        engine.save_to_file(text, full_path)
        engine.runAndWait()
        return f"/static/media/tts/{session_id}/{filename}"
    except Exception:
        return None

    # Root and health endpoints
@app.route("/", methods=["GET"])
def index():
    return send_from_directory(FRONTEND_DIR, "interviewer.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"healthy","time": int(time.time())})

@app.route("/start", methods=["POST"])
def start():
    data = request.get_json() or {}
    track = data.get("track") or data.get("role") or "Software Engineer"
    session_id = str(uuid.uuid4())

    # Ensure a media directory exists for this session
    media_dir = os.path.join(STATIC_DIR, "media", session_id)
    os.makedirs(media_dir, exist_ok=True)

    first_question = interviewer.start_session(session_id=session_id, role=track)

    bot_video_path = os.path.join(STATIC_DIR, "media", "bot.mp4")
    bot_video_url = "/static/media/bot.mp4" if os.path.exists(bot_video_path) else None
    bot_image_url = url_for("static", filename="media/bot.svg")
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
            saved_media_path = f"/static/media/answers/{sid}/{filename}"
            session_id = sid

    # Fallback to JSON body if session_id still missing
    if not session_id:
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")
        answer_text = data.get("answer") or data.get("answer_text") or answer_text


    # If media exists but transcript empty, mark as video-only
    if (not answer_text or not answer_text.strip()) and saved_media_path:
        answer_text = "[video_answer]"

    if not session_id:
        return jsonify({"error": "session_id missing"}), 400

    resp = interviewer.handle_answer(session_id, answer_text)

    # Include media info and bot assets in response
    resp = dict(resp or {})
    resp["media_path"] = saved_media_path
    bot_video_path = os.path.join(STATIC_DIR, "media", "bot.mp4")
    resp["bot_video_url"] = "/static/media/bot.mp4" if os.path.exists(bot_video_path) else None
    resp["bot_image_url"] = url_for("static", filename="media/bot.svg")
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


@app.route("/funnel", methods=["GET"])
def funnel_page():
    return send_from_directory(FRONTEND_DIR, "funnel.html")

@app.route("/funnel/start", methods=["POST"]) 
def funnel_start():
    data = request.get_json(silent=True) or {}
    track = data.get("track") or "General"
    funnel_id = str(uuid.uuid4())
    return jsonify({"funnel_id": funnel_id, "track": track, "thresholds": {"ats": 60, "assessment": 70}})

@app.route("/resume/upload", methods=["POST"]) 
def resume_upload():
    funnel_id = request.form.get("funnel_id") if request.form else (request.json or {}).get("funnel_id")
    if not funnel_id:
        return jsonify({"error": "funnel_id missing"}), 400
    file = None
    try:
        file = request.files.get("resume")
    except Exception:
        file = None
    if not file:
        return jsonify({"error": "resume file missing"}), 400
    resumes_dir = os.path.join(STATIC_DIR, "media", "resumes", funnel_id)
    os.makedirs(resumes_dir, exist_ok=True)
    filename = file.filename or f"resume_{int(time.time())}.txt"
    full_path = os.path.join(resumes_dir, filename)
    file.save(full_path)

    parsed_text = ""
    parse_error = None
    try:
        ext = os.path.splitext(filename.lower())[1]
        if ext == ".pdf":
            try:
                from pdfminer.high_level import extract_text
                parsed_text = extract_text(full_path) or ""
            except Exception as e:
                parse_error = f"pdf_parse_error: {str(e)[:120]}"
        elif ext == ".docx":
            try:
                import docx
                doc = docx.Document(full_path)
                parsed_text = "\n".join([p.text for p in doc.paragraphs if p.text]) or ""
            except Exception as e:
                parse_error = f"docx_parse_error: {str(e)[:120]}"
        elif ext == ".txt":
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    parsed_text = f.read()
            except Exception as e:
                parse_error = f"txt_read_error: {str(e)[:120]}"
        else:
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    parsed_text = f.read()
            except Exception:
                parsed_text = ""
                parse_error = parse_error or "unsupported_format"
    except Exception as e:
        parse_error = f"parse_error: {str(e)[:120]}"

    try:
        save_resume(DB_PATH, funnel_id, filename, parsed_text)
    except Exception:
        pass

    resp = {
        "resume_url": f"/static/media/resumes/{funnel_id}/{filename}",
        "text_len": len(parsed_text),
        "parsed": bool((parsed_text or "").strip())
    }
    if parse_error:
        resp["error"] = parse_error
    return jsonify(resp)

@app.route("/ats/score", methods=["POST"]) 
def ats_score():
    data = request.get_json(silent=True) or {}
    funnel_id = data.get("funnel_id")
    track = data.get("track") or "General"
    text = data.get("text") or ""
    if not funnel_id:
        return jsonify({"error": "funnel_id missing"}), 400

    # Use provided text or fallback to latest stored resume
    if not text.strip():
        try:
            text = get_latest_resume_text(DB_PATH, funnel_id) or ""
        except Exception:
            text = text or ""

    score, details, breakdown = compute_ats_score(text, track=track)
    try:
        save_ats_score(DB_PATH, funnel_id, score, details)
    except Exception:
        pass
    return jsonify({"score": score, "details": details, "breakdown": breakdown, "pass": bool(score >= 60)})

@app.route("/assessment/start", methods=["POST"]) 
def assessment_start():
    data = request.get_json(silent=True) or {}
    funnel_id = data.get("funnel_id")
    track = data.get("track") or "General"
    if not funnel_id:
        return jsonify({"error": "funnel_id missing"}), 400
    problem = pick_problem(track=track)
    return jsonify({"problem_key": problem["key"], "prompt": problem["prompt"]})

@app.route("/assessment/submit", methods=["POST"]) 
def assessment_submit():
    form = request.form
    data = request.get_json(silent=True) or {}
    funnel_id = (form.get("funnel_id") if form else None) or data.get("funnel_id")
    problem_key = (form.get("problem_key") if form else None) or data.get("problem_key")
    code_text = (form.get("code") if form else None) or data.get("code") or ""
    if not funnel_id:
        return jsonify({"error": "funnel_id missing"}), 400
    if not problem_key:
        return jsonify({"error": "problem_key missing"}), 400
    score, feedback = grade_code(problem_key, code_text)
    assess_dir = os.path.join(STATIC_DIR, "media", "assessments", funnel_id)
    os.makedirs(assess_dir, exist_ok=True)
    code_filename = f"{problem_key}_{int(time.time())}.py"
    code_path = os.path.join(assess_dir, code_filename)
    try:
        with open(code_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(code_text)
    except Exception:
        pass
    try:
        save_assessment(DB_PATH, funnel_id, problem_key, code_path, score, feedback)
    except Exception:
        pass
    return jsonify({"score": score, "feedback": feedback, "pass": bool(score >= 70), "code_url": f"/static/media/assessments/{funnel_id}/{code_filename}"})

@app.route("/schedule/book", methods=["POST"]) 
def schedule_book():
    data = request.get_json(silent=True) or {}
    funnel_id = data.get("funnel_id")
    slot = normalize_slot(data.get("slot") or "")
    note = data.get("note") or ""
    if not funnel_id:
        return jsonify({"error": "funnel_id missing"}), 400
    if not is_valid_slot(slot):
        return jsonify({"error": "invalid slot"}), 400
    try:
        save_schedule(DB_PATH, funnel_id, slot, note)
    except Exception:
        pass
    return jsonify({"status": "scheduled", "slot": slot})

@app.route("/offer/generate", methods=["POST"]) 
def offer_generate():
    data = request.get_json(silent=True) or {}
    funnel_id = data.get("funnel_id")
    title = data.get("title") or "Offer"
    candidate_name = data.get("name") or None
    if not funnel_id:
        return jsonify({"error": "funnel_id missing"}), 400
    body = generate_offer(title, candidate_name)
    try:
        save_offer(DB_PATH, funnel_id, title, body)
    except Exception:
        pass
    return jsonify({"title": title, "body": body})

@app.route("/lms/enroll", methods=["POST"]) 
def lms_enroll():
    data = request.get_json(silent=True) or {}
    funnel_id = data.get("funnel_id")
    course_name = data.get("course_name") or "Onboarding"
    if not funnel_id:
        return jsonify({"error": "funnel_id missing"}), 400
    try:
        save_course_enroll(DB_PATH, funnel_id, course_name)
    except Exception:
        pass
    return jsonify({"status": "enrolled", "course_name": course_name, "message": enroll_message(course_name)})

@app.route("/lab/start", methods=["POST"]) 
def lab_start():
    data = request.get_json(silent=True) or {}
    funnel_id = data.get("funnel_id")
    if not funnel_id:
        return jsonify({"error": "funnel_id missing"}), 400
    lab = pick_lab()
    return jsonify({"lab_key": lab["key"], "prompt": lab["prompt"]})

@app.route("/lab/submit", methods=["POST"]) 
def lab_submit():
    form = request.form
    data = request.get_json(silent=True) or {}
    funnel_id = (form.get("funnel_id") if form else None) or data.get("funnel_id")
    lab_key = (form.get("lab_key") if form else None) or data.get("lab_key")
    code_text = (form.get("code") if form else None) or data.get("code") or ""
    if not funnel_id:
        return jsonify({"error": "funnel_id missing"}), 400
    if not lab_key:
        return jsonify({"error": "lab_key missing"}), 400
    score, feedback = grade_lab_code(lab_key, code_text)
    lab_dir = os.path.join(STATIC_DIR, "media", "labs", funnel_id)
    os.makedirs(lab_dir, exist_ok=True)
    code_filename = f"{lab_key}_{int(time.time())}.py"
    code_path = os.path.join(lab_dir, code_filename)
    try:
        with open(code_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(code_text)
    except Exception:
        pass
    try:
        save_lab_submission(DB_PATH, funnel_id, lab_key, code_path, score, feedback)
    except Exception:
        pass
    return jsonify({"score": score, "feedback": feedback, "pass": bool(score >= 70), "code_url": f"/static/media/labs/{funnel_id}/{code_filename}"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7860, debug=False, use_reloader=False)
#d:\wipronix\venv\Scripts\python.exe app.py
#d:\wipronix\venv\Scripts\python.exe d:\wipronix\backend\app.py
#d:\wipronix\venv\Scripts\python.exe d:\wipronix\backend\app.py
#.\venv\Scripts\activate; python run.py