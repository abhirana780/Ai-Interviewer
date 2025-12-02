from model.pipeline import ModelPipeline
from utils.helpers import sanitize_text
from utils.scoring import score_answer
from utils.prompts import INTERVIEWER_PROMPT
from database.db_helper import get_transcript, save_transcript
import json
import re


class Interviewer:
    def __init__(self, model_dir, db_path):
        self.pipeline = ModelPipeline(model_dir=model_dir)
        self.db_path = db_path
        self.sessions = {}
        self.question_banks = {
            "Software Engineer": [
                "Describe a challenging system you designed. What were the requirements and constraints?",
                "How do you approach designing a service API? Discuss versioning and backward compatibility.",
                "Explain the difference between concurrency and parallelism. When would you use each?",
                "Walk through how you would optimize a slow database-backed endpoint.",
                "What are trade-offs between monoliths and microservices?"
            ],
            "MERN": [
                "Explain how you structure a MERN app with separate client and server. What are key folders?",
                "How do you manage authentication in MERN? Discuss JWT and refresh tokens.",
                "Describe state management choices in React for MERN (Context vs Redux).",
                "How do you design MongoDB schemas for relational-like data in MERN?",
                "Explain server-side rendering vs CSR in MERN and when to use each."
            ],
            "Data Science": [
                "Walk through a typical DS project lifecycle from problem to deployment.",
                "How do you handle class imbalance? Discuss techniques and metrics.",
                "Explain feature selection and regularization trade-offs.",
                "How do you validate models to avoid leakage?",
                "Describe how you’d communicate findings to non-technical stakeholders."
            ],
            "Data Analytics": [
                "How do you design a dashboard to track KPIs?",
                "Explain data cleaning steps for messy CSVs with missing values.",
                "What chart types fit different data stories and why?",
                "Describe SQL window functions and a use case.",
                "How do you ensure reproducibility in analytics workflows?"
            ],
            "AI/ML": [
                "Compare traditional ML and deep learning and when each is appropriate.",
                "Explain bias-variance trade-off with examples.",
                "How do you monitor ML models in production?",
                "Discuss hyperparameter tuning strategies and pitfalls.",
                "Explain transfer learning and a practical use case."
            ],
            "Python": [
                "Explain generators and iterators; provide use cases.",
                "How do you manage environments and dependencies in Python?",
                "Describe async/await and when it helps.",
                "What are dataclasses and benefits vs namedtuple?",
                "How do you structure a package with tests and CI?"
            ],
            "Java": [
                "Explain JVM memory model and garbage collection basics.",
                "Discuss Streams API vs traditional loops and trade-offs.",
                "How do you design a REST API with Spring Boot?",
                "Explain concurrency tools in Java (CompletableFuture, Executors).",
                "What are records and when to use them?"
            ],
            "Cloud": [
                "Compare IaaS, PaaS, and SaaS with examples.",
                "Explain scaling strategies and autoscaling triggers.",
                "How do you design a secure VPC network layout?",
                "Discuss cost optimization techniques in cloud.",
                "Describe blue/green and canary deployments."
            ],
            "Cyber": [
                "Explain common OWASP top risks and mitigations.",
                "How do you perform threat modeling for a web app?",
                "Discuss authentication hardening and MFA.",
                "Explain secure storage of secrets and key rotation.",
                "Describe incident response steps after a breach."
            ],
            "default": [
                "Tell me about a time you solved a difficult problem.",
                "How do you prioritize tasks under tight deadlines?",
                "Describe how you handle constructive feedback.",
                "What motivates you at work?",
                "Where do you want to grow in the next year?"
            ]
        }

    def start_session(self, session_id, role="Software Engineer"):
        role = sanitize_text(role) or "Software Engineer"
        bank = self.question_banks.get(role) or self.question_banks.get("Software Engineer") or self.question_banks["default"]
        questions = list(bank)
        first_question = sanitize_text(questions[0]) if questions else ""
        self.sessions[session_id] = {"role": role, "index": 0, "questions": questions}

        transcript = f"INTERVIEWER: {first_question}\n" if first_question else ""
        save_transcript(self.db_path, session_id, transcript)

        return first_question

    def handle_answer(self, session_id, answer):
        answer = sanitize_text(answer)

        transcript = get_transcript(self.db_path, session_id) or ""
        transcript += f"CANDIDATE: {answer}\n"

        # Score and feedback
        score, feedback = score_answer(answer)

        # Determine next question from session state
        state = self.sessions.get(session_id) or {}

        next_q = None
        if state:
            idx = state.get("index", -1) + 1
            questions = state.get("questions") or []
            if idx < len(questions):
                next_q = sanitize_text(questions[idx])
                state["index"] = idx
                self.sessions[session_id] = state
            else:
                next_q = ""
        else:
            # Fallback if state missing
            next_q = sanitize_text(self.pipeline.generate("Ask a follow-up interview question.", max_length=80))

        if next_q:
            transcript += f"INTERVIEWER: {next_q}\n"
        else:
            transcript += "INTERVIEW COMPLETE\n"

        transcript += f"SCORE: {score}\nFEEDBACK: {feedback}\n"
        save_transcript(self.db_path, session_id, transcript)

        return {"next_question": next_q if next_q else None, "score": score, "feedback": feedback}

    def _extract_json(self, text):
        try:
            match = re.search(r"{.*}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            return None
        return None
