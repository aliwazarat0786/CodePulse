# CODEPULSE-AI
> Multi-Language AI-Powered Code Quality, Security & Complexity Analyzer

CodePulse AI is an intelligent llm powered source code inspection platform combining traditional static analysis with an LLM interpretation layer. It detects code quality issues, security vulnerabilities, and complexity across 5 major programming languages and much more.

## Key Features
- Multi-Language Pipeline: Python, Java, C, C++, JavaScript
- Hybrid Analysis: AST structural parsing, Radon complexity, Bandit security, Pylint adapters
- LLM Interpretation: Explains why issues matter, assesses runtime impact, and provides remediated code
- Unified Normalization & Deduplication: Standard CodePulse schema (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- Transparent Quality Score: Weighted 0-100 score
- Cyberpunk UI: Dark-themed, animated, glowing interface with live counters, radial score meter, and code inspector

## Quick Start
```bash
pip install -r requirements.txt
python app.py
```
Visit http://localhost:5000 in your browser.

## Running Tests
```bash
pytest tests/ -v
```
