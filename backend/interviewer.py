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
        # Question banks with expected answer keywords for accurate scoring
        self.question_banks = {
            "Software Engineer": [
                {
                    "question": "Describe a challenging system you designed. What were the requirements and constraints?",
                    "keywords": ["requirements", "constraints", "architecture", "scalability", "performance", "design decisions"]
                },
                {
                    "question": "How do you approach designing a service API? Discuss versioning and backward compatibility.",
                    "keywords": ["api design", "versioning", "backward compatibility", "rest", "endpoints", "documentation"]
                },
                {
                    "question": "Explain the difference between concurrency and parallelism. When would you use each?",
                    "keywords": ["concurrency", "parallelism", "threads", "processes", "cpu bound", "io bound"]
                },
                {
                    "question": "Walk through how you would optimize a slow database-backed endpoint.",
                    "keywords": ["database optimization", "indexing", "query optimization", "caching", "connection pooling"]
                },
                {
                    "question": "What are trade-offs between monoliths and microservices?",
                    "keywords": ["monolith", "microservices", "scalability", "deployment", "complexity", "communication"]
                },
                {
                    "question": "How would you design a rate limiting system for an API?",
                    "keywords": ["rate limiting", "throttling", "tokens", "sliding window", "distributed systems", "algorithms"]
                },
                {
                    "question": "Explain how you would handle database migrations in a production environment.",
                    "keywords": ["database migration", "schema changes", "rollback", "zero downtime", "versioning", "liquibase"]
                },
                {
                    "question": "What strategies do you use for debugging production issues?",
                    "keywords": ["debugging", "logging", "monitoring", "profiling", "distributed tracing", "root cause"]
                },
                {
                    "question": "How do you approach writing maintainable code in a team setting?",
                    "keywords": ["code maintainability", "clean code", "documentation", "code reviews", "standards", "refactoring"]
                },
                {
                    "question": "Describe your experience with CI/CD pipelines and best practices.",
                    "keywords": ["ci/cd", "continuous integration", "continuous deployment", "automation", "testing", "rollback"]
                },
                {
                    "question": "How would you design a caching strategy for a high-traffic application?",
                    "keywords": ["caching", "cache strategy", "redis", "memory", "ttl", "cache invalidation"]
                },
                {
                    "question": "Explain the CAP theorem and its implications for distributed systems.",
                    "keywords": ["cap theorem", "consistency", "availability", "partition tolerance", "trade-offs", "distributed systems"]
                },
                {
                    "question": "What are your strategies for ensuring code quality and preventing bugs?",
                    "keywords": ["code quality", "testing", "code reviews", "linting", "static analysis", "unit tests"]
                },
                {
                    "question": "How do you handle technical debt in a codebase?",
                    "keywords": ["technical debt", "refactoring", "prioritization", "measurement", "repayment", "documentation"]
                },
                {
                    "question": "Describe a time when you had to make a difficult architectural decision.",
                    "keywords": ["architectural decision", "trade-offs", "evaluation", "stakeholders", "implementation", "results"]
                },
                {
                    "question": "How would you design a notification system that handles millions of users?",
                    "keywords": ["notification system", "scalability", "message queue", "push notifications", "email", "real-time"]
                },
                {
                    "question": "Explain different types of testing and when you would use each.",
                    "keywords": ["testing", "unit testing", "integration testing", "end-to-end testing", "performance testing", "automated testing"]
                },
                {
                    "question": "What are your thoughts on code reviews and how do you conduct them?",
                    "keywords": ["code reviews", "best practices", "feedback", "collaboration", "quality assurance", "process"]
                },
                {
                    "question": "How do you stay updated with new technologies and best practices?",
                    "keywords": ["learning", "technologies", "best practices", "communities", "resources", "continuous learning"]
                },
                {
                    "question": "Describe your approach to optimizing application performance.",
                    "keywords": ["performance optimization", "profiling", "bottlenecks", "caching", "database", "algorithms"]
                }
            ],
            "MERN": [
                {
                    "question": "Explain how you structure a MERN app with separate client and server. What are key folders?",
                    "keywords": ["mern structure", "client-server", "folder structure", "components", "routes", "controllers"]
                },
                {
                    "question": "How do you manage authentication in MERN? Discuss JWT and refresh tokens.",
                    "keywords": ["authentication", "jwt", "refresh tokens", "sessions", "security", "middleware"]
                },
                {
                    "question": "Describe state management choices in React for MERN (Context vs Redux).",
                    "keywords": ["state management", "react context", "redux", "global state", "reducers", "actions"]
                },
                {
                    "question": "How do you design MongoDB schemas for relational-like data in MERN?",
                    "keywords": ["mongodb schema", "relational data", "embedding", "referencing", "normalization", "denormalization"]
                },
                {
                    "question": "Explain server-side rendering vs CSR in MERN and when to use each.",
                    "keywords": ["server-side rendering", "client-side rendering", "seo", "performance", "initial load", "user experience"]
                },
                {
                    "question": "How do you handle file uploads in a MERN application?",
                    "keywords": ["file uploads", "multipart/form-data", "multer", "storage", "validation", "security"]
                },
                {
                    "question": "Explain how you would implement real-time features using WebSockets or Socket.io.",
                    "keywords": ["real-time", "websockets", "socket.io", "bidirectional", "events", "connections"]
                },
                {
                    "question": "What are React hooks and how do they improve functional components?",
                    "keywords": ["react hooks", "functional components", "useState", "useEffect", "custom hooks", "lifecycle"]
                },
                {
                    "question": "How do you optimize React application performance?",
                    "keywords": ["react optimization", "performance", "memoization", "lazy loading", "bundle size", "rendering"]
                },
                {
                    "question": "Describe error handling strategies in Express.js APIs.",
                    "keywords": ["error handling", "express.js", "middleware", "centralized", "status codes", "logging"]
                },
                {
                    "question": "How would you implement pagination in a MERN application?",
                    "keywords": ["pagination", "skip", "limit", "cursor-based", "performance", "user experience"]
                },
                {
                    "question": "Explain the concept of middleware in Express and provide examples.",
                    "keywords": ["middleware", "express", "request-response", "authentication", "logging", "error handling"]
                },
                {
                    "question": "How do you handle CORS issues in MERN applications?",
                    "keywords": ["cors", "cross-origin", "headers", "security", "access control", "domains"]
                },
                {
                    "question": "What are the differences between useEffect and useLayoutEffect?",
                    "keywords": ["useeffect", "uselayouteffect", "rendering", "dom manipulation", "synchronous", "asynchronous"]
                },
                {
                    "question": "How would you implement role-based access control in MERN?",
                    "keywords": ["rbac", "access control", "roles", "permissions", "middleware", "authentication"]
                },
                {
                    "question": "Describe your approach to API versioning in a Node.js backend.",
                    "keywords": ["api versioning", "node.js", "urls", "headers", "backward compatibility", "migration"]
                },
                {
                    "question": "How do you handle environment variables and configuration in MERN?",
                    "keywords": ["environment variables", "configuration", "dotenv", "secrets", "deployment", "security"]
                },
                {
                    "question": "Explain indexing strategies in MongoDB for query optimization.",
                    "keywords": ["mongodb indexing", "query optimization", "single field", "compound", "multikey", "text indexes"]
                },
                {
                    "question": "What are your strategies for securing a MERN application?",
                    "keywords": ["security", "mern", "authentication", "authorization", "input validation", "owasp"]
                },
                {
                    "question": "How would you implement search functionality with MongoDB?",
                    "keywords": ["search", "mongodb", "text search", "indexes", "aggregation", "performance"]
                }
            ],
            "Data Science": [
                {
                    "question": "Walk through a typical DS project lifecycle from problem to deployment.",
                    "keywords": ["ds lifecycle", "problem definition", "data collection", "modeling", "deployment", "monitoring"]
                },
                {
                    "question": "How do you handle class imbalance? Discuss techniques and metrics.",
                    "keywords": ["class imbalance", "sampling", "smote", "metrics", "roc-auc", "f1-score"]
                },
                {
                    "question": "Explain feature selection and regularization trade-offs.",
                    "keywords": ["feature selection", "regularization", "lasso", "ridge", "overfitting", "model complexity"]
                },
                {
                    "question": "How do you validate models to avoid leakage?",
                    "keywords": ["model validation", "data leakage", "cross-validation", "temporal splits", "target leakage", "preprocessing"]
                },
                {
                    "question": "Describe how you'd communicate findings to non-technical stakeholders.",
                    "keywords": ["communication", "stakeholders", "visualization", "storytelling", "insights", "recommendations"]
                },
                {
                    "question": "What is the difference between bagging and boosting algorithms?",
                    "keywords": ["bagging", "boosting", "random forest", "gradient boosting", "ensemble", "bias-variance"]
                },
                {
                    "question": "How do you handle missing data in your datasets?",
                    "keywords": ["missing data", "imputation", "deletion", "mean", "median", "interpolation"]
                },
                {
                    "question": "Explain the bias-variance trade-off with practical examples.",
                    "keywords": ["bias-variance", "underfitting", "overfitting", "model complexity", "mse", "generalization"]
                },
                {
                    "question": "What evaluation metrics would you use for a classification problem?",
                    "keywords": ["classification metrics", "accuracy", "precision", "recall", "f1-score", "confusion matrix"]
                },
                {
                    "question": "How do you perform exploratory data analysis on a new dataset?",
                    "keywords": ["eda", "exploratory analysis", "visualization", "summary statistics", "outliers", "correlations"]
                },
                {
                    "question": "Describe the process of feature engineering and its importance.",
                    "keywords": ["feature engineering", "feature extraction", "domain knowledge", "transformation", "encoding", "scaling"]
                },
                {
                    "question": "What is cross-validation and why is it important?",
                    "keywords": ["cross-validation", "model validation", "k-fold", "generalization", "overfitting", "performance estimation"]
                },
                {
                    "question": "How would you detect and handle outliers in your data?",
                    "keywords": ["outliers", "detection", "handling", "z-score", "iqr", "robust statistics"]
                },
                {
                    "question": "Explain the difference between supervised and unsupervised learning.",
                    "keywords": ["supervised learning", "unsupervised learning", "labeled data", "clustering", "classification", "regression"]
                },
                {
                    "question": "What is dimensionality reduction and when would you use it?",
                    "keywords": ["dimensionality reduction", "pca", "tsne", "curse of dimensionality", "features", "visualization"]
                },
                {
                    "question": "How do you choose the right algorithm for a given problem?",
                    "keywords": ["algorithm selection", "problem type", "data characteristics", "performance", "interpretability", "scalability"]
                },
                {
                    "question": "Describe your experience with time series analysis and forecasting.",
                    "keywords": ["time series", "forecasting", "arima", "seasonality", "trends", "stationarity"]
                },
                {
                    "question": "What is A/B testing and how would you design an experiment?",
                    "keywords": ["a/b testing", "experiment design", "hypothesis testing", "statistical significance", "control group", "variants"]
                },
                {
                    "question": "How do you ensure reproducibility in your data science projects?",
                    "keywords": ["reproducibility", "version control", "pipelines", "seeds", "environments", "documentation"]
                },
                {
                    "question": "Explain the concept of ensemble methods and their advantages.",
                    "keywords": ["ensemble methods", "bagging", "boosting", "stacking", "accuracy", "generalization"]
                }
            ],
            "Data Analytics": [
                {
                    "question": "How do you design a dashboard to track KPIs?",
                    "keywords": ["dashboard design", "kpis", "visualization", "user experience", "metrics", "interactivity"]
                },
                {
                    "question": "Explain data cleaning steps for messy CSVs with missing values.",
                    "keywords": ["data cleaning", "csv", "missing values", "imputation", "validation", "transformation"]
                },
                {
                    "question": "What chart types fit different data stories and why?",
                    "keywords": ["chart types", "data visualization", "bar charts", "line charts", "scatter plots", "storytelling"]
                },
                {
                    "question": "Describe SQL window functions and a use case.",
                    "keywords": ["sql window functions", "over clause", "rank", "lag", "lead", "aggregation"]
                },
                {
                    "question": "How do you ensure reproducibility in analytics workflows?",
                    "keywords": ["reproducibility", "workflows", "version control", "documentation", "automation", "environments"]
                },
                {
                    "question": "What is the difference between OLTP and OLAP systems?",
                    "keywords": ["oltp", "olap", "transactional", "analytical", "real-time", "batch processing"]
                },
                {
                    "question": "How would you identify trends and patterns in large datasets?",
                    "keywords": ["trend analysis", "pattern recognition", "visualization", "statistical methods", "time series", "clustering"]
                },
                {
                    "question": "Explain the concept of data warehousing and its benefits.",
                    "keywords": ["data warehouse", "etl", "star schema", "snowflake schema", "performance", "historical data"]
                },
                {
                    "question": "How do you handle data quality issues in your analyses?",
                    "keywords": ["data quality", "validation", "cleansing", "accuracy", "consistency", "completeness"]
                },
                {
                    "question": "Describe your experience with ETL processes and tools.",
                    "keywords": ["etl", "extract", "transform", "load", "pipelines", "tools", "scheduling"]
                },
                {
                    "question": "What are the best practices for creating effective visualizations?",
                    "keywords": ["data visualization", "best practices", "design principles", "color", "labels", "audience"]
                },
                {
                    "question": "How would you perform cohort analysis for user retention?",
                    "keywords": ["cohort analysis", "user retention", "behavioral analytics", "time periods", "segments", "metrics"]
                },
                {
                    "question": "Explain the difference between correlation and causation.",
                    "keywords": ["correlation", "causation", "association", "experimental design", "confounding variables", "inference"]
                },
                {
                    "question": "How do you prioritize which metrics to track for a business?",
                    "keywords": ["metrics", "kpi selection", "business objectives", "strategic alignment", "measurability", "actionability"]
                },
                {
                    "question": "Describe a time when your analysis led to actionable insights.",
                    "keywords": ["actionable insights", "business impact", "recommendations", "data-driven", "decision making", "results"]
                },
                {
                    "question": "What is data normalization and when is it necessary?",
                    "keywords": ["data normalization", "database design", "redundancy", "integrity", "forms", "relationships"]
                },
                {
                    "question": "How would you build a customer segmentation model?",
                    "keywords": ["customer segmentation", "clustering", "rfm analysis", "demographics", "behavioral data", "personalization"]
                },
                {
                    "question": "Explain your approach to funnel analysis and optimization.",
                    "keywords": ["funnel analysis", "conversion rates", "drop-off points", "optimization", "user journey", "metrics"]
                },
                {
                    "question": "What tools and technologies do you prefer for data analysis and why?",
                    "keywords": ["analytics tools", "python", "sql", "tableau", "power bi", "r", "excel"]
                },
                {
                    "question": "How do you validate the accuracy of your analytical reports?",
                    "keywords": ["report validation", "accuracy", "testing", "peer review", "source data", "cross-checking"]
                }
            ],
            "AI/ML": [
                {
                    "question": "Compare traditional ML and deep learning and when each is appropriate.",
                    "keywords": ["traditional ml", "deep learning", "neural networks", "data requirements", "interpretability", "performance"]
                },
                {
                    "question": "Explain bias-variance trade-off with examples.",
                    "keywords": ["bias-variance", "underfitting", "overfitting", "model complexity", "mse", "generalization"]
                },
                {
                    "question": "How do you monitor ML models in production?",
                    "keywords": ["ml monitoring", "production", "drift detection", "performance metrics", "alerting", "retraining"]
                },
                {
                    "question": "Discuss hyperparameter tuning strategies and pitfalls.",
                    "keywords": ["hyperparameter tuning", "grid search", "random search", "bayesian optimization", "overfitting", "cv"]
                },
                {
                    "question": "Explain transfer learning and a practical use case.",
                    "keywords": ["transfer learning", "pre-trained models", "fine-tuning", "computer vision", "nlp", "efficiency"]
                },
                {
                    "question": "What is the difference between CNN and RNN architectures?",
                    "keywords": ["cnn", "rnn", "convolutional", "recurrent", "spatial data", "sequential data", "memory"]
                },
                {
                    "question": "How would you handle overfitting in a neural network?",
                    "keywords": ["overfitting", "regularization", "dropout", "early stopping", "data augmentation", "batch normalization"]
                },
                {
                    "question": "Explain the concept of attention mechanisms in transformers.",
                    "keywords": ["attention", "transformers", "self-attention", "context", "sequence modeling", "nlp"]
                },
                {
                    "question": "What are GANs and what are their applications?",
                    "keywords": ["gans", "generative models", "discriminator", "generator", "image synthesis", "data augmentation"]
                },
                {
                    "question": "How do you approach model interpretability and explainability.",
                    "keywords": ["model interpretability", "explainability", "lime", "shap", "feature importance", "transparency"]
                },
                {
                    "question": "Describe the process of fine-tuning a pre-trained model.",
                    "keywords": ["fine-tuning", "pre-trained models", "transfer learning", "learning rate", "layers", "domain adaptation"]
                },
                {
                    "question": "What is batch normalization and why is it useful?",
                    "keywords": ["batch normalization", "training", "convergence", "internal covariate shift", "stability", "gradient flow"]
                },
                {
                    "question": "How would you optimize inference time for a deployed model?",
                    "keywords": ["inference optimization", "model compression", "quantization", "pruning", "hardware", "latency"]
                },
                {
                    "question": "Explain the concept of reinforcement learning with examples.",
                    "keywords": ["reinforcement learning", "agent", "environment", "reward", "policy", "q-learning"]
                },
                {
                    "question": "What are the challenges of deploying ML models at scale?",
                    "keywords": ["ml deployment", "scalability", "latency", "monitoring", "versioning", "infrastructure"]
                },
                {
                    "question": "How do you handle imbalanced datasets in deep learning?",
                    "keywords": ["imbalanced datasets", "sampling", "class weights", "focal loss", "data augmentation", "metrics"]
                },
                {
                    "question": "Describe your experience with model versioning and MLOps.",
                    "keywords": ["model versioning", "mlops", "pipelines", "experiment tracking", "deployment", "ci/cd"]
                },
                {
                    "question": "What is gradient descent and its variants?",
                    "keywords": ["gradient descent", "sgd", "adam", "rmsprop", "optimization", "learning rate"]
                },
                {
                    "question": "How would you implement a recommendation system?",
                    "keywords": ["recommendation system", "collaborative filtering", "content-based", "matrix factorization", "deep learning", "evaluation"]
                },
                {
                    "question": "Explain the difference between object detection and image segmentation.",
                    "keywords": ["object detection", "image segmentation", "bounding boxes", "pixel-wise", "mask r-cnn", "yolo"]
                }
            ],
            "Python": [
                {
                    "question": "Explain generators and iterators; provide use cases.",
                    "keywords": ["generators", "iterators", "yield", "memory efficiency", "lazy evaluation", "iteration"]
                },
                {
                    "question": "How do you manage environments and dependencies in Python?",
                    "keywords": ["python environments", "virtualenv", "conda", "pip", "requirements.txt", "dependency management"]
                },
                {
                    "question": "Describe async/await and when it helps.",
                    "keywords": ["async/await", "asynchronous", "concurrency", "event loop", "non-blocking", "io-bound"]
                },
                {
                    "question": "What are dataclasses and benefits vs namedtuple?",
                    "keywords": ["dataclasses", "namedtuple", "boilerplate", "type hints", "immutability", "methods"]
                },
                {
                    "question": "How do you structure a package with tests and CI?",
                    "keywords": ["package structure", "setup.py", "tests", "ci/cd", "directory layout", "distribution"]
                },
                {
                    "question": "Explain the difference between lists and tuples in Python.",
                    "keywords": ["lists", "tuples", "mutability", "performance", "use cases", "syntax"]
                },
                {
                    "question": "What are decorators and how do you use them?",
                    "keywords": ["decorators", "functions", "wrapping", "@ syntax", "logging", "authentication"]
                },
                {
                    "question": "How does Python's garbage collection work?",
                    "keywords": ["garbage collection", "memory management", "reference counting", "cyclic garbage collector", "gc module"]
                },
                {
                    "question": "Describe the GIL and its implications for multithreading.",
                    "keywords": ["gil", "global interpreter lock", "multithreading", "multiprocessing", "cpu-bound", "io-bound"]
                },
                {
                    "question": "What are context managers and how do you create them?",
                    "keywords": ["context managers", "with statement", "__enter__", "__exit__", "resource management", "cleanup"]
                },
                {
                    "question": "Explain list comprehensions vs generator expressions.",
                    "keywords": ["list comprehensions", "generator expressions", "memory usage", "syntax", "performance", "iteration"]
                },
                {
                    "question": "How do you handle exceptions in Python effectively?",
                    "keywords": ["exception handling", "try/except", "finally", "raise", "custom exceptions", "best practices"]
                },
                {
                    "question": "What is the difference between @staticmethod and @classmethod?",
                    "keywords": ["staticmethod", "classmethod", "instance methods", "cls", "self", "decorators"]
                },
                {
                    "question": "Describe your experience with Python testing frameworks.",
                    "keywords": ["testing frameworks", "unittest", "pytest", "mocking", "fixtures", "test coverage"]
                },
                {
                    "question": "How would you optimize slow Python code?",
                    "keywords": ["python optimization", "profiling", "cython", "numpy", "algorithms", "data structures"]
                },
                {
                    "question": "Explain metaclasses and when you might use them.",
                    "keywords": ["metaclasses", "class creation", "__new__", "__init__", "metaprogramming", "orm"]
                },
                {
                    "question": "What are the differences between deep copy and shallow copy?",
                    "keywords": ["deep copy", "shallow copy", "copy module", "references", "mutability", "assignment"]
                },
                {
                    "question": "How do you manage configuration in Python applications?",
                    "keywords": ["configuration", "settings", "environment variables", "config files", "dotenv", "pydantic"]
                },
                {
                    "question": "Describe the purpose of __init__.py files in packages.",
                    "keywords": ["__init__.py", "packages", "module initialization", "namespace", "imports", "submodules"]
                },
                {
                    "question": "What are Python's built-in data structures and their use cases?",
                    "keywords": ["data structures", "list", "dict", "set", "tuple", "collections module"]
                }
            ],
            "Java": [
                {
                    "question": "Explain JVM memory model and garbage collection basics.",
                    "keywords": ["jvm", "memory model", "heap", "stack", "garbage collection", "gc roots"]
                },
                {
                    "question": "Discuss Streams API vs traditional loops and trade-offs.",
                    "keywords": ["streams api", "loops", "functional programming", "parallel processing", "readability", "performance"]
                },
                {
                    "question": "How do you design a REST API with Spring Boot?",
                    "keywords": ["rest api", "spring boot", "controllers", "dto", "validation", "http methods"]
                },
                {
                    "question": "Explain concurrency tools in Java (CompletableFuture, Executors).",
                    "keywords": ["concurrency", "completablefuture", "executors", "thread pools", "async", "callbacks"]
                },
                {
                    "question": "What are records and when to use them?",
                    "keywords": ["records", "immutable data", "boilerplate reduction", "constructors", "accessors", "java 14+"]
                },
                {
                    "question": "Describe the difference between abstract classes and interfaces.",
                    "keywords": ["abstract classes", "interfaces", "inheritance", "multiple inheritance", "method implementation", "contracts"]
                },
                {
                    "question": "How does Spring dependency injection work?",
                    "keywords": ["spring di", "dependency injection", "ioc container", "beans", "autowiring", "configuration"]
                },
                {
                    "question": "Explain the concept of Java annotations and their uses.",
                    "keywords": ["annotations", "metadata", "@interface", "runtime", "compile-time", "framework integration"]
                },
                {
                    "question": "What are the principles of Object-Oriented Programming in Java?",
                    "keywords": ["oop", "encapsulation", "inheritance", "polymorphism", "abstraction", "classes"]
                },
                {
                    "question": "How do you handle exceptions in Java applications?",
                    "keywords": ["exceptions", "try-catch", "throws", "custom exceptions", "checked vs unchecked", "best practices"]
                },
                {
                    "question": "Describe the differences between ArrayList and LinkedList.",
                    "keywords": ["arraylist", "linkedlist", "performance", "memory", "access time", "insertion"]
                },
                {
                    "question": "What is the purpose of the Optional class?",
                    "keywords": ["optional", "null safety", "avoid nullpointerexception", "functional methods", "orElse", "map"]
                },
                {
                    "question": "How would you implement caching in a Spring Boot application?",
                    "keywords": ["caching", "spring boot", "@cacheable", "cache manager", "redis", "ehcache"]
                },
                {
                    "question": "Explain the differences between checked and unchecked exceptions.",
                    "keywords": ["checked exceptions", "unchecked exceptions", "compile-time", "runtime", "exception hierarchy", "handling"]
                },
                {
                    "question": "What are design patterns and which ones do you commonly use?",
                    "keywords": ["design patterns", "singleton", "factory", "observer", "strategy", "builder"]
                },
                {
                    "question": "How does the Java Collections Framework work?",
                    "keywords": ["collections framework", "list", "set", "map", "interfaces", "implementations"]
                },
                {
                    "question": "Describe your experience with JPA and Hibernate.",
                    "keywords": ["jpa", "hibernate", "orm", "entities", "jpql", "transactions"]
                },
                {
                    "question": "What is the difference between == and .equals() in Java?",
                    "keywords": ["== operator", ".equals() method", "reference comparison", "value comparison", "strings", "objects"]
                },
                {
                    "question": "How would you handle database transactions in Spring?",
                    "keywords": ["database transactions", "spring", "@transactional", "acid properties", "rollback", "isolation"]
                },
                {
                    "question": "Explain the concept of method overloading and overriding.",
                    "keywords": ["method overloading", "method overriding", "polymorphism", "signature", "@override", "inheritance"]
                }
            ],
            "Cloud": [
                {
                    "question": "Compare IaaS, PaaS, and SaaS with examples.",
                    "keywords": ["iaas", "paas", "saas", "service models", "responsibility", "examples", "control"]
                },
                {
                    "question": "Explain scaling strategies and autoscaling triggers.",
                    "keywords": ["scaling", "autoscaling", "horizontal scaling", "vertical scaling", "metrics", "triggers"]
                },
                {
                    "question": "How do you design a secure VPC network layout?",
                    "keywords": ["vpc", "network security", "subnets", "acl", "security groups", "private/public"]
                },
                {
                    "question": "Discuss cost optimization techniques in cloud.",
                    "keywords": ["cost optimization", "reserved instances", "spot instances", "auto shutdown", "monitoring", "budgets"]
                },
                {
                    "question": "Describe blue/green and canary deployments.",
                    "keywords": ["blue-green deployment", "canary deployment", "release strategies", "zero downtime", "rollback", "risk mitigation"]
                },
                {
                    "question": "What is the difference between horizontal and vertical scaling?",
                    "keywords": ["horizontal scaling", "vertical scaling", "scale out", "scale up", "load balancing", "performance"]
                },
                {
                    "question": "How would you design a highly available architecture?",
                    "keywords": ["high availability", "fault tolerance", "redundancy", "failover", "regions", "load balancing"]
                },
                {
                    "question": "Explain the concept of Infrastructure as Code with examples.",
                    "keywords": ["iac", "infrastructure as code", "terraform", "cloudformation", "version control", "automation"]
                },
                {
                    "question": "What are the benefits and challenges of containerization?",
                    "keywords": ["containerization", "docker", "kubernetes", "benefits", "challenges", "portability"]
                },
                {
                    "question": "How do you implement disaster recovery in the cloud?",
                    "keywords": ["disaster recovery", "backup", "restore", "rto", "rpo", "replication", "failover"]
                },
                {
                    "question": "Describe your experience with cloud monitoring and logging.",
                    "keywords": ["cloud monitoring", "logging", "cloudwatch", "stackdriver", "alerts", "dashboards"]
                },
                {
                    "question": "What is a CDN and when would you use one?",
                    "keywords": ["cdn", "content delivery network", "edge locations", "latency", "caching", "global distribution"]
                },
                {
                    "question": "How would you secure data in transit and at rest in the cloud?",
                    "keywords": ["data security", "encryption", "tls", "ssl", "kms", "at rest", "in transit"]
                },
                {
                    "question": "Explain the concept of serverless computing and its use cases.",
                    "keywords": ["serverless", "functions as a service", "lambda", "event-driven", "scalability", "cost efficiency"]
                },
                {
                    "question": "What are cloud load balancers and how do they work?",
                    "keywords": ["load balancers", "distribution", "health checks", "algorithms", "ssl termination", "high availability"]
                },
                {
                    "question": "How do you manage secrets and credentials in cloud environments?",
                    "keywords": ["secrets management", "credentials", "vault", "kms", "environment variables", "rotation"]
                },
                {
                    "question": "Describe the differences between S3 storage classes.",
                    "keywords": ["s3 storage classes", "standard", "ia", "glacier", "cost", "retrieval time", "durability"]
                },
                {
                    "question": "What is cloud-native architecture and its principles?",
                    "keywords": ["cloud-native", "microservices", "containers", "devops", "ci/cd", "observability"]
                },
                {
                    "question": "How would you implement multi-region deployments?",
                    "keywords": ["multi-region", "geographic distribution", "latency", "disaster recovery", "data replication", "dns routing"]
                },
                {
                    "question": "Explain the concept of service mesh and its benefits.",
                    "keywords": ["service mesh", "istio", "linkerd", "microservices", "traffic management", "security", "observability"]
                }
            ],
            "Cyber": [
                {
                    "question": "Explain common OWASP top risks and mitigations.",
                    "keywords": ["owasp", "top risks", "injection", "xss", "broken authentication", "mitigations", "security controls"]
                },
                {
                    "question": "How do you perform threat modeling for a web app?",
                    "keywords": ["threat modeling", "stride", "attack surface", "assets", "threats", "mitigations"]
                },
                {
                    "question": "Discuss authentication hardening and MFA.",
                    "keywords": ["authentication", "mfa", "password policies", "session management", "tokens", "biometrics"]
                },
                {
                    "question": "Explain secure storage of secrets and key rotation.",
                    "keywords": ["secret storage", "key rotation", "encryption", "vault", "hsm", "access controls"]
                },
                {
                    "question": "Describe incident response steps after a breach.",
                    "keywords": ["incident response", "breach", "containment", "eradication", "recovery", "lessons learned"]
                },
                {
                    "question": "What is the principle of least privilege and how do you implement it?",
                    "keywords": ["least privilege", "access control", "principle", "permissions", "roles", "privilege escalation"]
                },
                {
                    "question": "How would you conduct a security audit of an application?",
                    "keywords": ["security audit", "vulnerability assessment", "penetration testing", "compliance", "findings", "remediation"]
                },
                {
                    "question": "Explain the differences between symmetric and asymmetric encryption.",
                    "keywords": ["symmetric encryption", "asymmetric encryption", "keys", "performance", "use cases", "algorithms"]
                },
                {
                    "question": "What are SQL injection attacks and how do you prevent them?",
                    "keywords": ["sql injection", "input validation", "prepared statements", "orm", "escaping", "waf"]
                },
                {
                    "question": "Describe your approach to implementing secure API authentication.",
                    "keywords": ["api authentication", "oauth", "jwt", "api keys", "tls", "rate limiting"]
                },
                {
                    "question": "How do you handle session management securely?",
                    "keywords": ["session management", "cookies", "tokens", "timeout", "regeneration", "secure flags"]
                },
                {
                    "question": "What is Cross-Site Scripting (XSS) and how do you mitigate it?",
                    "keywords": ["xss", "cross-site scripting", "input sanitization", "output encoding", "csp", "validation"]
                },
                {
                    "question": "Explain the concept of defense in depth.",
                    "keywords": ["defense in depth", "layered security", "multiple controls", "redundancy", "compartmentalization", "strategy"]
                },
                {
                    "question": "How would you implement secure logging practices?",
                    "keywords": ["secure logging", "log management", "pii protection", "integrity", "audit trails", "retention"]
                },
                {
                    "question": "What are the best practices for password storage?",
                    "keywords": ["password storage", "hashing", "salting", "bcrypt", "pbkdf2", "credential stuffing"]
                },
                {
                    "question": "Describe the CIA triad in information security.",
                    "keywords": ["cia triad", "confidentiality", "integrity", "availability", "security principles", "balance"]
                },
                {
                    "question": "How do you perform vulnerability assessments?",
                    "keywords": ["vulnerability assessment", "scanning", "tools", "cvss", "remediation", "reporting"]
                },
                {
                    "question": "What is Zero Trust architecture and its principles?",
                    "keywords": ["zero trust", "never trust always verify", "microsegmentation", "least privilege", "continuous validation", "network security"]
                },
                {
                    "question": "How would you secure a microservices architecture?",
                    "keywords": ["microservices security", "api gateway", "service mesh", "authentication", "authorization", "encryption"]
                },
                {
                    "question": "Explain the concept of security by design.",
                    "keywords": ["security by design", "sdlc", "threat modeling", "secure coding", "privacy", "compliance"]
                }
            ],
            "default": [
                {
                    "question": "Tell me about a time you solved a difficult problem.",
                    "keywords": ["problem solving", "challenge", "approach", "solution", "outcome", "learning"]
                },
                {
                    "question": "How do you prioritize tasks under tight deadlines?",
                    "keywords": ["prioritization", "time management", "deadlines", "urgency", "importance", "strategies"]
                },
                {
                    "question": "Describe how you handle constructive feedback.",
                    "keywords": ["feedback", "reception", "improvement", "growth mindset", "response", "implementation"]
                },
                {
                    "question": "What motivates you at work?",
                    "keywords": ["motivation", "drivers", "purpose", "goals", "engagement", "satisfaction"]
                },
                {
                    "question": "Where do you want to grow in the next year?",
                    "keywords": ["career growth", "development", "skills", "objectives", "timeline", "aspirations"]
                },
                {
                    "question": "Describe a situation where you had to work with a difficult team member.",
                    "keywords": ["teamwork", "conflict resolution", "communication", "collaboration", "professionalism", "outcome"]
                },
                {
                    "question": "How do you handle stress and pressure at work?",
                    "keywords": ["stress management", "pressure", "coping strategies", "resilience", "work-life balance", "productivity"]
                },
                {
                    "question": "What is your greatest professional achievement?",
                    "keywords": ["achievement", "success", "impact", "recognition", "skills demonstrated", "results"]
                },
                {
                    "question": "How do you approach learning new skills or technologies?",
                    "keywords": ["learning", "skill development", "adaptability", "resources", "practice", "application"]
                },
                {
                    "question": "Describe a time when you failed and what you learned from it.",
                    "keywords": ["failure", "setback", "reflection", "learning", "growth", "improvement"]
                },
                {
                    "question": "What are your strengths and weaknesses?",
                    "keywords": ["strengths", "weaknesses", "self-awareness", "improvement", "development", "honesty"]
                },
                {
                    "question": "How do you ensure work-life balance?",
                    "keywords": ["work-life balance", "boundaries", "time management", "well-being", "productivity", "stress"]
                },
                {
                    "question": "What type of work environment do you thrive in?",
                    "keywords": ["work environment", "culture", "collaboration", "autonomy", "structure", "preferences"]
                },
                {
                    "question": "How do you handle conflicting priorities?",
                    "keywords": ["conflicting priorities", "decision making", "negotiation", "communication", "stakeholders", "resolution"]
                },
                {
                    "question": "Describe your leadership style.",
                    "keywords": ["leadership", "management", "influence", "team", "vision", "approach"]
                },
                {
                    "question": "What makes you a good fit for this role?",
                    "keywords": ["fit", "qualifications", "experience", "skills", "alignment", "value"]
                },
                {
                    "question": "How do you measure success in your work?",
                    "keywords": ["success metrics", "goals", "performance", "outcomes", "impact", "evaluation"]
                },
                {
                    "question": "What are your career goals for the next 5 years?",
                    "keywords": ["career goals", "aspirations", "development", "progression", "planning", "vision"]
                },
                {
                    "question": "How do you contribute to team success?",
                    "keywords": ["team contribution", "collaboration", "support", "shared goals", "communication", "results"]
                },
                {
                    "question": "What would your previous colleagues say about you?",
                    "keywords": ["colleague perspective", "reputation", "work style", "relationships", "characteristics", "feedback"]
                }
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
        
        first_question = sanitize_text(questions[0]["question"]) if questions else ""
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
        current_question_obj = questions[current_idx] if current_idx < len(questions) else {}
        current_question = current_question_obj.get("question", "") if isinstance(current_question_obj, dict) else ""
        expected_keywords = current_question_obj.get("keywords", []) if isinstance(current_question_obj, dict) else []
        
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

        # Score with context (question, track, and expected keywords)
        score, feedback = score_answer(answer, question=current_question, track=role, expected_keywords=expected_keywords)

        # Determine next question from session state
        next_q = None
        if state:
            idx = state.get("index", -1) + 1
            questions = state.get("questions") or []
            asked_questions = state.get("asked_questions") or []
            
            # Check if we've completed all questions (max 5)
            if idx < len(questions):
                next_q_obj = questions[idx]
                next_q = sanitize_text(next_q_obj.get("question", "")) if isinstance(next_q_obj, dict) else sanitize_text(next_q_obj)
                
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

    
