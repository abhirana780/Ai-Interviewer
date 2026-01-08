from model.pipeline import ModelPipeline
from utils.helpers import sanitize_text
from utils.scoring import score_answer
from database.db_helper import get_transcript, save_transcript, get_session
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
                    "expected_answer": "A challenging system I designed was a scalable e-commerce platform with high traffic requirements. The key requirements included handling thousands of concurrent users, ensuring data consistency, providing fast response times, and supporting real-time inventory updates. Major constraints were budget limitations, tight deadlines, legacy system integration, and compliance with PCI-DSS security standards. I addressed these by implementing a microservices architecture with load balancing, database sharding, caching layers, and automated testing pipelines."
                },
                {
                    "question": "How do you approach designing a service API? Discuss versioning and backward compatibility.",
                    "expected_answer": "When designing a service API, I follow RESTful principles with clear resource naming, consistent HTTP methods, and proper status codes. For versioning, I use URL versioning like /api/v1/resource or header-based versioning. Backward compatibility is maintained by never removing fields, only adding optional ones, and using graceful degradation patterns. I document APIs thoroughly with OpenAPI/Swagger and implement rate limiting, authentication, and logging. Testing includes unit tests, integration tests, and contract testing with tools like Pact."
                },
                {
                    "question": "Explain the difference between concurrency and parallelism. When would you use each?",
                    "expected_answer": "Concurrency is about dealing with multiple tasks at once by interleaving their execution, while parallelism is about executing multiple tasks simultaneously. Concurrency is useful for I/O-bound operations like handling multiple web requests or file operations where threads can wait efficiently. Parallelism is beneficial for CPU-intensive tasks like mathematical computations or data processing where multiple cores can work simultaneously. In Python, I use asyncio for concurrency and multiprocessing for parallelism. In Java, I use thread pools for concurrency and ForkJoinPool for parallelism."
                },
                {
                    "question": "Walk through how you would optimize a slow database-backed endpoint.",
                    "expected_answer": "To optimize a slow database-backed endpoint, I first profile the query using EXPLAIN to identify bottlenecks. I add appropriate indexes on frequently queried columns, especially foreign keys and filter columns. I optimize the query structure by avoiding SELECT *, using LIMIT clauses, and reducing JOIN complexity. I implement caching with Redis or Memcached for frequently accessed data. I use connection pooling to reduce overhead. I consider database-specific optimizations like partitioning large tables, using read replicas, and query result caching. Finally, I monitor performance with tools like New Relic or DataDog."
                },
                {
                    "question": "What are trade-offs between monoliths and microservices?",
                    "expected_answer": "Monoliths offer simplicity in development, deployment, and testing with shared databases and libraries. However, they become difficult to scale, have longer deployment cycles, and create technology lock-in. Microservices provide independent scaling, technology diversity, and fault isolation but introduce complexity in distributed systems, network latency, and data consistency challenges. They require robust DevOps practices, service discovery, and inter-service communication mechanisms. I choose monoliths for small teams and simple domains, microservices for large organizations with complex domains."
                },
                {
                    "question": "How would you design a rate limiting system for an API?",
                    "expected_answer": "For rate limiting, I would implement a token bucket or leaky bucket algorithm using Redis for distributed state. Each user gets a token bucket that refills at a fixed rate. Requests consume tokens, and when buckets are empty, requests are rejected with 429 status codes. I use sliding window counters for more precise limits. I implement rate limiting at multiple levels: per-user, per-API-key, and globally. I log violations for security monitoring and provide retry-after headers. For high availability, I use Redis clusters and fallback to local counters when Redis is unavailable."
                },
                {
                    "question": "Explain how you would handle database migrations in a production environment.",
                    "expected_answer": "For production database migrations, I follow a blue-green deployment strategy with backward-compatible changes. I use migration tools like Flyway or Liquibase to version schema changes. I separate schema changes from data migrations and test them thoroughly in staging. I schedule migrations during low-traffic periods and have rollback plans. I use transactions for ACID compliance and implement proper error handling. For zero-downtime deployments, I use techniques like dual-writing, shadow tables, and feature flags. I monitor migrations closely and have automated alerts for failures."
                },
                {
                    "question": "What strategies do you use for debugging production issues?",
                    "expected_answer": "For production debugging, I rely on comprehensive logging with structured logs and correlation IDs to trace requests. I use distributed tracing tools like Jaeger or Zipkin for microservices. I implement health checks and metrics collection with Prometheus and Grafana. I use feature flags to isolate problematic code changes. For debugging, I analyze logs, check system metrics, reproduce issues in staging, and use remote debugging when safe. I maintain runbooks for common issues and post-mortem documentation for major incidents. I also use APM tools for performance monitoring."
                },
                {
                    "question": "How do you approach writing maintainable code in a team setting?",
                    "expected_answer": "For maintainable code in teams, I follow SOLID principles and clean code practices. I write comprehensive unit tests with high coverage and integration tests. I use consistent naming conventions, modular design, and clear documentation. I conduct code reviews focusing on readability, performance, and security. I implement CI/CD pipelines with automated testing and linting. I use design patterns appropriately and avoid over-engineering. I refactor regularly and keep functions small and focused. I document architectural decisions and maintain up-to-date README files."
                },
                {
                    "question": "Describe your experience with CI/CD pipelines and best practices.",
                    "expected_answer": "I have extensive experience with CI/CD using GitHub Actions, Jenkins, and GitLab CI. Best practices include fast feedback loops with parallel testing, automated code quality checks, security scanning, and dependency updates. I implement trunk-based development with feature flags, automated rollbacks on failure, and environment parity. I use infrastructure as code with Terraform, containerization with Docker, and orchestration with Kubernetes. I ensure proper secret management, audit trails, and compliance checks. I monitor deployment metrics and have alerting for pipeline failures."
                },
                {
                    "question": "How would you design a caching strategy for a high-traffic application?",
                    "expected_answer": "For high-traffic applications, I implement multi-layered caching: CDN for static assets, reverse proxy caching for dynamic content, application-level caching with Redis/Memcached, and database query caching. I use cache-aside pattern with appropriate TTL values and cache warming strategies. I implement cache key design carefully to avoid hotspots and use consistent hashing for distribution. I handle cache invalidation with event-driven updates and eventual consistency patterns. I monitor cache hit ratios, eviction rates, and implement circuit breakers for cache failures."
                },
                {
                    "question": "Explain the CAP theorem and its implications for distributed systems.",
                    "expected_answer": "CAP theorem states that distributed systems can only guarantee two of three properties: Consistency, Availability, and Partition tolerance. In practice, network partitions are inevitable, so systems must choose between consistency and availability. CP systems like traditional RDBMS prioritize consistency, potentially becoming unavailable during partitions. AP systems like DNS prioritize availability, potentially serving stale data. CA systems don't exist in real distributed systems. I design systems based on business requirements, using eventual consistency patterns, conflict resolution strategies, and appropriate data storage solutions."
                },
                {
                    "question": "What are your strategies for ensuring code quality and preventing bugs?",
                    "expected_answer": "My strategies for code quality include comprehensive testing pyramids with unit, integration, and end-to-end tests. I use static analysis tools like SonarQube, ESLint, or SonarLint for code linting. I implement code reviews with checklists focusing on security, performance, and maintainability. I use design patterns appropriately and follow coding standards. I implement continuous integration with automated testing and quality gates. I conduct regular refactoring sessions and pair programming. I use feature flags for safe deployments and implement proper error handling and logging."
                },
                {
                    "question": "How do you handle technical debt in a codebase?",
                    "expected_answer": "I handle technical debt by first identifying and documenting it through code reviews and static analysis tools. I prioritize debt based on business impact, maintenance costs, and risk factors. I allocate dedicated time in sprints for refactoring, typically 15-20% of development time. I use metrics like code complexity, test coverage, and bug frequency to track progress. I refactor incrementally using strangler patterns and feature flags. I communicate the business case for debt reduction to stakeholders and maintain a technical debt register. I ensure refactored code has proper test coverage."
                },
                {
                    "question": "Describe a time when you had to make a difficult architectural decision.",
                    "expected_answer": "In a previous project, I had to choose between a microservices architecture and a monolithic approach for a rapidly evolving startup. Despite the trend toward microservices, I chose a modular monolith initially because the team was small, the domain wasn't well understood, and we needed rapid iteration. I designed it with clear module boundaries and service-like interfaces so we could easily transition to microservices later when the domain stabilized and the team grew. This decision reduced complexity, accelerated time-to-market, and allowed us to pivot quickly based on user feedback."
                },
                {
                    "question": "How would you design a notification system that handles millions of users?",
                    "expected_answer": "For a high-scale notification system, I would use a message queue like Apache Kafka or RabbitMQ for decoupling. I'd implement fan-out patterns with topic subscriptions and use push notifications via Firebase or APNs. For email, I'd integrate with services like SendGrid or AWS SES. I'd use rate limiting and exponential backoff for delivery retries. I'd implement idempotency to handle duplicates and use dead letter queues for failed deliveries. For scalability, I'd use horizontal partitioning, caching layers, and CDN for static content. I'd monitor delivery rates, latency, and implement proper logging."
                },
                {
                    "question": "Explain different types of testing and when you would use each.",
                    "expected_answer": "Unit testing validates individual functions or classes in isolation with mocks. Integration testing verifies interactions between components like databases or APIs. End-to-end testing simulates real user scenarios across the entire system. Performance testing ensures system behavior under load using tools like JMeter. Security testing identifies vulnerabilities with tools like OWASP ZAP. Smoke testing verifies basic functionality after deployments. Regression testing ensures new changes don't break existing features. I use unit tests for development, integration tests for component interactions, and end-to-end tests for critical user flows."
                },
                {
                    "question": "What are your thoughts on code reviews and how do you conduct them?",
                    "expected_answer": "Code reviews are essential for maintaining code quality, sharing knowledge, and catching bugs early. I conduct reviews focusing on correctness, readability, performance, and security. I check for adherence to coding standards, proper error handling, and test coverage. I provide constructive feedback with explanations and suggestions rather than commands. I use review checklists and tools like GitHub PR templates. I aim for reviews within 24 hours and keep discussions professional. I also rotate reviewers to spread knowledge and avoid bottlenecks. I treat reviews as learning opportunities for both parties."
                },
                {
                    "question": "How do you stay updated with new technologies and best practices?",
                    "expected_answer": "I stay updated by following industry blogs like Martin Fowler's, subscribing to newsletters like Hacker News and InfoQ, and participating in developer communities like Stack Overflow and Reddit. I attend conferences, webinars, and meetups regularly. I experiment with new technologies in personal projects and contribute to open-source projects. I read technical books and research papers. I participate in internal tech talks and knowledge-sharing sessions. I follow thought leaders on social media and join relevant Slack/Discord communities. I also mentor junior developers which helps reinforce my own learning."
                },
                {
                    "question": "Describe your approach to optimizing application performance.",
                    "expected_answer": "My approach to performance optimization starts with profiling to identify bottlenecks using tools like profilers, APMs, and custom metrics. I optimize database queries with proper indexing, query analysis, and caching strategies. I implement lazy loading, pagination, and asynchronous processing where appropriate. I optimize front-end performance with code splitting, asset compression, and CDN usage. I use connection pooling, caching layers, and efficient algorithms. I monitor key metrics like response time, throughput, and resource utilization. I conduct load testing and implement auto-scaling. I follow performance best practices from the beginning rather than optimizing reactively."
                }
            ],
            "MERN": [
                {
                    "question": "Explain how you structure a MERN app with separate client and server. What are key folders?"
                },
                {
                    "question": "How do you manage authentication in MERN? Discuss JWT and refresh tokens."
                },
                {
                    "question": "Describe state management choices in React for MERN (Context vs Redux)."
                },
                {
                    "question": "How do you design MongoDB schemas for relational-like data in MERN?"
                },
                {
                    "question": "Explain server-side rendering vs CSR in MERN and when to use each."
                },
                {
                    "question": "How do you handle file uploads in a MERN application?"
                },
                {
                    "question": "Explain how you would implement real-time features using WebSockets or Socket.io."
                },
                {
                    "question": "What are React hooks and how do they improve functional components?"
                },
                {
                    "question": "How do you optimize React application performance?"
                },
                {
                    "question": "Describe error handling strategies in Express.js APIs."
                },
                {
                    "question": "How would you implement pagination in a MERN application?"
                },
                {
                    "question": "Explain the concept of middleware in Express and provide examples."
                },
                {
                    "question": "How do you handle CORS issues in MERN applications?"
                },
                {
                    "question": "What are the differences between useEffect and useLayoutEffect?"
                },
                {
                    "question": "How would you implement role-based access control in MERN?"
                },
                {
                    "question": "Describe your approach to API versioning in a Node.js backend."
                },
                {
                    "question": "How do you handle environment variables and configuration in MERN?"
                },
                {
                    "question": "Explain indexing strategies in MongoDB for query optimization."
                },
                {
                    "question": "What are your strategies for securing a MERN application?"
                },
                {
                    "question": "How would you implement search functionality with MongoDB?"
                }
            ],
            "Data Science": [
                {
                    "question": "Walk through a typical DS project lifecycle from problem to deployment."
                },
                {
                    "question": "How do you handle class imbalance? Discuss techniques and metrics."
                },
                {
                    "question": "Explain feature selection and regularization trade-offs."
                },
                {
                    "question": "How do you validate models to avoid leakage?"
                },
                {
                    "question": "Describe how you'd communicate findings to non-technical stakeholders."
                },
                {
                    "question": "What is the difference between bagging and boosting algorithms?"
                },
                {
                    "question": "How do you handle missing data in your datasets?"
                },
                {
                    "question": "Explain the bias-variance trade-off with practical examples."
                },
                {
                    "question": "What evaluation metrics would you use for a classification problem?"
                },
                {
                    "question": "How do you perform exploratory data analysis on a new dataset?"
                },
                {
                    "question": "Describe the process of feature engineering and its importance."
                },
                {
                    "question": "What is cross-validation and why is it important?"
                },
                {
                    "question": "How would you detect and handle outliers in your data?"
                },
                {
                    "question": "Explain the difference between supervised and unsupervised learning."
                },
                {
                    "question": "What is dimensionality reduction and when would you use it?"
                },
                {
                    "question": "How do you choose the right algorithm for a given problem?"
                },
                {
                    "question": "Describe your experience with time series analysis and forecasting."
                },
                {
                    "question": "What is A/B testing and how would you design an experiment?"
                },
                {
                    "question": "How do you ensure reproducibility in your data science projects?"
                },
                {
                    "question": "Explain the concept of ensemble methods and their advantages."
                }
            ],
            "Data Analytics": [
                {
                    "question": "How do you design a dashboard to track KPIs?"
                },
                {
                    "question": "Explain data cleaning steps for messy CSVs with missing values."
                },
                {
                    "question": "What chart types fit different data stories and why?"
                },
                {
                    "question": "Describe SQL window functions and a use case."
                },
                {
                    "question": "How do you ensure reproducibility in analytics workflows?"
                },
                {
                    "question": "What is the difference between OLTP and OLAP systems?"
                },
                {
                    "question": "How would you identify trends and patterns in large datasets?"
                },
                {
                    "question": "Explain the concept of data warehousing and its benefits."
                },
                {
                    "question": "How do you handle data quality issues in your analyses?"
                },
                {
                    "question": "Describe your experience with ETL processes and tools."
                },
                {
                    "question": "What are the best practices for creating effective visualizations?"
                },
                {
                    "question": "How would you perform cohort analysis for user retention?"
                },
                {
                    "question": "Explain the difference between correlation and causation."
                },
                {
                    "question": "How do you prioritize which metrics to track for a business?"
                },
                {
                    "question": "Describe a time when your analysis led to actionable insights."
                },
                {
                    "question": "What is data normalization and when is it necessary?"
                },
                {
                    "question": "How would you build a customer segmentation model?"
                },
                {
                    "question": "Explain your approach to funnel analysis and optimization."
                },
                {
                    "question": "What tools and technologies do you prefer for data analysis and why?"
                },
                {
                    "question": "How do you validate the accuracy of your analytical reports?"
                }
            ],
            "AI/ML": [
                {
                    "question": "Compare traditional ML and deep learning and when each is appropriate."
                },
                {
                    "question": "Explain bias-variance trade-off with examples."
                },
                {
                    "question": "How do you monitor ML models in production?"
                },
                {
                    "question": "Discuss hyperparameter tuning strategies and pitfalls."
                },
                {
                    "question": "Explain transfer learning and a practical use case."
                },
                {
                    "question": "What is the difference between CNN and RNN architectures?"
                },
                {
                    "question": "How would you handle overfitting in a neural network?"
                },
                {
                    "question": "Explain the concept of attention mechanisms in transformers."
                },
                {
                    "question": "What are GANs and what are their applications?"
                },
                {
                    "question": "How do you approach model interpretability and explainability."
                },
                {
                    "question": "Describe the process of fine-tuning a pre-trained model."
                },
                {
                    "question": "What is batch normalization and why is it useful?"
                },
                {
                    "question": "How would you optimize inference time for a deployed model?"
                },
                {
                    "question": "Explain the concept of reinforcement learning with examples."
                },
                {
                    "question": "What are the challenges of deploying ML models at scale?"
                },
                {
                    "question": "How do you handle imbalanced datasets in deep learning?"
                },
                {
                    "question": "Describe your experience with model versioning and MLOps."
                },
                {
                    "question": "What is gradient descent and its variants?"
                },
                {
                    "question": "How would you implement a recommendation system?"
                },
                {
                    "question": "Explain the difference between object detection and image segmentation."
                }
            ],
            "Python": [
                {
                    "question": "Explain generators and iterators; provide use cases."
                },
                {
                    "question": "How do you manage environments and dependencies in Python?"
                },
                {
                    "question": "Describe async/await and when it helps."
                },
                {
                    "question": "What are dataclasses and benefits vs namedtuple?"
                },
                {
                    "question": "How do you structure a package with tests and CI?"
                },
                {
                    "question": "Explain the difference between lists and tuples in Python."
                },
                {
                    "question": "What are decorators and how do you use them?"
                },
                {
                    "question": "How does Python's garbage collection work?"
                },
                {
                    "question": "Describe the GIL and its implications for multithreading."
                },
                {
                    "question": "What are context managers and how do you create them?"
                },
                {
                    "question": "Explain list comprehensions vs generator expressions."
                },
                {
                    "question": "How do you handle exceptions in Python effectively?"
                },
                {
                    "question": "What is the difference between @staticmethod and @classmethod?"
                },
                {
                    "question": "Describe your experience with Python testing frameworks."
                },
                {
                    "question": "How would you optimize slow Python code?"
                },
                {
                    "question": "Explain metaclasses and when you might use them."
                },
                {
                    "question": "What are the differences between deep copy and shallow copy?"
                },
                {
                    "question": "How do you manage configuration in Python applications?"
                },
                {
                    "question": "Describe the purpose of __init__.py files in packages."
                },
                {
                    "question": "What are Python's built-in data structures and their use cases?"
                }
            ],
            "Java": [
                {
                    "question": "Explain JVM memory model and garbage collection basics."
                },
                {
                    "question": "Discuss Streams API vs traditional loops and trade-offs."
                },
                {
                    "question": "How do you design a REST API with Spring Boot?"
                },
                {
                    "question": "Explain concurrency tools in Java (CompletableFuture, Executors)."
                },
                {
                    "question": "What are records and when to use them?"
                },
                {
                    "question": "Describe the difference between abstract classes and interfaces."
                },
                {
                    "question": "How does Spring dependency injection work?"
                },
                {
                    "question": "Explain the concept of Java annotations and their uses."
                },
                {
                    "question": "What are the principles of Object-Oriented Programming in Java?"
                },
                {
                    "question": "How do you handle exceptions in Java applications?"
                },
                {
                    "question": "Describe the differences between ArrayList and LinkedList."
                },
                {
                    "question": "What is the purpose of the Optional class?"
                },
                {
                    "question": "How would you implement caching in a Spring Boot application?"
                },
                {
                    "question": "Explain the differences between checked and unchecked exceptions."
                },
                {
                    "question": "What are design patterns and which ones do you commonly use?"
                },
                {
                    "question": "How does the Java Collections Framework work?"
                },
                {
                    "question": "Describe your experience with JPA and Hibernate."
                },
                {
                    "question": "What is the difference between == and .equals() in Java?"
                },
                {
                    "question": "How would you handle database transactions in Spring?"
                },
                {
                    "question": "Explain the concept of method overloading and overriding."
                }
            ],
            "Cloud": [
                {
                    "question": "Compare IaaS, PaaS, and SaaS with examples."
                },
                {
                    "question": "Explain scaling strategies and autoscaling triggers."
                },
                {
                    "question": "How do you design a secure VPC network layout?"
                },
                {
                    "question": "Discuss cost optimization techniques in cloud."
                },
                {
                    "question": "Describe blue/green and canary deployments."
                },
                {
                    "question": "What is the difference between horizontal and vertical scaling?"
                },
                {
                    "question": "How would you design a highly available architecture?"
                },
                {
                    "question": "Explain the concept of Infrastructure as Code with examples."
                },
                {
                    "question": "What are the benefits and challenges of containerization?"
                },
                {
                    "question": "How do you implement disaster recovery in the cloud?"
                },
                {
                    "question": "Describe your experience with cloud monitoring and logging."
                },
                {
                    "question": "What is a CDN and when would you use one?"
                },
                {
                    "question": "How would you secure data in transit and at rest in the cloud?"
                },
                {
                    "question": "Explain the concept of serverless computing and its use cases."
                },
                {
                    "question": "What are cloud load balancers and how do they work?"
                },
                {
                    "question": "How do you manage secrets and credentials in cloud environments?"
                },
                {
                    "question": "Describe the differences between S3 storage classes."
                },
                {
                    "question": "What is cloud-native architecture and its principles?"
                },
                {
                    "question": "How would you implement multi-region deployments?"
                },
                {
                    "question": "Explain the concept of service mesh and its benefits."
                }
            ],
            "Cyber": [
                {
                    "question": "Explain common OWASP top risks and mitigations."
                },
                {
                    "question": "How do you perform threat modeling for a web app?"
                },
                {
                    "question": "Discuss authentication hardening and MFA."
                },
                {
                    "question": "Explain secure storage of secrets and key rotation."
                },
                {
                    "question": "Describe incident response steps after a breach."
                },
                {
                    "question": "What is the principle of least privilege and how do you implement it?"
                },
                {
                    "question": "How would you conduct a security audit of an application?"
                },
                {
                    "question": "Explain the differences between symmetric and asymmetric encryption."
                },
                {
                    "question": "What are SQL injection attacks and how do you prevent them?"
                },
                {
                    "question": "Describe your approach to implementing secure API authentication."
                },
                {
                    "question": "How do you handle session management securely?"
                },
                {
                    "question": "What is Cross-Site Scripting (XSS) and how do you mitigate it?"
                },
                {
                    "question": "Explain the concept of defense in depth."
                },
                {
                    "question": "How would you implement secure logging practices?"
                },
                {
                    "question": "What are the best practices for password storage?"
                },
                {
                    "question": "Describe the CIA triad in information security."
                },
                {
                    "question": "How do you perform vulnerability assessments?"
                },
                {
                    "question": "What is Zero Trust architecture and its principles?"
                },
                {
                    "question": "How would you secure a microservices architecture?"
                },
                {
                    "question": "Explain the concept of security by design."
                }
            ],
            "Networking": [
                {
                    "question": "Explain the OSI model layers and their functions.",
                    "expected_answer": "The OSI model has 7 layers. Layer 1 (Physical) transmits raw bit streams. Layer 2 (Data Link) handles node-to-node transfer and error detection (MAC addresses). Layer 3 (Network) manages routing and addressing (IP). Layer 4 (Transport) ensures reliable delivery and flow control (TCP/UDP). Layer 5 (Session) establishes and manages sessions. Layer 6 (Presentation) translates and encrypts data (SSL/TLS). Layer 7 (Application) provides network services to user applications (HTTP, FTP)."
                },
                {
                    "question": "What is the difference between TCP and UDP?",
                    "expected_answer": "TCP is connection-oriented, ensuring reliable, ordered, and error-checked delivery of data. It uses a three-way handshake and handles congestion control. It's used for web browsing, email, and file transfers where accuracy matters. UDP is connectionless and does not guarantee delivery or order. It has lower overhead and latency. It's used for real-time applications like video streaming, VoIP, and online gaming where speed is critical and minor data loss is acceptable."
                },
                {
                    "question": "How does DNS work?",
                    "expected_answer": "DNS (Domain Name System) translates human-readable domain names (like google.com) into IP addresses. When a user queries a domain, the resolver first checks local cache. If missing, it queries a Root Server, which points to a TLD Server (.com). The TLD server points to the Authoritative Name Server for that domain, which returns the IP. This result is then cached by the resolver and OS to speed up future requests."
                },
                {
                    "question": "Explain the concept of Subnetting.",
                    "expected_answer": "Subnetting is the practice of dividing a large network into smaller, manageable sub-networks (subnets). It improves performance by reducing broadcast traffic and enhances security by isolating network segments. It involves borrowing bits from the host portion of an IP address to create a subnet mask. This allows administrators to allocate IP addresses more efficiently and control traffic flow between different departments or locations."
                },
                {
                    "question": "What is a VLAN and why is it used?",
                    "expected_answer": "A VLAN (Virtual Local Area Network) is a logical grouping of devices in the same broadcast domain, regardless of their physical location. It is configured on switches. VLANs improve security by isolating sensitive traffic, reduce broadcast domains to improve performance, and simplify network management by grouping users by function (e.g., HR, Engineering) rather than physical connection."
                }
            ],
            "default": [
                {
                    "question": "Tell me about a time you solved a difficult problem.",
                    "expected_answer": "I encountered a challenging problem when our e-commerce website experienced sudden performance degradation during peak shopping hours. The issue was causing timeouts and frustrated customers. I systematically analyzed server logs, database queries, and network traffic to identify the bottleneck. Through profiling, I discovered that a particular database query was taking several seconds to execute due to missing indexes. I added appropriate composite indexes, optimized the query structure, and implemented caching for frequently accessed data. The solution reduced response times from 5+ seconds to under 200ms, resulting in improved customer satisfaction and increased sales conversion rates. This experience taught me the importance of systematic debugging and performance optimization."
                },
                {
                    "question": "How do you prioritize tasks under tight deadlines?",
                    "expected_answer": "When facing tight deadlines, I first assess all tasks to understand their urgency, importance, and dependencies. I categorize tasks using the Eisenhower Matrix - urgent and important tasks get immediate attention. I break down large tasks into smaller, manageable chunks and estimate realistic timeframes. I communicate with stakeholders about priorities and potential trade-offs. I focus on high-impact tasks that deliver the most value. I use time-blocking techniques and minimize distractions. If deadlines are unrealistic, I negotiate for extensions or scope reductions. I also build in buffer time for unexpected issues. Regular progress updates help manage expectations and allow for course corrections when needed."
                },
                {
                    "question": "Describe how you handle constructive feedback.",
                    "expected_answer": "I welcome constructive feedback as an opportunity for growth and improvement. When receiving feedback, I listen actively without becoming defensive and ask clarifying questions to fully understand the perspective. I thank the person for taking the time to provide feedback. I reflect on the feedback objectively, separating the message from the delivery style. I identify specific actionable items and create a plan to address the concerns. I follow up to show that I've implemented the suggestions. I also seek feedback proactively to continuously improve. I view feedback as a gift that helps me become better at my job and strengthen working relationships. I maintain a growth mindset and see feedback as part of my professional development journey."
                },
                {
                    "question": "What motivates you at work?",
                    "expected_answer": "I'm motivated by solving complex technical challenges that have real-world impact on users and businesses. I enjoy the process of breaking down complicated problems into elegant solutions. Learning new technologies and staying current with industry trends keeps me engaged. Collaborating with talented teammates and mentoring junior developers provides fulfillment. Seeing my code in production and receiving positive user feedback is rewarding. I'm also motivated by opportunities to take ownership of projects and make architectural decisions. Creating efficient, scalable, and maintainable systems that stand the test of time drives my passion for software development."
                },
                {
                    "question": "Where do you want to grow in the next year?",
                    "expected_answer": "In the next year, I want to deepen my expertise in cloud-native technologies and microservices architecture. I plan to gain hands-on experience with Kubernetes, service meshes, and advanced DevOps practices. I want to improve my leadership skills by taking on more mentoring responsibilities and potentially leading small projects. I'm interested in learning more about system design at scale and understanding business domains more deeply. I also want to contribute more to open-source projects and perhaps speak at technical conferences. Additionally, I'd like to develop better product sense to understand how technical decisions align with business objectives."
                }
            ]
        }

    def start_session(self, session_id, role="Software Engineer", candidate_name=None):
        role_key = sanitize_text(role) or "Software Engineer"
        
        # Role Mapping to match question keys
        role_map = {
            "ai engineer": "AI/ML",
            "ai/ml": "AI/ML",
            "artificial intelligence": "AI/ML",
            "data scientist": "Data Science",
            "data science": "Data Science",
            "data analyst": "Data Analytics",
            "data analytics": "Data Analytics",
            "mern": "MERN",
            "mern stack": "MERN",
            "mern stack developer": "MERN",
            "cloud": "Cloud",
            "cloud engineer": "Cloud",
            "cyber": "Cyber",
            "cybersecurity": "Cyber",
            "cybersecurity engineer": "Cyber",
            "software engineer": "Software Engineer",
            "software developer": "Software Engineer",
            "network": "Networking",
            "network engineer": "Networking",
            "networking": "Networking"
        }
        
        # Normalize role for lookup
        lookup_role = role_key.lower()
        bank_key = role_map.get(lookup_role, "Software Engineer")
        
        # Try to find specific bank, fallback to Software Engineer, then default
        bank = self.question_banks.get(bank_key) or self.question_banks.get("Software Engineer") or self.question_banks["default"]
        
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
        session_data = get_session(self.db_path, session_id) or {}
        candidate_name = session_data.get("candidate_name", "")
        mobile_number = session_data.get("mobile_number", "")
        email = session_data.get("email", "")
        qualification = session_data.get("qualification", "")
        college_name = session_data.get("college_name", "")
        track = session_data.get("track", role)  # Use role as fallback
        
        transcript += f"CANDIDATE: {answer}\n"

        # Get expected answer if available
        expected_answer = current_question_obj.get("expected_answer", "") if isinstance(current_question_obj, dict) else ""
        
        # Score with context (question, track, and expected answer)
        score, feedback = score_answer(answer, question=current_question, track=role, expected_answer=expected_answer)

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

    
