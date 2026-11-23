"""
REST API routes for CodePulse AI.
Provides endpoints for multi-language static analysis, isolated dynamic execution,
AI-assisted issue fixation, backend verification, side-by-side comparison, and multi-format report exports.
"""
from flask import Blueprint, request, jsonify, Response
from core.orchestrator import AnalysisOrchestrator
from core.report_comparator import ReportComparator
from core.diff_engine import DiffEngine
from reports.generator import ReportGenerator
from utils.code_executor import CodeExecutor
from llm.fixer import AIFixer
from config import Config
import json

api_bp = Blueprint("api", __name__)
orchestrator = AnalysisOrchestrator()
ai_fixer = AIFixer()

# In-memory storage for analysis and comparison reports
REPORT_STORE = {}
COMPARISON_STORE = {}
SESSION_STORE = {}

@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "CodePulse AI",
        "version": "2.0.0"
    }), 200

@api_bp.route("/languages", methods=["GET"])
def get_languages():
    return jsonify({
        "languages": Config.SUPPORTED_LANGUAGES,
        "default": "python"
    }), 200

@api_bp.route("/analyze", methods=["POST"])
def analyze_code():
    data = request.get_json() or {}
    source_code = data.get("source_code", "")
    filename = data.get("filename", "snippet.py")
    language = data.get("language", "auto")
    enable_ai = data.get("enable_ai", True)
    execute_code = data.get("execute_code", False)

    if not source_code.strip():
        return jsonify({
            "status": "error",
            "message": "Source code cannot be empty."
        }), 400

    if len(source_code.encode("utf-8")) > Config.MAX_FILE_SIZE:
        return jsonify({
            "status": "error",
            "message": f"Source code exceeds maximum limit of {Config.MAX_FILE_SIZE} bytes."
        }), 413

    try:
        result = orchestrator.analyze_code(
            source_code=source_code,
            filename=filename,
            requested_language=language,
            enable_ai=enable_ai,
            execute_code=execute_code
        )

        REPORT_STORE[result.analysis_id] = result
        SESSION_STORE[result.analysis_id] = {
            "original_code": source_code,
            "filename": filename,
            "language": result.language,
            "version": 1
        }

        return jsonify({
            "status": "success",
            "analysis": result.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Analysis pipeline failed: {str(e)}"
        }), 500

@api_bp.route("/execute", methods=["POST"])
def execute_code():
    """
    Dedicated endpoint to execute user source code in an isolated sandbox.
    """
    data = request.get_json() or {}
    source_code = data.get("source_code", "")
    language = data.get("language", "auto")
    filename = data.get("filename", "snippet.py")
    timeout_sec = data.get("timeout_sec", 10)

    if not source_code.strip():
        return jsonify({
            "status": "error",
            "message": "Source code cannot be empty."
        }), 400

    if language == "auto" or not language:
        from core.language_detector import detect_language
        language, _, _ = detect_language(filename, source_code, "auto")

    try:
        exec_result = CodeExecutor.execute(
            source_code=source_code,
            language=language,
            filename=filename,
            timeout_sec=timeout_sec
        )
        return jsonify({
            "status": "success",
            "execution": exec_result.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Execution service error: {str(e)}"
        }), 500

@api_bp.route("/analyze-and-run", methods=["POST"])
def analyze_and_run():
    """
    Combined pipeline: Static Analysis + Dynamic Execution + AI Synthesis.
    """
    data = request.get_json() or {}
    source_code = data.get("source_code", "")
    filename = data.get("filename", "snippet.py")
    language = data.get("language", "auto")
    enable_ai = data.get("enable_ai", True)

    if not source_code.strip():
        return jsonify({"status": "error", "message": "Source code cannot be empty."}), 400

    try:
        # Run combined pipeline with execution enabled
        result = orchestrator.analyze_code(
            source_code=source_code,
            filename=filename,
            requested_language=language,
            enable_ai=enable_ai,
            execute_code=True
        )

        REPORT_STORE[result.analysis_id] = result
        SESSION_STORE[result.analysis_id] = {
            "original_code": source_code,
            "filename": filename,
            "language": result.language,
            "version": 1
        }

        return jsonify({
            "status": "success",
            "analysis": result.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Analyze + Run failed: {str(e)}"
        }), 500

@api_bp.route("/ai/fix", methods=["POST"])
def ai_fix_selected():
    """
    Generates AI fix ONLY for user-selected issues, and conducts real backend verification.
    """
    data = request.get_json() or {}
    source_code = data.get("source_code", "")
    language = data.get("language", "python")
    analysis_id = data.get("analysis_id", "")
    selected_issue_ids = data.get("selected_issue_ids", [])
    fix_all = data.get("fix_all", False)

    if not source_code.strip():
        return jsonify({"status": "error", "message": "Source code cannot be empty."}), 400

    orig_result = REPORT_STORE.get(analysis_id)
    orig_issues = orig_result.issues if orig_result else []
    orig_exec = orig_result.execution if orig_result else None

    try:
        candidate_code, fix_results = ai_fixer.generate_fix(
            source_code=source_code,
            language=language,
            issues=orig_issues,
            selected_issue_ids=selected_issue_ids,
            execution_result=orig_exec,
            fix_all=fix_all
        )

        # Conduct real backend verification
        verification = ai_fixer.verify_fix(
            original_code=source_code,
            fixed_code=candidate_code,
            language=language,
            original_issues=orig_issues,
            original_execution=orig_exec,
            orchestrator_instance=orchestrator
        )

        # Generate Diff
        diff_data = DiffEngine.compare_code(source_code, candidate_code).to_dict()

        return jsonify({
            "status": "success",
            "candidate_fixed_code": candidate_code,
            "fix_results": [f.to_dict() for f in fix_results],
            "verification": verification.to_dict(),
            "code_comparison": diff_data
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"AI Fix generation failed: {str(e)}"
        }), 500

@api_bp.route("/ai/fix-all", methods=["POST"])
def ai_fix_all():
    """
    Fixes all fixable issues using AI.
    """
    data = request.get_json() or {}
    data["fix_all"] = True
    return ai_fix_selected()

@api_bp.route("/run-fixed", methods=["POST"])
def run_fixed_code():
    """
    Executes the candidate fixed code independently and returns execution metrics.
    """
    data = request.get_json() or {}
    language = data.get("language", "auto")
    filename = data.get("filename", "fixed_code.py")

    if not fixed_code.strip():
        return jsonify({"status": "error", "message": "Fixed code is empty."}), 400

    if language == "auto" or not language:
        from core.language_detector import detect_language
        language, _, _ = detect_language(filename, fixed_code, "auto")

    try:
        exec_res = CodeExecutor.execute(
            source_code=fixed_code,
            language=language,
            filename=filename
        )
        return jsonify({
            "status": "success",
            "execution": exec_res.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/reanalyze", methods=["POST"])
def reanalyze_code():
    """
    Re-analyzes applied code, executes it, and computes a comprehensive ReportComparison.
    """
    data = request.get_json() or {}
    source_code = data.get("source_code", "")
    original_analysis_id = data.get("original_analysis_id", "")
    original_code = data.get("original_code", "")
    filename = data.get("filename", "reanalyzed.py")
    language = data.get("language", "auto")
    enable_ai = data.get("enable_ai", True)

    if not source_code.strip():
        return jsonify({"status": "error", "message": "Source code is empty."}), 400

    try:
        orig_result = REPORT_STORE.get(original_analysis_id)
        if not orig_result and original_code:
            # Reconstruct baseline original analysis if cache cleared
            orig_result = orchestrator.analyze_code(
                source_code=original_code,
                filename=filename,
                requested_language=language,
                enable_ai=False,
                execute_code=True
            )
            REPORT_STORE[orig_result.analysis_id] = orig_result

        # Run complete re-analysis on new code
        new_result = orchestrator.analyze_code(
            source_code=source_code,
            filename=filename,
            requested_language=language,
            enable_ai=enable_ai,
            execute_code=True,
            version=2,
            parent_analysis_id=original_analysis_id
        )
        REPORT_STORE[new_result.analysis_id] = new_result

        # Compute ReportComparison
        comparison = None
        if orig_result:
            comparison = ReportComparator.compare(
                original_result=orig_result,
                fixed_result=new_result,
                original_code=original_code or orig_result.source_code,
                fixed_code=source_code
            )
            COMPARISON_STORE[comparison.comparison_id] = comparison

        return jsonify({
            "status": "success",
            "new_analysis": new_result.to_dict(),
            "comparison": comparison.to_dict() if comparison else None
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Re-analysis failed: {str(e)}"}), 500

@api_bp.route("/compare-reports", methods=["POST"])
def compare_reports():
    data = request.get_json() or {}
    orig_id = data.get("original_analysis_id")
    fixed_id = data.get("fixed_analysis_id")

    orig_result = REPORT_STORE.get(orig_id)
    fixed_result = REPORT_STORE.get(fixed_id)

    if not orig_result or not fixed_result:
        return jsonify({"status": "error", "message": "Analysis reports not found."}), 404

    comparison = ReportComparator.compare(
        original_result=orig_result,
        fixed_result=fixed_result,
        original_code=orig_result.source_code,
        fixed_code=fixed_result.source_code
    )
    COMPARISON_STORE[comparison.comparison_id] = comparison

    return jsonify({
        "status": "success",
        "comparison": comparison.to_dict()
    }), 200

@api_bp.route("/report/<analysis_id>", methods=["GET"])
def get_report(analysis_id):
    format_type = request.args.get("format", "json").lower()
    is_download = request.args.get("download", "false").lower() in ("true", "1", "yes")
    result = REPORT_STORE.get(analysis_id)

    if not result:
        return jsonify({"status": "error", "message": "Report not found or expired."}), 404

    filename_base = f"CodePulse_Report_{analysis_id}"

    if format_type in ["zip", "package"]:
        # Find if this report has an associated comparison
        matched_comp = None
        for c in COMPARISON_STORE.values():
            if c.original_analysis_id == analysis_id or c.fixed_analysis_id == analysis_id:
                matched_comp = c
                break

        if matched_comp:
            orig = REPORT_STORE.get(matched_comp.original_analysis_id)
            fixed = REPORT_STORE.get(matched_comp.fixed_analysis_id)
            zip_bytes = ReportGenerator.generate_report_package_zip(
                comparison=matched_comp,
                original_result=orig or result,
                fixed_result=fixed or result,
                original_code=(orig or result).source_code or "",
                fixed_code=(fixed or result).source_code or ""
            )
            headers = {"Content-Disposition": f'attachment; filename="CodePulse_Report_Package_{matched_comp.comparison_id}.zip"'}
            return Response(zip_bytes, mimetype="application/zip", headers=headers)
        else:
            zip_bytes = ReportGenerator.generate_single_report_package_zip(result, result.source_code or "")
            headers = {"Content-Disposition": f'attachment; filename="CodePulse_Report_Package_{analysis_id}.zip"'}
            return Response(zip_bytes, mimetype="application/zip", headers=headers)

    elif format_type in ["html", "pdf"]:
        html_content = ReportGenerator.generate_html_report(result)
        headers = {}
        if is_download:
            headers["Content-Disposition"] = f'attachment; filename="{filename_base}.html"'
        return Response(html_content, mimetype="text/html", headers=headers)

    elif format_type in ["doc", "docx", "word"]:
        doc_content = ReportGenerator.generate_doc_report(result)
        headers = {
            "Content-Disposition": f'attachment; filename="{filename_base}.doc"'
        }
        return Response(doc_content, mimetype="application/msword", headers=headers)

    elif format_type in ["md", "markdown"]:
        md_content = ReportGenerator.generate_markdown_report(result)
        headers = {}
        if is_download:
            headers["Content-Disposition"] = f'attachment; filename="{filename_base}.md"'
        return Response(md_content, mimetype="text/markdown", headers=headers)

    else:
        json_data = result.to_dict()
        if is_download:
            json_str = json.dumps(json_data, indent=2)
            headers = {"Content-Disposition": f'attachment; filename="{filename_base}.json"'}
            return Response(json_str, mimetype="application/json", headers=headers)
        return jsonify(json_data), 200

@api_bp.route("/report/comparison/<comparison_id>", methods=["GET"])
def get_comparison_report(comparison_id):
    format_type = request.args.get("format", "html").lower()
    is_download = request.args.get("download", "false").lower() in ("true", "1", "yes")
    comparison = COMPARISON_STORE.get(comparison_id)

    if not comparison:
        return jsonify({"status": "error", "message": "Comparison report not found."}), 404

    filename_base = f"CodePulse_Comparison_{comparison_id}"

    if format_type in ["zip", "package"]:
        orig_result = REPORT_STORE.get(comparison.original_analysis_id)
        fixed_result = REPORT_STORE.get(comparison.fixed_analysis_id)
        zip_bytes = ReportGenerator.generate_report_package_zip(
            comparison=comparison,
            original_result=orig_result,
            fixed_result=fixed_result,
            original_code=(orig_result.source_code if orig_result else ""),
            fixed_code=(fixed_result.source_code if fixed_result else "")
        )
        headers = {"Content-Disposition": f'attachment; filename="CodePulse_Report_Package_{comparison_id}.zip"'}
        return Response(zip_bytes, mimetype="application/zip", headers=headers)

    elif format_type in ["html", "pdf"]:
        html_content = ReportGenerator.generate_comparison_html_report(comparison)
        headers = {}
        if is_download:
            headers["Content-Disposition"] = f'attachment; filename="{filename_base}.html"'
        return Response(html_content, mimetype="text/html", headers=headers)

    elif format_type in ["doc", "docx", "word"]:
        doc_content = ReportGenerator.generate_comparison_doc_report(comparison)
        headers = {"Content-Disposition": f'attachment; filename="{filename_base}.doc"'}
        return Response(doc_content, mimetype="application/msword", headers=headers)

    elif format_type in ["md", "markdown"]:
        md_content = ReportGenerator.generate_comparison_markdown_report(comparison)
        headers = {}
        if is_download:
            headers["Content-Disposition"] = f'attachment; filename="{filename_base}.md"'
        return Response(md_content, mimetype="text/markdown", headers=headers)

    else:
        json_data = comparison.to_dict()
        if is_download:
            json_str = json.dumps(json_data, indent=2)
            headers = {"Content-Disposition": f'attachment; filename="{filename_base}.json"'}
            return Response(json_str, mimetype="application/json", headers=headers)
        return jsonify(json_data), 200

@api_bp.route("/report/download-all/<comparison_id>", methods=["GET"])
def download_all_reports_package(comparison_id):
    """
    Packages Original Report, Fixed Report, Comparison Report, and source codes into a single ZIP.
    """
    comparison = COMPARISON_STORE.get(comparison_id)
    if not comparison:
        return jsonify({"status": "error", "message": "Comparison report not found."}), 404

    orig_result = REPORT_STORE.get(comparison.original_analysis_id)
    fixed_result = REPORT_STORE.get(comparison.fixed_analysis_id)

    if not orig_result or not fixed_result:
        return jsonify({"status": "error", "message": "Referenced analysis reports expired."}), 404

    orig_code = orig_result.source_code or ""
    fixed_code = fixed_result.source_code or ""

    zip_bytes = ReportGenerator.generate_report_package_zip(
        comparison=comparison,
        original_result=orig_result,
        fixed_result=fixed_result,
        original_code=orig_code,
        fixed_code=fixed_code
    )

    headers = {
        "Content-Disposition": f'attachment; filename="CodePulse_Report_Package_{comparison_id}.zip"'
    }
    return Response(zip_bytes, mimetype="application/zip", headers=headers)

@api_bp.route("/sample/<language>", methods=["GET"])
def get_sample_code(language):
    samples = {
        "python": """def calculate(a, b):
    # Syntax issue: missing closing parenthesis
    result = a / b
    print(result

calculate(10, 0)
""",
        "java": """package com.example;
import java.util.*;

public class PaymentProcessor {
    private String apiKey = "sk_live_998877665544332211";

    public void executeTransaction(String input) {
        try {
            System.out.println("Processing transaction: " + input);
        } catch (Exception e) {
            // Empty catch block hides critical errors
        }
    }
}
""",
        "c": """#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void read_input() {
    char buffer[64];
    // Insecure gets allows buffer overflow
    gets(buffer);
    
    char dest[32];
    strcpy(dest, buffer);
    
    int* leak = (int*)malloc(sizeof(int) * 100);
    // Missing free(leak)
}

int main() {
    read_input();
    return 0;
}
""",
        "cpp": """#include <iostream>
using namespace std;

class DatabaseManager {
public:
    void connect() {
        int* raw_ptr = new int(100);
        // Raw pointer without smart pointer
        char* null_val = NULL;
        
        int count = (int)3.14159; // C-style cast
    }
};
""",
        "javascript": """var secret_key = "12345-token";

function handleLogin(payload) {
    // eval execution vulnerability
    var parsed = eval("(" + payload + ")");
    
    if (payload == "admin") {
        console.log("Logged in as admin");
    }
    
    return parsed;
}
""",
        "sql": """-- PostgreSQL Database Schema & PL/pgSQL Function
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL, -- Storing plaintext password
    email VARCHAR(100) NOT NULL
);

-- Unbounded Dangerous Delete
DELETE FROM users;

-- Insecure Dynamic SQL Concatenation in PL/pgSQL
CREATE OR REPLACE FUNCTION search_users(user_query TEXT) 
RETURNS SETOF users AS $$
BEGIN
    -- Dynamic concatenation susceptible to SQL Injection
    RETURN QUERY EXECUTE 'SELECT * FROM users WHERE username = ' || user_query;
END;
$$ LANGUAGE plpgsql;

-- Dangerous Privilege Escalation
GRANT ALL PRIVILEGES ON DATABASE production_db TO PUBLIC;
""",
        "react": """import React, { useState, useEffect } from 'react';

export default function UserProfileWidget({ userData, htmlBio }) {
    const [theme, setTheme] = useState('dark');

    return (
        <div className="profile-container">
            <h3>User: {userData.name}</h3>
            
            {/* Dangerous Unescaped HTML Rendering (XSS) */}
            <div 
                className="bio-section"
                dangerouslySetInnerHTML={{ __html: htmlBio }} 
            />

            {/* Insecure javascript: pseudo-protocol */}
            <a href="javascript:alert('Executing JS URI')">Click to refresh profile</a>
        </div>
    );
}
""",
        "node_mongo": """const express = require('express');
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');
const { exec } = require('child_process');

const app = express();
app.use(express.json());

const JWT_SECRET = "super_hardcoded_jwt_secret_token_12345";

// MongoDB Model
const User = mongoose.model('User', { username: String, role: String });

// NoSQL $where injection & Auth bypass
app.post('/api/login', async (req, res) => {
    // Unsanitized query with $where allows arbitrary JS code execution on MongoDB
    const user = await User.findOne({
        $where: `this.username == '${req.body.username}'`
    });
    
    if (user) {
        const token = jwt.sign({ id: user._id }, JWT_SECRET);
        return res.json({ token });
    }
    res.status(401).json({ error: "Invalid credentials" });
});

// Remote Command Injection
app.get('/api/ping', (req, res) => {
    exec("ping -c 1 " + req.query.host, (err, stdout) => {
        res.send(stdout);
    });
});
""",
        "django_flask": """import os
from flask import Flask, request, render_template_string
from django.utils.safestring import mark_safe
import sqlite3

app = Flask(__name__)
app.secret_key = "insecure_dev_secret_key"

# Flask Server-Side Template Injection (SSTI)
@app.route('/greet')
def greet():
    name = request.args.get('name', 'Guest')
    template = f"<h2>Hello {name}!</h2>"
    return render_template_string(template)

# Django / SQL Injection simulation
def get_user_records(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # Direct SQL query string formatting
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchall()

if __name__ == '__main__':
    app.run(debug=True)
"""
    }

    code = samples.get(language.lower(), samples["python"])
    return jsonify({
        "language": language,
        "code": code
    }), 200
