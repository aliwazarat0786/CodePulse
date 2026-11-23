"""
Report generator for CodePulse AI.
Supports Single-File Reports and Full Comparison Reports across:
- PDF (printable HTML with print trigger)
- Word Document (.doc XML format)
- Markdown (.md)
- HTML (.html)
- JSON (.json)
- Full ZIP Package (.zip) with all reports & source code
"""
import io
import zipfile
import json
from typing import Dict, Any, Optional
from models.schemas import AnalysisResult, ReportComparison

class ReportGenerator:
    @staticmethod
    def generate_json_report(result: AnalysisResult) -> str:
        return json.dumps(result.to_dict(), indent=2)

    @staticmethod
    def generate_markdown_report(result: AnalysisResult) -> str:
        data = result.to_dict()
        summary = data["summary"]
        metrics = data["metrics"]
        issues = data["issues"]
        exec_info = data.get("execution") or {}
        ml = data.get("ml_prediction") or {}
        purpose = data.get("code_purpose") or {}
        roadmap = data.get("refactoring_roadmap") or {}

        caps = ", ".join(purpose.get("capabilities", [])) or "Standard module execution"

        exec_md = ""
        if exec_info:
            exec_md = f"""
---

## ⚡ Execution Output & Diagnostics
- **Status:** `{exec_info.get('status', 'SUCCESS')}` (Exit Code: `{exec_info.get('exit_code', 0)}`, Duration: `{exec_info.get('execution_time', 0.0)}s`)
- **Stdout:**
```text
{exec_info.get('stdout') or '// No stdout produced'}
```
- **Stderr / Diagnostics:**
```text
{exec_info.get('stderr') or '// Clean execution - No errors'}
```
"""

        md = f"""# CodePulse AI — Code Quality & Security Audit Report

**Analysis ID:** `{data['analysis_id']}`  
**Target File:** `{data['filename']}`  
**Language:** `{data['language'].upper()}`  
**Generated At:** `{data['timestamp']}`  
**Version:** `{data.get('version', 1)}`
{exec_md}
---

## 🏛️ Code Architecture & Semantic Purpose
- **Inferred Role:** **{purpose.get('purpose_title', 'General Utility Module')}**
- **Domain:** {purpose.get('domain', 'Software Engineering')}
- **Target Runtime:** {purpose.get('target_runtime', 'Standard Environment')}
- **Overview:** {purpose.get('description', 'Analyzed source code file.')}
- **Key Capabilities:** {caps}

---

## 📊 Executive Telemetry & Metrics
- **Code Quality Score:** **{summary['quality_score']} / 100** (Grade {summary['score_grade']})
- **Overall Verdict:** {summary['verdict']}
- **Total Issues Detected:** {summary['total_issues']} (Critical: {summary['critical']}, High: {summary['high']}, Medium: {summary['medium']}, Low: {summary['low']})
- **Lines of Code:** {metrics['lines_of_code']}
- **Cyclomatic Complexity:** {metrics['cyclomatic_complexity']} (Avg per function)
- **Maintainability Index:** {metrics['maintainability_index']} / 100
- **ML Vulnerability Classification:** `{ml.get('predicted_label', 'CLEAN_CODE')}` (Risk Score: `{int((ml.get('risk_score', 0.1))*100)}%`)

---

## 🛠️ Actionable Remediation & Refactoring Roadmap
- **Diagnostic Review:** {roadmap.get('diagnostic_summary', 'Code health reviewed.')}
- **Action Urgency:** `{roadmap.get('action_urgency', 'LOW')}`
- **Projected Recovery Score:** **{roadmap.get('projected_score', 100)} / 100**

### Prioritized Step-by-Step Changes:
"""
        steps = roadmap.get("refactoring_steps", [])
        if not steps:
            md += "\n> ✨ **No refactoring required.** Code is in clean, production-ready state.\n"
        else:
            for s in steps:
                md += f"""
#### Step {s['step']}: {s['title']}
- **Root Cause / Problem:** {s['problem']}
- **Required Action:** {s['solution']}
- **Target Location:** `{s['target']}`
- **Expected Score Gain:** `{s['expected_gain']}`
"""

        md += f"""
---

## 🔎 Detailed Findings Breakdown ({len(issues)})
"""
        if not issues:
            md += "\n> ✨ **Zero Deficiencies Detected.** Source code adheres to high quality and security benchmarks.\n"
        else:
            for idx, iss in enumerate(issues, start=1):
                ai = iss.get("ai_analysis") or {}
                md += f"""
### {idx}. [{iss['severity']}] {iss['message']}
- **File:** `{iss['file']}` (Line {iss['line']}, Column {iss.get('column', 0)})
- **Error Type:** `{iss.get('error_type', 'GENERAL')}` | **Tool:** `{iss['tool']}`
- **Source Code Snippet:**
```{data['language']}
{iss.get('source') or '// Source line context'}
```
- **Why it matters:** {ai.get('explanation', 'Static analysis flagged this pattern.')}
- **Potential Impact:** {ai.get('impact', 'System maintainability or runtime reliability.')}
- **Recommended Action:** {ai.get('recommendation', iss.get('suggested_fix', 'Refactor according to language standards.'))}
"""
                if ai.get('fixed_code'):
                    md += f"""- **Corrected Code:**
```{data['language']}
{ai.get('fixed_code')}
```
"""
        md += f"\n---\n*Disclaimer: {summary['disclaimer']}*\n"
        return md

    @staticmethod
    def generate_html_report(result: AnalysisResult) -> str:
        data = result.to_dict()
        summary = data["summary"]
        metrics = data["metrics"]
        issues = data["issues"]
        exec_info = data.get("execution") or {}
        purpose = data.get("code_purpose") or {}
        roadmap = data.get("refactoring_roadmap") or {}

        caps_html = "".join(f"<span style='background:#e2e8f0;color:#0f172a;padding:2px 8px;border-radius:4px;font-size:12px;margin-right:6px;'>{c}</span>" for c in purpose.get("capabilities", []))

        exec_box = ""
        if exec_info:
            status_color = "#10b981" if exec_info.get("status") == "SUCCESS" else "#ef4444"
            exec_box = f"""
            <div style="background:#0f172a;border:1px solid #334155;border-radius:8px;padding:16px;margin-bottom:20px;color:#f8fafc;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-weight:600;font-size:14px;color:#94a3b8;">⚡ Execution Terminal Output</span>
                    <span style="background:{status_color};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">{exec_info.get('status')} (Exit: {exec_info.get('exit_code')})</span>
                </div>
                <div style="font-size:12px;color:#64748b;margin-bottom:8px;">Execution Duration: <strong>{exec_info.get('execution_time', 0.0)}s</strong></div>
                <div style="font-size:11px;color:#94a3b8;margin-bottom:2px;">STDOUT:</div>
                <pre style="background:#020617;padding:10px;border-radius:4px;font-family:monospace;font-size:12px;color:#38bdf8;margin:0 0 8px 0;overflow-x:auto;"><code>{exec_info.get('stdout') or '// No stdout produced'}</code></pre>
                {f'<div style="font-size:11px;color:#f87171;margin-bottom:2px;">STDERR / TRACEBACK:</div><pre style="background:#020617;padding:10px;border-radius:4px;font-family:monospace;font-size:12px;color:#f87171;margin:0;overflow-x:auto;"><code>{exec_info.get("stderr")}</code></pre>' if exec_info.get("stderr") else ''}
            </div>
            """

        steps_html = ""
        for s in roadmap.get("refactoring_steps", []):
            steps_html += f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px;margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                    <strong style="color:#0f172a;font-size:14px;">Step {s['step']}: {s['title']}</strong>
                    <span style="background:#dcfce7;color:#16a34a;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">{s['expected_gain']}</span>
                </div>
                <div style="font-size:13px;color:#334155;margin-bottom:2px;"><strong>Problem:</strong> {s['problem']}</div>
                <div style="font-size:13px;color:#64748b;"><strong>Action:</strong> {s['solution']} &bull; <em>Target: {s['target']}</em></div>
            </div>
            """

        issues_html = ""
        for iss in issues:
            ai = iss.get("ai_analysis") or {}
            ai_box = ""
            if ai:
                fixed_box = f"<pre style='background:#f1f5f9;color:#0f172a;padding:10px;border-radius:6px;overflow-x:auto;font-family:monospace;font-size:13px;border:1px solid #cbd5e1;'><code>{ai.get('fixed_code', '')}</code></pre>" if ai.get("fixed_code") else ""
                ai_box = f"""
                <div style="background:#f8fafc;padding:12px;border-radius:6px;margin-top:10px;border-left:3px solid #2563eb;">
                    <div style="color:#2563eb;font-weight:bold;font-size:13px;margin-bottom:4px;">🤖 AI Explanation &amp; Recommendation:</div>
                    <p style="margin:4px 0;font-size:13px;color:#334155;"><strong>Why it matters:</strong> {ai.get('explanation', '')}</p>
                    <p style="margin:4px 0;font-size:13px;color:#334155;"><strong>Impact:</strong> {ai.get('impact', '')}</p>
                    <p style="margin:4px 0;font-size:13px;color:#334155;"><strong>Recommendation:</strong> {ai.get('recommendation', '')}</p>
                    {fixed_box}
                </div>
                """

            issues_html += f"""
            <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-bottom:14px;page-break-inside:avoid;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-weight:600;font-size:15px;color:#0f172a;">{iss['id']}: {iss['message']}</span>
                    <span style="padding:3px 10px;border-radius:4px;font-size:12px;font-weight:bold;background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;">{iss['severity']}</span>
                </div>
                <div style="color:#64748b;font-size:12px;margin-bottom:8px;font-family:monospace;">
                    File: <strong>{iss['file']}</strong> &bull; Line: <strong>{iss['line']}</strong> &bull; Error Type: <strong>{iss.get('error_type', 'GENERAL')}</strong> &bull; Tool: <strong>{iss['tool']}</strong>
                </div>
                <div style="background:#0f172a;color:#f8fafc;padding:8px 12px;border-radius:4px;font-family:monospace;font-size:13px;">
                    {iss['source'] or '// No source snippet'}
                </div>
                {ai_box}
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CodePulse AI Audit Report - {data['analysis_id']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#f8fafc; color:#0f172a; margin:0; padding:24px; }}
        .container {{ max-width: 920px; margin:0 auto; background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:32px; box-shadow:0 4px 16px rgba(0,0,0,0.06); }}
        .header {{ border-bottom:1px solid #e2e8f0; padding-bottom:16px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center; }}
        .title {{ font-size:24px; font-weight:bold; color:#0f172a; margin:0; }}
        .meta {{ color:#64748b; font-size:13px; margin-top:4px; }}
        .score-row {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:24px; }}
        .metric-box {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px; text-align:center; }}
        .metric-val {{ font-size:26px; font-weight:bold; color:#2563eb; }}
        .metric-lbl {{ font-size:12px; color:#64748b; margin-top:2px; font-weight:500; }}
        .section-title {{ font-size:18px; font-weight:600; color:#0f172a; margin:24px 0 12px 0; border-bottom:1px solid #e2e8f0; padding-bottom:6px; }}
        @media print {{
            body {{ padding:0; background:#fff; }}
            .container {{ border:none; box-shadow:none; padding:0; }}
            .no-print {{ display:none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 class="title">CodePulse AI — Quality &amp; Security Report</h1>
                <div class="meta">Analysis ID: <strong>{data['analysis_id']}</strong> &bull; Generated: {data['timestamp']} &bull; Language: <strong>{data['language'].upper()}</strong></div>
            </div>
            <button class="no-print" onclick="window.print()" style="background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;font-weight:600;cursor:pointer;">🖨️ Print / Save PDF</button>
        </div>

        <div class="score-row">
            <div class="metric-box">
                <div class="metric-val" style="color:#10b981;">{summary['quality_score']}/100</div>
                <div class="metric-lbl">Quality Score ({summary['score_grade']})</div>
            </div>
            <div class="metric-box">
                <div class="metric-val" style="color:#ef4444;">{summary['critical']}</div>
                <div class="metric-lbl">Critical Issues</div>
            </div>
            <div class="metric-box">
                <div class="metric-val" style="color:#f59e0b;">{summary['high']}</div>
                <div class="metric-lbl">High Issues</div>
            </div>
            <div class="metric-box">
                <div class="metric-val">{metrics['lines_of_code']}</div>
                <div class="metric-lbl">Lines of Code</div>
            </div>
        </div>

        {exec_box}

        <!-- Code Purpose & Domain Architecture -->
        <div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;padding:16px;margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <strong style="color:#0f172a;font-size:15px;">🏛️ Architectural Purpose: {purpose.get('purpose_title', 'Module Analysis')}</strong>
                <span style="background:#2563eb;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">{data['language'].upper()}</span>
            </div>
            <div style="font-size:12px;color:#64748b;margin-bottom:8px;">Domain: <strong>{purpose.get('domain', 'Software Engineering')}</strong> &bull; Target Runtime: <strong>{purpose.get('target_runtime', 'Standard')}</strong></div>
            <p style="font-size:13px;color:#334155;margin:0 0 10px 0;line-height:1.5;">{purpose.get('description', '')}</p>
            <div style="font-size:12px;"><strong>Capabilities:</strong> {caps_html or 'Standard algorithmic routines'}</div>
        </div>

        <!-- Actionable Refactoring Roadmap -->
        <h2 class="section-title">🛠️ Actionable Remediation &amp; Refactoring Roadmap</h2>
        <div style="background:#fffbeb;border:1px solid #fef3c7;border-left:4px solid #f59e0b;border-radius:6px;padding:12px;margin-bottom:16px;">
            <div style="color:#b45309;font-weight:600;font-size:13px;margin-bottom:4px;">Diagnostic Assessment:</div>
            <div style="font-size:13px;color:#78350f;">{roadmap.get('diagnostic_summary', 'Code health analyzed.')}</div>
        </div>
        {steps_html or "<p style='color:#16a34a;font-size:13px;'>Code adheres to high quality standards. No refactoring required.</p>"}

        <h2 class="section-title">🔎 Findings Breakdown ({len(issues)})</h2>
        {issues_html or "<p style='color:#10b981;font-weight:500;'>No issues found. Code satisfies quality standards.</p>"}

        <div style="margin-top:30px;padding-top:14px;border-top:1px solid #e2e8f0;font-size:11px;color:#94a3b8;text-align:center;">
            {summary['disclaimer']}
        </div>
    </div>
</body>
</html>
"""
        return html

    @staticmethod
    def generate_doc_report(result: AnalysisResult) -> str:
        html = ReportGenerator.generate_html_report(result)
        doc_wrapper = f"""<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head>
<meta charset="utf-8">
<!--[if gte mso 9]>
<xml>
<w:WordDocument>
<w:View>Print</w:View>
<w:Zoom>100</w:Zoom>
<w:DoNotOptimizeForBrowser/>
</w:WordDocument>
</xml>
<![endif]-->
</head>
<body>
{html}
</body>
</html>
"""
        return doc_wrapper

    # --- Comparison Reports ---
    @staticmethod
    def generate_comparison_json_report(comparison: ReportComparison) -> str:
        return json.dumps(comparison.to_dict(), indent=2)

    @staticmethod
    def generate_comparison_markdown_report(comparison: ReportComparison) -> str:
        data = comparison.to_dict()
        m_comp = data.get("metrics_comparison", {})
        
        md = f"""# CodePulse AI — Code Fix Verification & Comparison Audit Report

**Comparison ID:** `{data['comparison_id']}`  
**Original Analysis ID:** `{data['original_analysis_id']}`  
**Fixed Analysis ID:** `{data['fixed_analysis_id']}`  
**Generated At:** `{data['timestamp']}`  

---

## 📈 Executive Quality Score & Fix Recovery
- **Original Quality Score:** **{data['score_before']} / 100** (Grade {data['grade_before']})
- **New Quality Score:** **{data['score_after']} / 100** (Grade {data['grade_after']})
- **Score Delta:** **{'+' if data['score_delta'] >= 0 else ''}{data['score_delta']} Points**
- **Total Issues:** `{data['total_issues_before']} ➔ {data['total_issues_after']}`

---

## 📊 Metrics Delta Telemetry
| Metric | Before | After | Delta |
| :--- | :---: | :---: | :---: |
"""
        for k, v in m_comp.items():
            delta_str = f"{'+' if v.get('delta', 0) > 0 else ''}{v.get('delta', 0)}"
            md += f"| **{v.get('label', k)}** | {v.get('before')} | {v.get('after')} | `{delta_str}` |\n"

        md += f"""
---

## ✅ Resolved Issues ({len(data.get('resolved_issues', []))})
"""
        if not data.get("resolved_issues"):
            md += "\n*No issues resolved.*\n"
        else:
            for iss in data["resolved_issues"]:
                md += f"- **[RESOLVED]** `{iss.get('id')}` (Line {iss.get('line')}): {iss.get('message')}\n"

        md += f"""
---

## ⚠️ Remaining Issues ({len(data.get('remaining_issues', []))})
"""
        if not data.get("remaining_issues"):
            md += "\n*Zero remaining issues. Codebase is clean.*\n"
        else:
            for iss in data["remaining_issues"]:
                md += f"- **[REMAINING]** `{iss.get('id')}` (Line {iss.get('line')}): {iss.get('message')}\n"

        md += f"""
---

## 🚨 Newly Introduced Issues ({len(data.get('new_issues', []))})
"""
        if not data.get("new_issues"):
            md += "\n> ✨ **Zero Regression Detected.** No new issues were introduced by the AI fix.\n"
        else:
            for iss in data["new_issues"]:
                md += f"- **[NEW REGRESSION]** `{iss.get('id')}` (Line {iss.get('line')}): {iss.get('message')}\n"

        return md

    @staticmethod
    def generate_comparison_html_report(comparison: ReportComparison) -> str:
        data = comparison.to_dict()
        m_comp = data.get("metrics_comparison", {})

        metrics_rows = ""
        for k, v in m_comp.items():
            delta_val = v.get('delta', 0)
            color = "#10b981" if v.get("improved", True) else "#ef4444"
            delta_str = f"{'+' if delta_val > 0 else ''}{delta_val}"
            metrics_rows += f"""
            <tr style="border-bottom:1px solid #e2e8f0;">
                <td style="padding:10px;font-weight:500;">{v.get('label', k)}</td>
                <td style="padding:10px;text-align:center;">{v.get('before')}</td>
                <td style="padding:10px;text-align:center;font-weight:bold;">{v.get('after')}</td>
                <td style="padding:10px;text-align:center;color:{color};font-weight:600;">{delta_str}</td>
            </tr>
            """

        resolved_html = "".join(f"<li style='margin-bottom:6px;'><strong>✓ {i.get('id')}</strong> (Line {i.get('line')}): {i.get('message')}</li>" for i in data.get("resolved_issues", []))
        remaining_html = "".join(f"<li style='margin-bottom:6px;'><strong>⚠ {i.get('id')}</strong> (Line {i.get('line')}): {i.get('message')}</li>" for i in data.get("remaining_issues", []))
        new_html = "".join(f"<li style='margin-bottom:6px;color:#ef4444;'><strong>! {i.get('id')}</strong> (Line {i.get('line')}): {i.get('message')}</li>" for i in data.get("new_issues", []))

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CodePulse AI Comparison Report - {data['comparison_id']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#f8fafc; color:#0f172a; margin:0; padding:24px; }}
        .container {{ max-width: 920px; margin:0 auto; background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:32px; box-shadow:0 4px 16px rgba(0,0,0,0.06); }}
        .header {{ border-bottom:1px solid #e2e8f0; padding-bottom:16px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center; }}
        .score-box-wrap {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; margin-bottom:24px; text-align:center; }}
        .card-val {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:16px; }}
        .val-num {{ font-size:28px; font-weight:bold; color:#0f172a; }}
        .val-sub {{ font-size:12px; color:#64748b; margin-top:2px; }}
        table {{ width:100%; border-collapse:collapse; margin-bottom:24px; font-size:13px; }}
        th {{ background:#f1f5f9; padding:10px; text-align:left; border-bottom:2px solid #cbd5e1; }}
        @media print {{ body {{ padding:0; background:#fff; }} .container {{ border:none; box-shadow:none; padding:0; }} .no-print {{ display:none; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 style="font-size:22px;margin:0;">CodePulse AI — Fix Verification &amp; Comparison Report</h1>
                <div style="font-size:12px;color:#64748b;margin-top:4px;">Comparison ID: <strong>{data['comparison_id']}</strong> &bull; Generated: {data['timestamp']}</div>
            </div>
            <button class="no-print" onclick="window.print()" style="background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;font-weight:600;cursor:pointer;">🖨️ Print / Save PDF</button>
        </div>

        <div class="score-box-wrap">
            <div class="card-val">
                <div class="val-num" style="color:#64748b;">{data['score_before']}/100</div>
                <div class="val-sub">Original Quality Score ({data['grade_before']})</div>
            </div>
            <div class="card-val" style="border-color:#10b981;background:#f0fdf4;">
                <div class="val-num" style="color:#10b981;">{data['score_after']}/100</div>
                <div class="val-sub">New Verified Score ({data['grade_after']})</div>
            </div>
            <div class="card-val">
                <div class="val-num" style="color:{'#10b981' if data['score_delta'] >= 0 else '#ef4444'};">{'+' if data['score_delta'] >= 0 else ''}{data['score_delta']}</div>
                <div class="val-sub">Net Score Gain (Points)</div>
            </div>
        </div>

        <h3 style="font-size:16px;border-bottom:1px solid #e2e8f0;padding-bottom:6px;margin:20px 0 12px 0;">📊 Metrics Comparison</h3>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th style="text-align:center;">Before</th>
                    <th style="text-align:center;">After</th>
                    <th style="text-align:center;">Change</th>
                </tr>
            </thead>
            <tbody>
                {metrics_rows}
            </tbody>
        </table>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;">
                <h4 style="margin:0 0 10px 0;color:#16a34a;font-size:14px;">✅ Resolved Issues ({len(data.get('resolved_issues', []))})</h4>
                <ul style="margin:0;padding-left:18px;font-size:12px;color:#14532d;">
                    {resolved_html or "<li>No issues resolved.</li>"}
                </ul>
            </div>

            <div style="background:#fffbeb;border:1px solid #fef3c7;border-radius:8px;padding:16px;">
                <h4 style="margin:0 0 10px 0;color:#d97706;font-size:14px;">⚠️ Remaining Issues ({len(data.get('remaining_issues', []))})</h4>
                <ul style="margin:0;padding-left:18px;font-size:12px;color:#78350f;">
                    {remaining_html or "<li>All issues successfully addressed!</li>"}
                </ul>
            </div>
        </div>

        {f'<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:16px;margin-bottom:20px;"><h4 style="margin:0 0 10px 0;color:#dc2626;font-size:14px;">🚨 Newly Introduced Issues ({len(data.get("new_issues", []))})</h4><ul style="margin:0;padding-left:18px;font-size:12px;">{new_html}</ul></div>' if data.get("new_issues") else '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px;font-size:12px;color:#16a34a;">✨ <strong>Zero Regressions:</strong> The AI fix introduced no new quality or security issues.</div>'}
    </div>
</body>
</html>
"""
        return html

    @staticmethod
    def generate_comparison_doc_report(comparison: ReportComparison) -> str:
        html = ReportGenerator.generate_comparison_html_report(comparison)
        doc_wrapper = f"""<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head>
<meta charset="utf-8">
<!--[if gte mso 9]>
<xml>
<w:WordDocument>
<w:View>Print</w:View>
<w:Zoom>100</w:Zoom>
<w:DoNotOptimizeForBrowser/>
</w:WordDocument>
</xml>
<![endif]-->
</head>
<body>
{html}
</body>
</html>
"""
        return doc_wrapper

    @staticmethod
    def generate_single_report_package_zip(result: AnalysisResult, source_code: str = "") -> bytes:
        """
        Creates an in-memory ZIP archive containing all formats for a single audit report:
        HTML, Word DOC, Markdown, JSON, and original source file.
        """
        zip_buffer = io.BytesIO()
        aid = result.analysis_id
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"CodePulse_Audit_Report_{aid}.html", ReportGenerator.generate_html_report(result))
            zf.writestr(f"CodePulse_Audit_Report_{aid}.doc", ReportGenerator.generate_doc_report(result))
            zf.writestr(f"CodePulse_Audit_Report_{aid}.md", ReportGenerator.generate_markdown_report(result))
            zf.writestr(f"CodePulse_Audit_Report_{aid}.json", ReportGenerator.generate_json_report(result))
            if source_code:
                zf.writestr(f"source_code_{result.filename}", source_code)
            
            manifest = {
                "package_type": "single_analysis",
                "analysis_id": aid,
                "filename": result.filename,
                "language": result.language,
                "quality_score": result.summary.quality_score,
                "total_issues": result.summary.total_issues,
                "generated_at": result.timestamp
            }
            zf.writestr("audit_manifest.json", json.dumps(manifest, indent=2))

        return zip_buffer.getvalue()

    @staticmethod
    def generate_report_package_zip(
        comparison: ReportComparison,
        original_result: AnalysisResult,
        fixed_result: AnalysisResult,
        original_code: str,
        fixed_code: str
    ) -> bytes:
        """
        Creates a complete multi-report in-memory ZIP archive containing:
        1. Original Analysis Reports (.html, .doc, .json, .md)
        2. Fixed Analysis Reports (.html, .doc, .json, .md)
        3. Before vs After Comparison Reports (.html, .doc, .json, .md)
        4. Original and Fixed Source Files
        5. Audit Package Telemetry Manifest (.json)
        """
        zip_buffer = io.BytesIO()
        cid = comparison.comparison_id
        orig_id = original_result.analysis_id
        fixed_id = fixed_result.analysis_id

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Original Analysis Reports
            zf.writestr(f"1_Original_Report_{orig_id}.html", ReportGenerator.generate_html_report(original_result))
            zf.writestr(f"1_Original_Report_{orig_id}.doc", ReportGenerator.generate_doc_report(original_result))
            zf.writestr(f"1_Original_Report_{orig_id}.md", ReportGenerator.generate_markdown_report(original_result))
            zf.writestr(f"1_Original_Report_{orig_id}.json", ReportGenerator.generate_json_report(original_result))

            # 2. Fixed Analysis Reports
            zf.writestr(f"2_Fixed_Report_{fixed_id}.html", ReportGenerator.generate_html_report(fixed_result))
            zf.writestr(f"2_Fixed_Report_{fixed_id}.doc", ReportGenerator.generate_doc_report(fixed_result))
            zf.writestr(f"2_Fixed_Report_{fixed_id}.md", ReportGenerator.generate_markdown_report(fixed_result))
            zf.writestr(f"2_Fixed_Report_{fixed_id}.json", ReportGenerator.generate_json_report(fixed_result))

            # 3. Before vs After Comparison Reports
            zf.writestr(f"3_Comparison_Report_{cid}.html", ReportGenerator.generate_comparison_html_report(comparison))
            zf.writestr(f"3_Comparison_Report_{cid}.doc", ReportGenerator.generate_comparison_doc_report(comparison))
            zf.writestr(f"3_Comparison_Report_{cid}.md", ReportGenerator.generate_comparison_markdown_report(comparison))
            zf.writestr(f"3_Comparison_Report_{cid}.json", ReportGenerator.generate_comparison_json_report(comparison))

            # 4. Source Codes
            zf.writestr(f"source_v1_original_{original_result.filename}", original_code)
            zf.writestr(f"source_v2_fixed_{fixed_result.filename}", fixed_code)

            # 5. Manifest Summary
            manifest = {
                "package_type": "full_comparison_bundle",
                "comparison_id": cid,
                "timestamp": comparison.timestamp,
                "original_analysis_id": orig_id,
                "fixed_analysis_id": fixed_id,
                "score_before": comparison.score_before,
                "score_after": comparison.score_after,
                "score_delta": comparison.score_delta,
                "resolved_issues_count": len(comparison.resolved_issues),
                "remaining_issues_count": len(comparison.remaining_issues),
                "new_issues_count": len(comparison.new_issues)
            }
            zf.writestr("audit_package_manifest.json", json.dumps(manifest, indent=2))

        return zip_buffer.getvalue()
