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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from interviewer import Interviewer
from model.stt import WhisperSTT
from database.db_helper import init_db, save_transcript, get_transcript, save_answer, save_resume, save_ats_score, save_assessment, save_schedule, save_offer, save_course_enroll, save_lab_submission, get_latest_resume_text, list_sessions, get_answers_for_session, update_answer_text_by_media, get_session
from utils.ats_scoring import compute_ats_score
from utils.coding_judge import pick_problem, grade_code
from utils.scheduler import normalize_slot, is_valid_slot
from utils.offer_generator import generate_offer
from utils.lms import enroll_message
from utils.labs import pick_lab, grade_lab_code
from utils.answer_verifier import verify_transcript, verify_session
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "model", "models"))
DB_PATH = os.path.join(BASE_DIR, "database", "interviews.db")
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "static"))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

# Email Configuration (Update these with your email credentials)
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")  # For Gmail
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))  # TLS port
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")  # Your email
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Your app password
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "AI Interview System")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
CORS(app)

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
        return f"/static/media/tts/{session_id}/{filename}"
    except Exception as e:
        print(f"TTS Error: {e}")
        return None
    # Root and health endpoints
@app.route("/", methods=["GET"])
def index():
    return send_from_directory(FRONTEND_DIR, "register.html")

@app.route("/interview", methods=["GET"])
def interview_page():
    return send_from_directory(FRONTEND_DIR, "interviewer.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"healthy","time": int(time.time())})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    session_id = str(uuid.uuid4())
    
    # Save user details to database
    save_transcript(
        DB_PATH, 
        session_id, 
        "",  # Empty transcript initially
        candidate_name=data.get("candidate_name", ""),
        mobile_number=data.get("mobile_number", ""),
        email=data.get("email", ""),
        qualification=data.get("qualification", ""),
        college_name=data.get("college_name", ""),
        track=data.get("track", "Software Engineer")
    )
    
    return jsonify({"session_id": session_id, "message": "Registration successful"})

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


    # If media exists and text is empty or placeholder, transcribe
    def _needs_stt(text):
        t = (text or "").strip().lower()
        return (t == "" or t == "[video_answer]")

    if saved_media_path and _needs_stt(answer_text):
        answer_text = "[video_answer]"
        full_path = None
        try:
            rel = saved_media_path.replace("/static/", "")
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

@app.route("/admin", methods=["GET"])
def admin_page():
    return send_from_directory(FRONTEND_DIR, "admin.html")

@app.route("/admin/sessions", methods=["GET"]) 
def admin_sessions():
    rows = list_sessions(DB_PATH)
    data = []
    for r in rows:
        sid = r["id"]
        answers = get_answers_for_session(DB_PATH, sid)
        t = get_transcript(DB_PATH, sid) or ""
        v = verify_session(t, answers)
        
        # Calculate average score from answers
        scores = [a["score"] for a in answers if a["score"] is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        
        data.append({
            "id": sid,
            "candidate_name": r.get("candidate_name", ""),
            "mobile_number": r.get("mobile_number", ""),
            "email": r.get("email", ""),
            "qualification": r.get("qualification", ""),
            "college_name": r.get("college_name", ""),
            "track": r.get("track", ""),
            "created_at": r["created_at"],
            "answers": len(answers),
            "overall": v.get("overall", 0.0),
            "avg_score": avg_score,
            "final_score": r.get("final_score") or avg_score
        })
    data.sort(key=lambda x: (x["final_score"], x["overall"], x["answers"]), reverse=True)
    return jsonify({"sessions": data})

@app.route("/admin/session/<session_id>", methods=["GET"]) 
def admin_session_detail(session_id):
    session = get_session(DB_PATH, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    t = session.get("transcript", "")
    candidate_name = session.get("candidate_name", "")
    mobile_number = session.get("mobile_number", "")
    email = session.get("email", "")
    qualification = session.get("qualification", "")
    college_name = session.get("college_name", "")
    track = session.get("track", "")
    created_at = session.get("created_at", 0)
    final_score = session.get("final_score")
    
    answers = get_answers_for_session(DB_PATH, session_id)
    verification = verify_session(t, answers)
    
    return jsonify({
        "session_id": session_id, 
        "candidate_name": candidate_name,
        "mobile_number": mobile_number,
        "email": email,
        "qualification": qualification,
        "college_name": college_name,
        "track": track,
        "created_at": created_at,
        "final_score": final_score,
        "transcript": t, 
        "answers": answers, 
        "verification": verification
    })

@app.route("/admin/rank", methods=["GET"]) 
def admin_rank():
    rows = list_sessions(DB_PATH)
    ranked = []
    for r in rows:
        sid = r["id"]
        t = get_transcript(DB_PATH, sid) or ""
        answers = get_answers_for_session(DB_PATH, sid)
        v = verify_session(t, answers)
        ranked.append({
            "id": sid,
            "created_at": r["created_at"],
            "answers": len(answers),
            "overall": v.get("overall", 0.0)
        })
    ranked.sort(key=lambda x: (x["overall"], x["answers"]), reverse=True)
    return jsonify({"rank": ranked})

@app.route("/admin/send-email", methods=["POST"])
def send_interview_email():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    
    if not session_id:
        return jsonify({"error": "session_id missing"}), 400
    
    # Get session data
    session = get_session(DB_PATH, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    candidate_name = session.get("candidate_name", "Candidate")
    email = session.get("email")
    mobile = session.get("mobile_number", "N/A")
    qualification = session.get("qualification", "N/A")
    college = session.get("college_name", "N/A")
    track = session.get("track", "N/A")
    created_at = session.get("created_at", 0)
    
    if not email:
        return jsonify({"error": "No email address for this candidate"}), 400
    
    # Get answers and calculate scores
    answers = get_answers_for_session(DB_PATH, session_id)
    transcript = session.get("transcript", "")
    verification = verify_session(transcript, answers)
    
    scores = [a["score"] for a in answers if a["score"] is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    final_score = session.get("final_score") or avg_score
    ai_score = int(verification.get("overall", 0))
    
    # Format date
    from datetime import datetime
    interview_date = datetime.fromtimestamp(created_at).strftime("%B %d, %Y at %I:%M %p") if created_at else "N/A"
    
    # Create HTML email template
    email_html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .score-card {{ background: white; border-left: 4px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .score-big {{ font-size: 48px; font-weight: bold; color: #667eea; margin: 10px 0; }}
        .score-label {{ color: #666; font-size: 14px; margin-bottom: 5px; }}
        .info-table {{ width: 100%; margin: 20px 0; }}
        .info-table td {{ padding: 8px; border-bottom: 1px solid #e0e0e0; }}
        .info-table td:first-child {{ font-weight: bold; color: #555; width: 40%; }}
        .performance-badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 14px; margin: 10px 5px; }}
        .badge-good {{ background: #e6f4ea; color: #1e8e3e; }}
        .badge-avg {{ background: #fff4e5; color: #b26a00; }}
        .badge-bad {{ background: #fdecea; color: #b00020; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #e0e0e0; color: #666; font-size: 12px; }}
        .qa-section {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #e0e0e0; }}
        .question {{ font-weight: bold; color: #444; margin-bottom: 8px; }}
        .answer {{ color: #666; margin-bottom: 8px; }}
        .feedback {{ background: #f0f9ff; padding: 10px; border-left: 3px solid #0b5ed7; border-radius: 4px; font-size: 13px; color: #495057; margin-top: 8px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎓Wipronix Interview Results</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">AI-Powered Wipronix Technologies Interview Assessment</p>
    </div>
    
    <div class="content">
        <h2 style="color: #333; margin-top: 0;">Dear {candidate_name},</h2>
        <p>Thank you for completing the AI interview for <strong>{track}</strong> position. We're pleased to share your interview results with you.</p>
        
        <div class="score-card">
            <div class="score-label">Overall Performance Score</div>
            <div class="score-big">{final_score}/5</div>
            <div>
                <span class="performance-badge {'badge-good' if final_score >= 4 else 'badge-avg' if final_score >= 3 else 'badge-bad'}">Average Score: {int((final_score/5)*100)}%</span>
                <span class="performance-badge {'badge-good' if ai_score >= 75 else 'badge-avg' if ai_score >= 50 else 'badge-bad'}">AI Analysis: {ai_score}%</span>
            </div>
        </div>
        
        <h3 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 8px;">Candidate Information</h3>
        <table class="info-table">
            <tr><td>Name</td><td>{candidate_name}</td></tr>
            <tr><td>Email</td><td>{email}</td></tr>
            <tr><td>Mobile</td><td>{mobile}</td></tr>
            <tr><td>Qualification</td><td>{qualification}</td></tr>
            <tr><td>College/University</td><td>{college}</td></tr>
            <tr><td>Interview Track</td><td>{track}</td></tr>
            <tr><td>Interview Date</td><td>{interview_date}</td></tr>
        </table>
        
        <h3 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 8px; margin-top: 30px;">Question-by-Question Performance</h3>
"""    
    # Add Q&A details
    pairs = verification.get("pairs", [])
    for i, pair in enumerate(pairs, 1):
        ans = answers[i-1] if i-1 < len(answers) else {}
        score_val = ans.get("score", 0)
        feedback_val = ans.get("feedback", "")
        
        email_html += f"""        <div class="qa-section">
            <div class="question">Q{i}: {pair.get("question", "N/A")}</div>
            <div class="answer">A{i}: {pair.get("answer", "N/A")}</div>
            <div style="margin-top: 8px;">
                <span class="performance-badge {'badge-good' if score_val >= 4 else 'badge-avg' if score_val >= 3 else 'badge-bad'}">Score: {score_val}/5</span>
                <span class="performance-badge {'badge-good' if pair.get('correctness', 0) >= 75 else 'badge-avg' if pair.get('correctness', 0) >= 50 else 'badge-bad'}">AI: {int(pair.get('correctness', 0))}%</span>
            </div>
            {f'<div class="feedback"><strong>Feedback:</strong> {feedback_val}</div>' if feedback_val else ''}
        </div>
"""
    
    email_html += """        
        <h3 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 8px; margin-top: 30px;">✨ Next Steps</h3>
        <p>Based on your performance, our team will review your results and get back to you within 3-5 business days regarding the next steps in the hiring process.</p>
        
        <p style="margin-top: 20px;">If you have any questions about your results, please don't hesitate to reach out to our recruitment team.</p>
        
        <p style="margin-top: 20px; font-weight: bold;">Best regards,<br>Wipronix Technologies</p>
    </div>
    
    <div class="footer">
        <p>© 2025 Wipronix Interview System. All rights reserved.</p>
        <p>This is an automated email. Please do not reply directly to this message.</p>
    </div>
</body>
</html>
"""
    
    # Try to send email if configured
    email_sent = False
    error_msg = None
    
    if EMAIL_ENABLED and SMTP_USERNAME and SMTP_PASSWORD:
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Your Interview Results - {track}"
            msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
            msg['To'] = email
            
            # Attach HTML content
            html_part = MIMEText(email_html, 'html')
            msg.attach(html_part)
            
            # Send email via SMTP
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            
            email_sent = True
            print(f"\n✅ Email sent successfully to {email}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Email send failed: {error_msg}")
    else:
        error_msg = "Email not configured. Set EMAIL_ENABLED=true and SMTP credentials in environment variables."
    
    # Log email for debugging
    print(f"\n{'='*60}")
    print(f"EMAIL TO: {email}")
    print(f"SUBJECT: Your Interview Results - {track}")
    print(f"EMAIL SENT: {email_sent}")
    if error_msg:
        print(f"ERROR: {error_msg}")
    print(f"{'='*60}\n")
    
    # Return response
    if email_sent:
        return jsonify({
            "success": True,
            "message": f"Email sent successfully to {email}!",
            "email_sent": True
        })
    else:
        return jsonify({
            "success": False,
            "message": error_msg or "Email service not configured",
            "email_sent": False,
            "preview": email_html[:200] + "...",
            "setup_instructions": {
                "step1": "Set environment variables: EMAIL_ENABLED=true",
                "step2": "SMTP_SERVER=smtp.gmail.com (or your email provider)",
                "step3": "SMTP_USERNAME=your-email@gmail.com",
                "step4": "SMTP_PASSWORD=your-app-password (not regular password)",
                "note": "For Gmail, create App Password at https://myaccount.google.com/apppasswords"
            }
        })


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

@app.route("/answers/transcribe", methods=["POST"])
def answers_transcribe():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id missing"}), 400
    base = os.path.join(STATIC_DIR, "media", "answers", session_id)
    if not os.path.isdir(base):
        return jsonify({"error": "answers directory not found", "path": base}), 404
    files = []
    try:
        files = sorted([f for f in os.listdir(base) if os.path.isfile(os.path.join(base, f))])
    except Exception:
        files = []
    results = []
    for fname in files:
        full = os.path.join(base, fname)
        t = stt_engine.transcribe_file(full) if stt_engine else None
        if t and t.strip():
            text = t.strip()
            url = f"/static/media/answers/{session_id}/{fname}"
            try:
                update_answer_text_by_media(DB_PATH, session_id, url, text)
            except Exception:
                try:
                    save_answer(DB_PATH, session_id, text, url, None, "")
                except Exception:
                    pass
            results.append({"file": fname, "text": text})
        else:
            results.append({"file": fname, "text": None})
    return jsonify({"session_id": session_id, "count": len(files), "transcribed": results})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7860, debug=False, use_reloader=False)
#d:\wipronix\venv\Scripts\python.exe app.py
#d:\wipronix\venv\Scripts\python.exe d:\wipronix\backend\app.py
#d:\wipronix\venv\Scripts\python.exe d:\wipronix\backend\app.py
#.\venv\Scripts\activate; python run.py
