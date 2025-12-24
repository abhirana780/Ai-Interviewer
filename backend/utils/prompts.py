INTERVIEWER_PROMPT = """
You are an expert technical interviewer.
Rules:
- Ask one question at a time.
- After candidate answers, evaluate from 0-5.
- Give short feedback.
- Output JSON when asked: { "next_question": "", "score": X, "feedback": "" }
"""

# Role descriptions used for TF-IDF similarity in ATS scoring
ROLE_DESCRIPTIONS = {
    "General": "Well-rounded software professional with experience in programming, version control, debugging, testing, working with APIs, databases, and cloud services. Strong fundamentals and clear communication.",
    "MERN": "Full-stack JavaScript developer skilled in React, Node.js, Express, and MongoDB. Familiar with JWT auth, Redux or Context state management, TypeScript, hooks, and building RESTful APIs.",
    "Data Science": "Data scientist proficient in Python, pandas, numpy, scikit-learn, statistics, feature engineering, model training and evaluation, and building pipelines. Knowledge of regression, classification, and deployment.",
    "Data Analytics": "Analyst experienced with Excel, SQL, dashboards (Tableau/Power BI), ETL, KPI tracking, and reporting. Strong data cleaning, visualization, and storytelling skills.",
    "AI/ML": "Machine learning engineer with experience in deep learning (PyTorch/TensorFlow), transformers, fine-tuning, GPU acceleration, and inference optimization. Understands model monitoring and MLOps basics.",
    "Python": "Python developer experienced in web frameworks (Flask/Django), packaging, venv, async programming, testing (pytest), and building maintainable applications.",
    "Java": "Java developer familiar with Spring Boot, REST APIs, JPA/Hibernate, Gradle/Maven tooling, JVM fundamentals, and concurrency utilities.",
    "Cloud": "Cloud engineer knowledgeable in AWS/Azure/GCP services, networking, IAM, storage, compute, Kubernetes, and IaC tools like Terraform. Focus on reliability and cost optimization.",
    "Cyber": "Security professional versed in OWASP risks, threat modeling, authentication hardening (MFA), encryption, vulnerability assessment, and incident response."
}

# Track-specific keyword sets for ATS scoring
ATS_KEYWORDS = {
    "General": ["python", "java", "sql", "git", "docker", "api", "testing", "cloud", "linux", "ci/cd", "rest", "microservices", "devops", "agile", "scrum", "json", "xml", "http", "https", "tcp/ip", "oop", "design patterns"],
    "MERN": ["react", "node", "express", "mongodb", "jwt", "redux", "hooks", "typescript", "vite", "next.js", "csr", "ssr", "component", "props", "state", "lifecycle", "middleware", "routing", "axios", "cors", "npm", "webpack"],
    "Data Science": ["pandas", "numpy", "scikit-learn", "sklearn", "regression", "classification", "feature", "model", "pipeline", "cross-validation", "metrics", "clustering", "nlp", "deep learning", "neural networks", "supervised", "unsupervised", "matplotlib", "seaborn", "jupyter"],
    "Data Analytics": ["excel", "tableau", "power bi", "dashboard", "kpi", "sql", "etl", "report", "visualization", "pivot", "looker", "qlik", "sap", "google analytics", "segmentation", "forecasting", "trend analysis"],
    "AI/ML": ["deep learning", "neural", "pytorch", "tensorflow", "transformer", "fine-tuning", "gpu", "inference", "embedding", "mlops", "computer vision", "nlp", "reinforcement learning", "gan", "cnn", "rnn", "bert", "llm", "openai", "huggingface"],
    "Python": ["python", "flask", "django", "asyncio", "pip", "venv", "pytest", "package", "dataclass", "typing", "decorator", "generator", "context manager", "virtualenv", "sqlalchemy", "requests", "beautifulsoup"],
    "Java": ["java", "spring", "spring boot", "jpa", "hibernate", "maven", "gradle", "rest", "jvm", "concurrency", "multithreading", "collections", "streams", "lambda", "optional", "annotations", "servlets"],
    "Cloud": ["aws", "azure", "gcp", "s3", "ec2", "iam", "kubernetes", "terraform", "vpc", "autoscaling", "lambda", "ecs", "eks", "cloudformation", "arm", "load balancer", "cdn", "route53"],
    "Cyber": ["owasp", "xss", "csrf", "encryption", "mfa", "threat", "mitigation", "vulnerability", "zero trust", "pentest", "firewall", "ids", "ips", "siem", "soc", "phishing", "malware", "ransomware", "iso27001"]
}
