from model.pipeline import ModelPipeline
from utils.helpers import sanitize_text
from utils.scoring import score_answer
from utils.prompts import INTERVIEWER_PROMPT
from database.db_helper import get_transcript, save_transcript
import json
import re
import random


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
                "What are trade-offs between monoliths and microservices?",
                "How would you design a rate limiting system for an API?",
                "Explain how you would handle database migrations in a production environment.",
                "What strategies do you use for debugging production issues?",
                "How do you approach writing maintainable code in a team setting?",
                "Describe your experience with CI/CD pipelines and best practices.",
                "How would you design a caching strategy for a high-traffic application?",
                "Explain the CAP theorem and its implications for distributed systems.",
                "What are your strategies for ensuring code quality and preventing bugs?",
                "How do you handle technical debt in a codebase?",
                "Describe a time when you had to make a difficult architectural decision.",
                "How would you design a notification system that handles millions of users?",
                "Explain different types of testing and when you would use each.",
                "What are your thoughts on code reviews and how do you conduct them?",
                "How do you stay updated with new technologies and best practices?",
                "Describe your approach to optimizing application performance."
            ],
            "MERN": [
                "Explain how you structure a MERN app with separate client and server. What are key folders?",
                "How do you manage authentication in MERN? Discuss JWT and refresh tokens.",
                "Describe state management choices in React for MERN (Context vs Redux).",
                "How do you design MongoDB schemas for relational-like data in MERN?",
                "Explain server-side rendering vs CSR in MERN and when to use each.",
                "How do you handle file uploads in a MERN application?",
                "Explain how you would implement real-time features using WebSockets or Socket.io.",
                "What are React hooks and how do they improve functional components?",
                "How do you optimize React application performance?",
                "Describe error handling strategies in Express.js APIs.",
                "How would you implement pagination in a MERN application?",
                "Explain the concept of middleware in Express and provide examples.",
                "How do you handle CORS issues in MERN applications?",
                "What are the differences between useEffect and useLayoutEffect?",
                "How would you implement role-based access control in MERN?",
                "Describe your approach to API versioning in a Node.js backend.",
                "How do you handle environment variables and configuration in MERN?",
                "Explain indexing strategies in MongoDB for query optimization.",
                "What are your strategies for securing a MERN application?",
                "How would you implement search functionality with MongoDB?"
            ],
            "Data Science": [
                "Walk through a typical DS project lifecycle from problem to deployment.",
                "How do you handle class imbalance? Discuss techniques and metrics.",
                "Explain feature selection and regularization trade-offs.",
                "How do you validate models to avoid leakage?",
                "Describe how you'd communicate findings to non-technical stakeholders.",
                "What is the difference between bagging and boosting algorithms?",
                "How do you handle missing data in your datasets?",
                "Explain the bias-variance trade-off with practical examples.",
                "What evaluation metrics would you use for a classification problem?",
                "How do you perform exploratory data analysis on a new dataset?",
                "Describe the process of feature engineering and its importance.",
                "What is cross-validation and why is it important?",
                "How would you detect and handle outliers in your data?",
                "Explain the difference between supervised and unsupervised learning.",
                "What is dimensionality reduction and when would you use it?",
                "How do you choose the right algorithm for a given problem?",
                "Describe your experience with time series analysis and forecasting.",
                "What is A/B testing and how would you design an experiment?",
                "How do you ensure reproducibility in your data science projects?",
                "Explain the concept of ensemble methods and their advantages."
            ],
            "Data Analytics": [
                "How do you design a dashboard to track KPIs?",
                "Explain data cleaning steps for messy CSVs with missing values.",
                "What chart types fit different data stories and why?",
                "Describe SQL window functions and a use case.",
                "How do you ensure reproducibility in analytics workflows?",
                "What is the difference between OLTP and OLAP systems?",
                "How would you identify trends and patterns in large datasets?",
                "Explain the concept of data warehousing and its benefits.",
                "How do you handle data quality issues in your analyses?",
                "Describe your experience with ETL processes and tools.",
                "What are the best practices for creating effective visualizations?",
                "How would you perform cohort analysis for user retention?",
                "Explain the difference between correlation and causation.",
                "How do you prioritize which metrics to track for a business?",
                "Describe a time when your analysis led to actionable insights.",
                "What is data normalization and when is it necessary?",
                "How would you build a customer segmentation model?",
                "Explain your approach to funnel analysis and optimization.",
                "What tools and technologies do you prefer for data analysis and why?",
                "How do you validate the accuracy of your analytical reports?"
            ],
            "AI/ML": [
                "Compare traditional ML and deep learning and when each is appropriate.",
                "Explain bias-variance trade-off with examples.",
                "How do you monitor ML models in production?",
                "Discuss hyperparameter tuning strategies and pitfalls.",
                "Explain transfer learning and a practical use case.",
                "What is the difference between CNN and RNN architectures?",
                "How would you handle overfitting in a neural network?",
                "Explain the concept of attention mechanisms in transformers.",
                "What are GANs and what are their applications?",
                "How do you approach model interpretability and explainability?",
                "Describe the process of fine-tuning a pre-trained model.",
                "What is batch normalization and why is it useful?",
                "How would you optimize inference time for a deployed model?",
                "Explain the concept of reinforcement learning with examples.",
                "What are the challenges of deploying ML models at scale?",
                "How do you handle imbalanced datasets in deep learning?",
                "Describe your experience with model versioning and MLOps.",
                "What is gradient descent and its variants?",
                "How would you implement a recommendation system?",
                "Explain the difference between object detection and image segmentation."
            ],
            "Python": [
                "Explain generators and iterators; provide use cases.",
                "How do you manage environments and dependencies in Python?",
                "Describe async/await and when it helps.",
                "What are dataclasses and benefits vs namedtuple?",
                "How do you structure a package with tests and CI?",
                "Explain the difference between lists and tuples in Python.",
                "What are decorators and how do you use them?",
                "How does Python's garbage collection work?",
                "Describe the GIL and its implications for multithreading.",
                "What are context managers and how do you create them?",
                "Explain list comprehensions vs generator expressions.",
                "How do you handle exceptions in Python effectively?",
                "What is the difference between @staticmethod and @classmethod?",
                "Describe your experience with Python testing frameworks.",
                "How would you optimize slow Python code?",
                "Explain metaclasses and when you might use them.",
                "What are the differences between deep copy and shallow copy?",
                "How do you manage configuration in Python applications?",
                "Describe the purpose of __init__.py files in packages.",
                "What are Python's built-in data structures and their use cases?"
            ],
            "Java": [
                "Explain JVM memory model and garbage collection basics.",
                "Discuss Streams API vs traditional loops and trade-offs.",
                "How do you design a REST API with Spring Boot?",
                "Explain concurrency tools in Java (CompletableFuture, Executors).",
                "What are records and when to use them?",
                "Describe the difference between abstract classes and interfaces.",
                "How does Spring dependency injection work?",
                "Explain the concept of Java annotations and their uses.",
                "What are the principles of Object-Oriented Programming in Java?",
                "How do you handle exceptions in Java applications?",
                "Describe the differences between ArrayList and LinkedList.",
                "What is the purpose of the Optional class?",
                "How would you implement caching in a Spring Boot application?",
                "Explain the differences between checked and unchecked exceptions.",
                "What are design patterns and which ones do you commonly use?",
                "How does the Java Collections Framework work?",
                "Describe your experience with JPA and Hibernate.",
                "What is the difference between == and .equals() in Java?",
                "How would you handle database transactions in Spring?",
                "Explain the concept of method overloading and overriding."
            ],
            "Cloud": [
                "Compare IaaS, PaaS, and SaaS with examples.",
                "Explain scaling strategies and autoscaling triggers.",
                "How do you design a secure VPC network layout?",
                "Discuss cost optimization techniques in cloud.",
                "Describe blue/green and canary deployments.",
                "What is the difference between horizontal and vertical scaling?",
                "How would you design a highly available architecture?",
                "Explain the concept of Infrastructure as Code with examples.",
                "What are the benefits and challenges of containerization?",
                "How do you implement disaster recovery in the cloud?",
                "Describe your experience with cloud monitoring and logging.",
                "What is a CDN and when would you use one?",
                "How would you secure data in transit and at rest in the cloud?",
                "Explain the concept of serverless computing and its use cases.",
                "What are cloud load balancers and how do they work?",
                "How do you manage secrets and credentials in cloud environments?",
                "Describe the differences between S3 storage classes.",
                "What is cloud-native architecture and its principles?",
                "How would you implement multi-region deployments?",
                "Explain the concept of service mesh and its benefits."
            ],
            "Cyber": [
                "Explain common OWASP top risks and mitigations.",
                "How do you perform threat modeling for a web app?",
                "Discuss authentication hardening and MFA.",
                "Explain secure storage of secrets and key rotation.",
                "Describe incident response steps after a breach.",
                "What is the principle of least privilege and how do you implement it?",
                "How would you conduct a security audit of an application?",
                "Explain the differences between symmetric and asymmetric encryption.",
                "What are SQL injection attacks and how do you prevent them?",
                "Describe your approach to implementing secure API authentication.",
                "How do you handle session management securely?",
                "What is Cross-Site Scripting (XSS) and how do you mitigate it?",
                "Explain the concept of defense in depth.",
                "How would you implement secure logging practices?",
                "What are the best practices for password storage?",
                "Describe the CIA triad in information security.",
                "How do you perform vulnerability assessments?",
                "What is Zero Trust architecture and its principles?",
                "How would you secure a microservices architecture?",
                "Explain the concept of security by design."
            ],
            "default": [
                "Tell me about a time you solved a difficult problem.",
                "How do you prioritize tasks under tight deadlines?",
                "Describe how you handle constructive feedback.",
                "What motivates you at work?",
                "Where do you want to grow in the next year?",
                "Describe a situation where you had to work with a difficult team member.",
                "How do you handle stress and pressure at work?",
                "What is your greatest professional achievement?",
                "How do you approach learning new skills or technologies?",
                "Describe a time when you failed and what you learned from it.",
                "What are your strengths and weaknesses?",
                "How do you ensure work-life balance?",
                "What type of work environment do you thrive in?",
                "How do you handle conflicting priorities?",
                "Describe your leadership style.",
                "What makes you a good fit for this role?",
                "How do you measure success in your work?",
                "What are your career goals for the next 5 years?",
                "How do you contribute to team success?",
                "What would your previous colleagues say about you?"
            ]
        }

    def start_session(self, session_id, role="Software Engineer", candidate_name=None):
        role = sanitize_text(role) or "Software Engineer"
        bank = self.question_banks.get(role) or self.question_banks.get("Software Engineer") or self.question_banks["default"]
        # Shuffle questions to randomize order for each session
        questions = list(bank)
        random.shuffle(questions)
        
        # Limit to 5 questions only
        questions = questions[:5]
        
        first_question = sanitize_text(questions[0]) if questions else ""
        self.sessions[session_id] = {
            "role": role, 
            "index": 0, 
            "questions": questions, 
            "candidate_name": candidate_name,
            "asked_questions": [first_question]  # Track asked questions
        }

        transcript = f"INTERVIEWER: {first_question}\n" if first_question else ""
        # Save transcript with candidate info to preserve data
        save_transcript(self.db_path, session_id, transcript, candidate_name)

        return first_question

    def handle_answer(self, session_id, answer):
        answer = sanitize_text(answer)

        transcript = get_transcript(self.db_path, session_id) or ""
        
        # Get current question and track info from session state
        state = self.sessions.get(session_id) or {}
        role = state.get("role", "Software Engineer")
        current_idx = state.get("index", 0)
        questions = state.get("questions", [])
        current_question = questions[current_idx] if current_idx < len(questions) else ""
        
        # Get candidate information from database to preserve during updates
        from database.db_helper import get_session
        session_data = get_session(self.db_path, session_id) or {}
        candidate_name = session_data.get("candidate_name", "")
        mobile_number = session_data.get("mobile_number", "")
        email = session_data.get("email", "")
        qualification = session_data.get("qualification", "")
        college_name = session_data.get("college_name", "")
        track = session_data.get("track", role)  # Use role as fallback
        
        transcript += f"CANDIDATE: {answer}\n"

        # Score with context (question and track)
        score, feedback = score_answer(answer, question=current_question, track=role)

        # Determine next question from session state
        next_q = None
        if state:
            idx = state.get("index", -1) + 1
            questions = state.get("questions") or []
            asked_questions = state.get("asked_questions") or []
            
            # Check if we've completed all questions (max 5)
            if idx < len(questions):
                next_q = sanitize_text(questions[idx])
                
                # Track this question as asked
                if next_q and next_q not in asked_questions:
                    asked_questions.append(next_q)
                
                state["index"] = idx
                state["asked_questions"] = asked_questions
                self.sessions[session_id] = state
            else:
                # All questions completed - end interview
                next_q = ""
        else:
            # State missing - end interview (don't generate new questions)
            next_q = ""

        if next_q:
            transcript += f"INTERVIEWER: {next_q}\n"
        else:
            transcript += "INTERVIEW COMPLETE\n"

        transcript += f"SCORE: {score}\nFEEDBACK: {feedback}\n"
        # Save transcript with ALL candidate info to preserve data
        save_transcript(self.db_path, session_id, transcript, 
                       candidate_name, mobile_number, email, qualification, college_name, track)

        return {"next_question": next_q if next_q else None, "score": score, "feedback": feedback}

    def _extract_asked_questions(self, transcript):
        """Extract questions that have already been asked from the transcript."""
        asked = []
        if not transcript:
            return asked
        
        lines = transcript.split("\n")
        for line in lines:
            if line.startswith("INTERVIEWER:"):
                question = line.replace("INTERVIEWER:", "").strip()
                if question:
                    asked.append(question)
        return asked
    
    def _extract_json(self, text):
        try:
            match = re.search(r"{.*}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            return None
        return None
