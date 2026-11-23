"""
Curated Multi-Language Code Vulnerability & Quality Dataset.
Covers CWE-78, CWE-89, CWE-120, CWE-798, CWE-94, CWE-400, and Clean Code standards.
"""
import json
import os
from pathlib import Path

DATASET_FILE = Path(__file__).resolve().parent / "data" / "vulnerability_dataset.json"

RAW_DATASET = [
    # --- SECURITY VULNERABILITIES (CWE-94, CWE-78, CWE-120, CWE-798, CWE-89) ---
    {"code": "def execute(user_input): return eval(user_input)", "language": "python", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-94", "type": "Code Injection"},
    {"code": "import subprocess\ndef run(cmd): subprocess.run(cmd, shell=True)", "language": "python", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-78", "type": "Command Injection"},
    {"code": "password = 'admin_super_secret_key_12345'\ndef login(): pass", "language": "python", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-798", "type": "Hardcoded Secret"},
    {"code": "import sqlite3\ndef get_user(db, name): return db.execute(f'SELECT * FROM users WHERE name = {name}')", "language": "python", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-89", "type": "SQL Injection"},
    {"code": "import pickle\ndef deserialize(data): return pickle.loads(data)", "language": "python", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-502", "type": "Unsafe Deserialization"},
    {"code": "import hashlib\ndef hash_pass(pwd): return hashlib.md5(pwd.encode()).hexdigest()", "language": "python", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-327", "type": "Weak Cryptography"},
    
    # C / C++ Vulnerabilities
    {"code": "void read_data() { char buf[32]; gets(buf); }", "language": "c", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-120", "type": "Buffer Overflow"},
    {"code": "void copy(char* src) { char dest[16]; strcpy(dest, src); }", "language": "c", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-120", "type": "Buffer Overflow"},
    {"code": "void log_msg(char* user) { char out[64]; sprintf(out, user); }", "language": "c", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-134", "type": "Format String"},
    {"code": "void leak_memory() { int* ptr = (int*)malloc(1024); if (!ptr) return; }", "language": "c", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-401", "type": "Memory Leak"},
    {"code": "void ptr_leak() { char* p = new char[256]; throw std::runtime_error('error'); }", "language": "cpp", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-401", "type": "Exception Leak"},
    
    # Java Vulnerabilities
    {"code": "public class App { private String apiKey = 'sk_live_123456789abcdef'; }", "language": "java", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-798", "type": "Hardcoded Secret"},
    {"code": "public void parse(String xml) { DocumentBuilder db = DocumentBuilderFactory.newInstance().newDocumentBuilder(); db.parse(xml); }", "language": "java", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-611", "type": "XXE Injection"},
    {"code": "public void query(Statement stmt, String id) { stmt.executeQuery('SELECT * FROM acc WHERE id=' + id); }", "language": "java", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-89", "type": "SQL Injection"},
    {"code": "public void silentFail() { try { File.createTempFile('a', 'b'); } catch(Exception e) {} }", "language": "java", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-390", "type": "Empty Catch"},

    # JavaScript Vulnerabilities
    {"code": "function run(data) { return eval('(' + data + ')'); }", "language": "javascript", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-94", "type": "Code Injection"},
    {"code": "function auth(user, pass) { var token = 'secret_jwt_token_9999'; }", "language": "javascript", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-798", "type": "Hardcoded Secret"},
    {"code": "function query(input) { document.getElementById('view').innerHTML = input; }", "language": "javascript", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-79", "type": "Cross Site Scripting"},

    # --- SQL & DATABASE VULNERABILITIES ---
    {"code": "CREATE FUNCTION run_query(val TEXT) RETURNS VOID AS $$ BEGIN EXECUTE 'SELECT * FROM users WHERE name = ' || val; END; $$ LANGUAGE plpgsql;", "language": "sql", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-89", "type": "Dynamic SQL Injection"},
    {"code": "DELETE FROM users;", "language": "sql", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-400", "type": "Unbounded Table Deletion"},
    {"code": "GRANT ALL PRIVILEGES ON DATABASE prod_db TO PUBLIC;", "language": "sql", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-732", "type": "Excessive Privileges"},
    {"code": "CREATE TABLE auth_accounts ( id INT, password VARCHAR(255) );", "language": "sql", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-256", "type": "Plaintext Password Column"},

    # --- REACT, NEXT.JS & NODE.JS VULNERABILITIES ---
    {"code": "function Component({ bio }) { return <div dangerouslySetInnerHTML={{ __html: bio }} />; }", "language": "javascript", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-79", "type": "React dangerouslySetInnerHTML XSS"},
    {"code": "app.get('/ping', (req, res) => { exec('ping -c 1 ' + req.query.host, (e, out) => res.send(out)); });", "language": "javascript", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-78", "type": "Node.js Command Injection"},
    {"code": "app.post('/auth', async (req, res) => { const u = await User.findOne({ $where: `this.name == '${req.body.name}'` }); });", "language": "javascript", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-943", "type": "MongoDB NoSQL Where Injection"},

    # --- DJANGO & FLASK VULNERABILITIES ---
    {"code": "@app.route('/view')\ndef view(): return render_template_string(f'<h1>{request.args.get(\"name\")}</h1>')", "language": "python", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-1336", "type": "Flask Template Injection SSTI"},
    {"code": "def query_db(uid): return User.objects.raw(f'SELECT * FROM users WHERE id = {uid}')", "language": "python", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-89", "type": "Django Raw SQL Injection"},
    {"code": "SECRET_KEY = 'django-insecure-999888777666555444333222111'\nDEBUG = True", "language": "python", "label": "SECURITY_VULNERABILITY", "cwe": "CWE-798", "type": "Hardcoded Django Secret"},

    # --- CLEAN SQL & FRAMEWORK CODE ---
    {"code": "CREATE TABLE users (\n    id SERIAL PRIMARY KEY,\n    username VARCHAR(50) UNIQUE NOT NULL,\n    password_hash VARCHAR(255) NOT NULL,\n    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP\n);\nCREATE INDEX idx_users_username ON users(username);", "language": "sql", "label": "CLEAN_CODE", "cwe": "None", "type": "Clean SQL Schema"},
    {"code": "CREATE OR REPLACE FUNCTION get_user_by_id(user_id INT)\nRETURNS TABLE(id INT, username VARCHAR)\nLANGUAGE plpgsql\nAS $$\nBEGIN\n    RETURN QUERY SELECT u.id, u.username FROM users u WHERE u.id = user_id;\nEND;\n$$;", "language": "sql", "label": "CLEAN_CODE", "cwe": "None", "type": "Parameterized PLpgSQL"},
    {"code": "import React, { useState } from 'react';\nexport default function Counter() {\n    const [count, setCount] = useState(0);\n    return <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>;\n}", "language": "javascript", "label": "CLEAN_CODE", "cwe": "None", "type": "Clean React Component"},
    {"code": "const express = require('express');\nconst app = express();\napp.use(express.json({ limit: '10kb' }));\napp.get('/api/status', (req, res) => res.json({ status: 'ok' }));", "language": "javascript", "label": "CLEAN_CODE", "cwe": "None", "type": "Clean Express App"},
    {"code": "from flask import Flask, jsonify, request\napp = Flask(__name__)\n@app.route('/api/calc', methods=['POST'])\ndef calc():\n    data = request.get_json() or {}\n    return jsonify({'result': data.get('val', 0) * 2})", "language": "python", "label": "CLEAN_CODE", "cwe": "None", "type": "Clean Flask Microservice"}
]

def generate_dataset():
    """Augments dataset with variations and writes to JSON."""
    os.makedirs(DATASET_FILE.parent, exist_ok=True)
    
    # Generate variations
    expanded = []
    for item in RAW_DATASET:
        expanded.append(item)
        # Add slight structural variations
        if item["language"] == "python":
            expanded.append({
                "code": "# Helper function\n" + item["code"] + "\n# End routine",
                "language": "python",
                "label": item["label"],
                "cwe": item["cwe"],
                "type": item["type"]
            })
        elif item["language"] == "javascript":
            expanded.append({
                "code": "// Clean client module\n" + item["code"] + "\n// End module",
                "language": "javascript",
                "label": item["label"],
                "cwe": item["cwe"],
                "type": item["type"]
            })
        elif item["language"] in ["c", "cpp"]:
            expanded.append({
                "code": "/* Header comment */\n" + item["code"],
                "language": item["language"],
                "label": item["label"],
                "cwe": item["cwe"],
                "type": item["type"]
            })

    with open(DATASET_FILE, "w", encoding="utf-8") as f:
        json.dump(expanded, f, indent=2)

    print(f"Dataset generated with {len(expanded)} samples at {DATASET_FILE}")
    return expanded

if __name__ == "__main__":
    generate_dataset()

