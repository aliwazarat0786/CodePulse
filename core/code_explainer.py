"""
Code Intelligence & Semantic Explanation Engine for CodePulse AI.
Analyzes code intent, architectural role, purpose, and generates actionable refactoring roadmaps.
"""
import re
from typing import Dict, Any, List
from models.schemas import Issue, Summary, Metrics

class CodeExplainer:
    @staticmethod
    def infer_code_purpose(source_code: str, language: str, filename: str) -> Dict[str, Any]:
        """
        Infers the functional domain, architectural purpose, capabilities, and target runtime.
        """
        code_lower = source_code.lower()
        lines = source_code.splitlines()
        loc = len(lines)

        purpose_title = "General Utility & Algorithm Module"
        domain = "General Software Engineering"
        target_runtime = "Standard Execution Environment"
        capabilities = []

        # 1. React / Next.js Component Architecture
        if any(tok in code_lower for tok in ["react", "usestate", "useeffect", "usecontext", "dangerouslysetinnerhtml", "next/image", "next/router", "jsx"]):
            purpose_title = "React.js Interactive UI Component Architecture"
            domain = "Modern Reactive Frontend & Component Layer"
            target_runtime = "React Virtual DOM / Next.js Server & Browser"
            capabilities.append("Reactive state management (useState / useEffect)")
            capabilities.append("Declarative JSX virtual DOM component rendering")
            if "dangerouslysetinnerhtml" in code_lower:
                capabilities.append("Direct unescaped HTML string DOM mounting")

        # 2. Node.js & Express API Gateway
        elif any(tok in code_lower for tok in ["express()", "app.use(", "app.get(", "app.post(", "req, res", "child_process", "bodyparser"]):
            purpose_title = "Node.js & Express REST API Gateway"
            domain = "Asynchronous Server-Side Backend"
            target_runtime = "Node.js V8 Engine / Express Middleware Pipeline"
            capabilities.append("HTTP REST endpoint routing & request middleware dispatching")
            capabilities.append("Non-blocking asynchronous I/O request processing")

        # 3. MongoDB & Mongoose / PyMongo NoSQL Layer
        elif any(tok in code_lower for tok in ["mongoose", "pymongo", "mongoclient", "$where", "schema({", "findone(", ".find("]):
            purpose_title = "MongoDB NoSQL Document Store & Model Schema"
            domain = "NoSQL Document Database & Data Layer"
            target_runtime = "MongoDB Engine & BSON Protocol"
            capabilities.append("Schemaless JSON/BSON document persistence")
            capabilities.append("NoSQL aggregation pipeline & query filtering")

        # 4. Django Web Application & ORM
        elif any(tok in code_lower for tok in ["django.db", "models.model", "django.http", "django.shortcuts", "views.py", "mark_safe", "csrf_exempt"]):
            purpose_title = "Django Full-Stack Web Application & ORM Model"
            domain = "Python Web Application Framework & ORM"
            target_runtime = "Django WSGI/ASGI & Python Virtualenv"
            capabilities.append("Django ORM database model persistence & migrations")
            capabilities.append("MVC / MVT HTTP request-response lifecycle handling")

        # 5. Flask / FastAPI Microservice
        elif any(tok in code_lower for tok in ["flask", "fastapi", "apirouter", "@app.route", "render_template", "blueprint"]):
            purpose_title = "Flask / FastAPI Asynchronous Microservice"
            domain = "Lightweight Python REST & Web Service"
            target_runtime = "WSGI / ASGI (Gunicorn / Uvicorn) Runtime"
            capabilities.append("Decorated route endpoint routing & JSON serialization")
            capabilities.append("Jinja2 / OpenAPI request-response processing")

        # 6. SQL / PostgreSQL Relational Database Schema & Stored Procedure
        elif language == "sql" or any(tok in code_lower for tok in ["plpgsql", "create table", "select * from", "primary key", "foreign key", "insert into"]):
            purpose_title = "Relational Database Schema & Stored Procedure Layer"
            domain = "Relational Data Management (RDBMS / PostgreSQL)"
            target_runtime = "PostgreSQL / ANSI SQL Database Engine"
            capabilities.append("Declarative relational table DDL schema definition")
            capabilities.append("SQL query filtering, indexing, and constraint enforcement")
            if "plpgsql" in code_lower or "create function" in code_lower:
                capabilities.append("PL/pgSQL transactional stored procedure execution")

        # 7. Frontend / Web UI Controller (Vanilla JS)
        elif any(tok in code_lower for tok in ["document.", "window.", "addeventlistener", "getelementbyid", "localstorage", "fetch(", "modal", "toast"]):
            purpose_title = "Client-Side Frontend Application & UI Controller"
            domain = "Web Application & User Interface Layer"
            target_runtime = "Modern Web Browser / ECMAScript Runtime"
            capabilities.append("DOM element manipulation & event-driven UI management")
            if "fetch(" in code_lower or "xmlhttprequest" in code_lower:
                capabilities.append("Asynchronous HTTP network communication")
            if "clipboard" in code_lower:
                capabilities.append("System clipboard integration & user export interactions")

        # 2. Health & Calculation Tools
        elif any(tok in code_lower for tok in ["bmi", "height", "weight", "underweight", "overweight", "obese", "calorie", "metric"]):
            purpose_title = "Health Metric & Body Mass Index (BMI) Computation Tool"
            domain = "Healthcare & Biomarker Analytics"
            target_runtime = "Interactive CLI / Calculation Service"
            capabilities.append("Anthropometric ratio calculation (Weight-to-Height squared)")
            capabilities.append("Clinical categorization (Underweight, Normal, Overweight, Obese)")

        # 3. Cryptography & Security / Auth
        elif any(tok in code_lower for tok in ["password", "hashlib", "jwt", "token", "sha256", "md5", "encrypt", "decrypt", "auth", "secret"]):
            purpose_title = "Authentication & Cryptographic Token Handler"
            domain = "Security & Identity Management"
            target_runtime = "Backend Authentication / Middleware Service"
            capabilities.append("Credential hashing & signature generation")
            capabilities.append("Access control token authorization")

        # 4. Database & Storage / Persistence
        elif any(tok in code_lower for tok in ["sqlite3", "sql", "select ", "insert into", "database", "cursor.execute", "transaction", "commit()"]):
            purpose_title = "Database Persistence & Query Execution Layer"
            domain = "Data Access Layer (DAL) / ORM"
            target_runtime = "Relational Database Backend Engine"
            capabilities.append("Structured Query Language (SQL) execution")
            capabilities.append("Record retrieval, filtering, and transaction persistence")

        # 5. Payment & Financial Processing
        elif any(tok in code_lower for tok in ["payment", "transaction", "stripe", "amount", "checkout", "billing", "invoice", "balance"]):
            purpose_title = "E-Commerce Transaction & Billing Processing Engine"
            domain = "Financial Technology / E-Commerce"
            target_runtime = "Secure Transaction Gateway"
            capabilities.append("Monetary ledger transaction processing")
            capabilities.append("Gateway API handshake & checkout flow management")

        # 6. Low-Level Systems & Memory Management
        elif any(tok in code_lower for tok in ["malloc", "calloc", "free(", "gets(", "strcpy", "pointer", "buffer", "stdio.h", "iostream", "make_unique"]):
            purpose_title = "Low-Level Systems & Memory Allocation Buffer"
            domain = "Systems Programming & Native Runtime"
            target_runtime = "Native Operating System Process (x86_64 / ARM)"
            capabilities.append("Dynamic heap allocation and memory buffer lifetime management")
            capabilities.append("Stream I/O & low-level memory block manipulation")

        # 7. Machine Learning / Math Analytics
        elif any(tok in code_lower for tok in ["numpy", "pandas", "sklearn", "tensorflow", "torch", "matrix", "dataset", "predict", "model"]):
            purpose_title = "Data Science & Predictive Modeling Pipeline"
            domain = "Machine Learning & Scientific Analytics"
            target_runtime = "Python Scientific Computing Stack (NumPy / SciPy)"
            capabilities.append("Matrix manipulation and vectorized tensor computation")
            capabilities.append("Inference execution and mathematical feature transformation")

        else:
            if language == "python":
                target_runtime = "Python 3.10+ Virtual Environment"
            elif language == "javascript":
                target_runtime = "Node.js Server / V8 Engine"
            elif language == "java":
                target_runtime = "Java Virtual Machine (JVM)"
            elif language in ["c", "cpp"]:
                target_runtime = "Compiled Native Binary"

            capabilities.append("Standard algorithmic flow & modular function execution")

        if not capabilities:
            capabilities.append("Procedural logic execution and data transformation")

        description = (
            f"This {language.upper()} source file functions as a {purpose_title.lower()}. "
            f"It operates within the {domain.lower()} under a {target_runtime.lower()}, "
            f"containing approximately {loc} lines of code across modular routines."
        )

        return {
            "purpose_title": purpose_title,
            "domain": domain,
            "target_runtime": target_runtime,
            "description": description,
            "capabilities": capabilities
        }

    @staticmethod
    def generate_remediation_roadmap(
        issues: List[Issue],
        summary: Summary,
        metrics: Metrics,
        language: str
    ) -> Dict[str, Any]:
        """
        Constructs a prioritized step-by-step refactoring guide detailing:
        - Why the score is at its current level
        - Where the problems are located (files, line numbers, rules)
        - Exact actionable instructions to fix them
        - Estimated score recovery
        """
        score = summary.quality_score
        total_issues = len(issues)

        # 1. Overall Diagnostic
        if score >= 90:
            diagnostic = "Codebase demonstrates clean architectural hygiene with minimal or no structural risks."
            action_urgency = "LOW — Code is production-ready. Apply routine linting polish if desired."
        elif score >= 75:
            diagnostic = "Good structural baseline, but minor code smells or style inconsistencies were detected."
            action_urgency = "MODERATE — Review highlighted recommendations before merging to production."
        elif score >= 50:
            diagnostic = "Moderate to high risk detected. Code exhibits either security oversights, unhandled error paths, or high branch complexity."
            action_urgency = "HIGH — Refactoring required to prevent runtime exceptions or exploit vectors."
        else:
            diagnostic = "Critical deficiency state. Code contains high-severity security vulnerabilities or severe architectural degradation."
            action_urgency = "URGENT — Immediate remediation required before deployment."

        # 2. Problem Locations Breakdown
        problem_locations = []
        steps = []

        # Sort issues by severity
        crit_issues = [i for i in issues if i.severity == "CRITICAL"]
        high_issues = [i for i in issues if i.severity == "HIGH"]
        med_issues = [i for i in issues if i.severity == "MEDIUM"]
        low_issues = [i for i in issues if i.severity == "LOW"]

        step_counter = 1

        # Process Critical Security
        for iss in crit_issues:
            problem_locations.append({
                "severity": "CRITICAL",
                "location": f"Line {iss.line}",
                "rule": iss.rule,
                "tool": iss.tool,
                "message": iss.message,
                "snippet": iss.source
            })
            steps.append({
                "step": step_counter,
                "title": f"Fix Critical Vulnerability: {iss.rule} (Line {iss.line})",
                "problem": iss.message,
                "solution": iss.suggested_fix or "Refactor code to eliminate unsafe API or unsanitized input execution.",
                "target": f"Line {iss.line}",
                "expected_gain": "+15 to +20 Quality Score points"
            })
            step_counter += 1

        # Process High Issues
        for iss in high_issues:
            problem_locations.append({
                "severity": "HIGH",
                "location": f"Line {iss.line}",
                "rule": iss.rule,
                "tool": iss.tool,
                "message": iss.message,
                "snippet": iss.source
            })
            steps.append({
                "step": step_counter,
                "title": f"Resolve High-Risk Defect: {iss.rule} (Line {iss.line})",
                "problem": iss.message,
                "solution": iss.suggested_fix or "Handle exception boundaries, credential management, or resource lifetimes properly.",
                "target": f"Line {iss.line}",
                "expected_gain": "+8 to +12 Quality Score points"
            })
            step_counter += 1

        # Process Medium / Complexity Issues
        for iss in med_issues[:5]:
            problem_locations.append({
                "severity": "MEDIUM",
                "location": f"Line {iss.line}",
                "rule": iss.rule,
                "tool": iss.tool,
                "message": iss.message,
                "snippet": iss.source
            })
            steps.append({
                "step": step_counter,
                "title": f"Refactor Maintainability / Complexity Issue (Line {iss.line})",
                "problem": iss.message,
                "solution": iss.suggested_fix or "Break large routines into focused sub-functions.",
                "target": f"Line {iss.line}",
                "expected_gain": "+4 to +6 Quality Score points"
            })
            step_counter += 1

        # Check Cyclomatic Complexity
        if metrics.cyclomatic_complexity and metrics.cyclomatic_complexity > 10.0:
            steps.append({
                "step": step_counter,
                "title": f"Reduce Cyclomatic Complexity (Current: {metrics.cyclomatic_complexity})",
                "problem": "Functions have deeply nested conditionals and excessive branch density.",
                "solution": "Decompose nested if/else statements, use guard clauses / early returns, or adopt strategy patterns.",
                "target": "Global Module Architecture",
                "expected_gain": "+10 to +15 Maintainability points"
            })
            step_counter += 1

        if not steps:
            steps.append({
                "step": 1,
                "title": "Maintain High Code Quality Standards",
                "problem": "No critical defects or security risks detected.",
                "solution": "Continue following current code formatting, unit testing, and modular architecture patterns.",
                "target": "Entire File",
                "expected_gain": "Sustains 100/100 Grade A Status"
            })

        projected_score = 100 if not issues else min(100, score + sum(8 for _ in issues))

        return {
            "diagnostic_summary": diagnostic,
            "action_urgency": action_urgency,
            "current_score": score,
            "projected_score": min(100, max(score, projected_score)),
            "problem_locations": problem_locations,
            "refactoring_steps": steps,
            "total_defects_count": total_issues
        }
