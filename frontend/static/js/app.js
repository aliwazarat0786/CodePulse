/**
 * CodePulse AI — Professional Client Controller
 * Handles Code Analysis, Dynamic Sandboxed Execution, Interactive Issue Selection,
 * AI Fixation, Real Backend Verification, Side-by-Side Diff, and Report Comparisons.
 */
class CodePulseApp {
    constructor() {
        this.currentAnalysis = null;
        this.originalAnalysis = null;
        this.originalCode = '';
        this.candidateFixedCode = '';
        this.selectedIssueIds = new Set();
        this.executionResult = null;
        this.reportComparison = null;
        this.activeFilter = 'ALL';
        this.selectedExportFormat = 'pdf';
        this.isComparisonExport = false;

        this.initEditorEvents();
    }

    // 1. Editor & Line Number Handlers
    initEditorEvents() {
        const textarea = document.getElementById('code-input');
        const lineNumbers = document.getElementById('line-numbers');
        const charCount = document.getElementById('char-count');
        const lineCount = document.getElementById('line-count');

        if (!textarea) return;

        const updateStats = () => {
            const val = textarea.value;
            const lines = val.split('\n');
            const numLines = lines.length;
            charCount.innerText = `${val.length} characters`;
            lineCount.innerText = `${numLines} line${numLines !== 1 ? 's' : ''}`;

            let numStr = '';
            for (let i = 1; i <= Math.max(numLines, 14); i++) {
                numStr += i + '<br>';
            }
            lineNumbers.innerHTML = numStr;

            // Live language detection if set to auto
            const langSelect = document.getElementById('language-select');
            if (langSelect && langSelect.value === 'auto') {
                const detected = this.detectLanguageClientSide(val);
                const liveTag = document.getElementById('live-lang-tag');
                const fileTag = document.getElementById('current-filename-tag');
                if (liveTag) liveTag.innerText = `Auto: ${detected.toUpperCase()}`;
                if (fileTag && fileTag.innerText.startsWith('snippet.')) {
                    fileTag.innerText = `snippet.${this.getExt(detected)}`;
                }
            }
        };

        textarea.addEventListener('input', updateStats);
        textarea.addEventListener('scroll', () => {
            lineNumbers.scrollTop = textarea.scrollTop;
        });

        // Tab key support
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                textarea.value = textarea.value.substring(0, start) + '    ' + textarea.value.substring(end);
                textarea.selectionStart = textarea.selectionEnd = start + 4;
                updateStats();
            }
        });

        updateStats();
    }

    // Client-Side Fast Heuristic Detector
    detectLanguageClientSide(code) {
        if (!code || !code.trim()) return 'python';
        const str = code.trim();

        const scores = {
            python: 0,
            javascript: 0,
            java: 0,
            cpp: 0,
            c: 0,
            sql: 0
        };

        // SQL / PostgreSQL / MySQL / SQLite
        if (/\b(SELECT\s+.*?\s+FROM|INSERT\s+INTO\s+\w+|UPDATE\s+\w+\s+SET|DELETE\s+FROM\s+\w+)\b/i.test(str)) scores.sql += 60;
        if (/\b(CREATE\s+(TABLE|FUNCTION|PROCEDURE|VIEW|INDEX|DATABASE|TRIGGER)|ALTER\s+TABLE|DROP\s+(TABLE|DATABASE|VIEW|INDEX))\b/i.test(str)) scores.sql += 60;
        if (/\b(PRIMARY\s+KEY|FOREIGN\s+KEY|REFERENCES\s+\w+|VARCHAR|TIMESTAMPTZ|PLPGSQL|LANGUAGE\s+PLPGSQL|SERIAL\s+PRIMARY\s+KEY)\b/i.test(str)) scores.sql += 50;
        if (/^\s*--(.*?)$/m.test(str)) scores.sql += 35;
        if (/\b(BEGIN\s+TRANSACTION|COMMIT;|ROLLBACK;|RETURNS\s+(SETOF|TABLE|VOID|TRIGGER)|END;\s*\$\$\s*LANGUAGE)\b/i.test(str)) scores.sql += 50;

        // Python / Django / Flask / FastAPI
        if (/^\s*def\s+[a-zA-Z_]\w*\s*\(.*?\):/m.test(str)) scores.python += 50;
        if (/^\s*class\s+[a-zA-Z_]\w*(\(.*?\))?:/m.test(str) && !str.includes('{')) scores.python += 40;
        if (/^\s*(from\s+[\w.]+\s+import\s+[\w.*, ]+|import\s+[\w., ]+)/m.test(str)) scores.python += 40;
        if (/\b(elif|except|self|__init__|__name__|None|True|False)\b/.test(str)) scores.python += 30;
        if (/@(app\.(route|get|post|put|delete)|router\.|csrf_exempt|classmethod|staticmethod|property|login_required)\b/.test(str)) scores.python += 45;
        if (/\b(django|flask|fastapi|sqlalchemy|pymongo|pydantic|render_template_string|render_template|models\.Model|models\.CharField)\b/.test(str)) scores.python += 45;

        // JavaScript / TypeScript / React / Node.js / MongoDB
        if (/\b(const|let|var)\s+([a-zA-Z_$][\w$]*|\{[^}]+\}|\[[^\]]+\])\s*=/.test(str)) scores.javascript += 50;
        if (/function\s+[a-zA-Z_$][\w$]*\s*\(|=>\s*\{|=>/.test(str)) scores.javascript += 45;
        if (/\bimport\s+.*?from\s+['"][^'"]+['"]/.test(str)) scores.javascript += 45;
        if (/\b(document\.|window\.|console\.(log|warn|error)|addEventListener|querySelector|getElementById)\b/.test(str)) scores.javascript += 50;
        if (/\b(useState|useEffect|useContext|useReducer|useCallback|useMemo|useRef|dangerouslySetInnerHTML)\b/.test(str)) scores.javascript += 55;
        if (/\b(module\.exports|export\s+default|export\s+const|require\(["'])/.test(str)) scores.javascript += 45;
        if (/\b(express\(\)|app\.(use|get|post|put|delete)\(|mongoose\.model|mongoose\.Schema|jwt\.sign|\$where)\b/.test(str)) scores.javascript += 50;
        if (str.includes('===') || str.includes('!==')) scores.javascript += 35;
        if (/<\/?([A-Z]\w+|div|span|button|input|section|main|p|h[1-6])(\s+[^>]*)?>/.test(str) && str.includes('class')) scores.javascript += 35;

        // Java / Spring
        if (/\bpublic\s+(final\s+|abstract\s+)?class\s+\w+/.test(str)) scores.java += 60;
        if (/public\s+static\s+void\s+main\s*\(\s*String\s*(\[\s*\]|\.\.\.)\s*\w+\s*\)/.test(str)) scores.java += 65;
        if (/System\.out\.print|System\.err\.print/.test(str)) scores.java += 50;
        if (/^\s*package\s+[a-zA-Z0-9_.]+;/m.test(str)) scores.java += 50;
        if (/^\s*import\s+java\.|^\s*import\s+org\.springframework/m.test(str)) scores.java += 45;
        if (/@(SpringBootApplication|RestController|Service|Repository|Autowired|Override|GetMapping|PostMapping)\b/.test(str)) scores.java += 50;

        // C++
        if (/#include\s+<(iostream|vector|memory|string|map|algorithm|thread|mutex)>/.test(str)) scores.cpp += 60;
        if (/std::cout|std::cin|std::endl|std::string|std::make_unique|std::vector/.test(str)) scores.cpp += 55;
        if (/\b(namespace\s+\w+|template\s*<|nullptr|constexpr|std::|std::shared_ptr|std::unique_ptr)\b/.test(str)) scores.cpp += 50;
        if (/using namespace std;|cout\s*<<|cin\s*>>/.test(str)) scores.cpp += 50;

        // C
        if (/#include\s+<(stdio\.h|stdlib\.h|string\.h|unistd\.h|stdbool\.h|pthread\.h)>/.test(str)) scores.c += 55;
        if (/\b(printf|scanf|malloc|calloc|realloc|free|strcpy|strlen|strncpy|fopen|fgets)\s*\(/.test(str)) scores.c += 40;
        if (/\bint\s+main\s*\(\s*(void|int\s+argc)?/.test(str)) scores.c += 30;

        // Balance host vs embedded SQL
        const maxHost = Math.max(scores.python, scores.javascript, scores.java, scores.cpp, scores.c);
        if (maxHost >= 60 && scores.sql < 100) {
            if (scores.python >= 40) scores.sql = Math.min(scores.sql, scores.python - 10);
            else if (scores.javascript >= 40) scores.sql = Math.min(scores.sql, scores.javascript - 10);
            else if (scores.java >= 40) scores.sql = Math.min(scores.sql, scores.java - 10);
        }

        let bestLang = 'python';
        let maxScore = 0;
        for (const [lang, score] of Object.entries(scores)) {
            if (score > maxScore) {
                maxScore = score;
                bestLang = lang;
            }
        }

        return maxScore >= 20 ? bestLang : 'python';
    }

    onLanguageChange(lang) {
        const liveTag = document.getElementById('live-lang-tag');
        const fileTag = document.getElementById('current-filename-tag');
        const textarea = document.getElementById('code-input');

        if (lang === 'auto') {
            const detected = this.detectLanguageClientSide(textarea ? textarea.value : '');
            if (liveTag) liveTag.innerText = `Auto: ${detected.toUpperCase()}`;
            if (fileTag && fileTag.innerText.startsWith('snippet.')) {
                fileTag.innerText = `snippet.${this.getExt(detected)}`;
            }
        } else {
            if (liveTag) liveTag.innerText = lang.toUpperCase();
            if (fileTag && fileTag.innerText.startsWith('snippet.')) {
                fileTag.innerText = `snippet.${this.getExt(lang)}`;
            }
        }
    }

    // 2. Tab Switcher
    switchTab(tab) {
        const pasteBtn = document.getElementById('tab-paste');
        const uploadBtn = document.getElementById('tab-upload');
        const pasteArea = document.getElementById('paste-area');
        const uploadArea = document.getElementById('upload-area');

        if (tab === 'paste') {
            pasteBtn.classList.add('active');
            uploadBtn.classList.remove('active');
            pasteArea.classList.remove('hidden');
            uploadArea.classList.add('hidden');
        } else {
            uploadBtn.classList.add('active');
            pasteBtn.classList.remove('active');
            uploadArea.classList.remove('hidden');
            pasteArea.classList.add('hidden');
        }
    }

    // 3. Sample Code Loader
    async loadSample(sampleKey) {
        try {
            const res = await fetch(`/api/sample/${sampleKey}`);
            const data = await res.json();
            if (data.code) {
                const textarea = document.getElementById('code-input');
                textarea.value = data.code;
                
                const langMap = {
                    sql: 'sql',
                    react: 'javascript',
                    node_mongo: 'javascript',
                    django_flask: 'python',
                    python: 'python',
                    javascript: 'javascript',
                    java: 'java',
                    c: 'c',
                    cpp: 'cpp'
                };
                const targetLang = langMap[sampleKey] || sampleKey;
                const langSelect = document.getElementById('language-select');
                if (langSelect) langSelect.value = targetLang;

                const fileTag = document.getElementById('current-filename-tag');
                if (fileTag) fileTag.innerText = `sample_${sampleKey}.${this.getExt(sampleKey)}`;

                textarea.dispatchEvent(new Event('input'));
                this.showToast(`Loaded ${sampleKey.toUpperCase().replace(/_/g, ' ')} demonstration code.`);
            }
        } catch (err) {
            this.showToast('Failed to load sample code.', 'error');
        }
    }

    getExt(lang) {
        const map = {
            python: 'py',
            java: 'java',
            c: 'c',
            cpp: 'cpp',
            javascript: 'js',
            sql: 'sql',
            react: 'jsx',
            node_mongo: 'js',
            django_flask: 'py'
        };
        return map[lang] || 'txt';
    }

    // 4. File Upload Handler
    handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (file.size > 1024 * 1024) {
            this.showToast('File size exceeds 1MB limit.', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
            const textarea = document.getElementById('code-input');
            textarea.value = event.target.result;
            document.getElementById('current-filename-tag').innerText = file.name;
            document.getElementById('upload-status').innerText = `Loaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            this.switchTab('paste');
            textarea.dispatchEvent(new Event('input'));
            this.showToast(`File ${file.name} uploaded successfully.`);
        };
        reader.readAsText(file);
    }

    // 5. Standalone Execute Code Action
    async executeCode() {
        const textarea = document.getElementById('code-input');
        const code = textarea.value.trim();
        let language = document.getElementById('language-select').value;
        const filename = document.getElementById('current-filename-tag').innerText || 'snippet.py';

        if (!code) {
            this.showToast('Please enter or upload source code to execute.', 'error');
            return;
        }

        if (language === 'auto') {
            language = this.detectLanguageClientSide(code);
        }

        this.showToast(`⚡ Initializing isolated sandboxed execution (${language.toUpperCase()})...`);
        try {
            const res = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_code: code,
                    language: language,
                    filename: filename
                })
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                this.renderExecutionOutput(data.execution);
                this.showToast('Execution finished.');
            } else {
                throw new Error(data.message || 'Execution error');
            }
        } catch (err) {
            this.showToast(`Execution failed: ${err.message}`, 'error');
        }
    }

    // 6. Start Analysis Execution (Analyze or Analyze + Run)
    async startAnalysis(runCode = true) {
        const textarea = document.getElementById('code-input');
        const code = textarea.value.trim();
        const language = document.getElementById('language-select').value;
        const enableAi = document.getElementById('ai-toggle').checked;
        const filename = document.getElementById('current-filename-tag').innerText || 'snippet.py';

        if (!code) {
            this.showToast('Please enter or upload source code to analyze.', 'error');
            return;
        }

        this.originalCode = code;

        // Show clean loading state
        document.getElementById('input-card').classList.add('hidden');
        document.getElementById('loading-card').classList.remove('hidden');
        document.getElementById('results-container').classList.add('hidden');
        document.getElementById('execution-card').classList.add('hidden');
        document.getElementById('ai-fix-preview-card').classList.add('hidden');
        document.getElementById('comparison-dashboard-card').classList.add('hidden');

        this.runStepAnimation();

        const endpoint = runCode ? '/api/analyze-and-run' : '/api/analyze';

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_code: code,
                    filename: filename,
                    language: language,
                    enable_ai: enableAi
                })
            });

            const resultData = await response.json();

            if (response.ok && resultData.status === 'success') {
                this.currentAnalysis = resultData.analysis;
                this.originalAnalysis = resultData.analysis;
                
                // Automatically select all issues initially
                this.selectedIssueIds.clear();
                if (this.currentAnalysis.issues) {
                    this.currentAnalysis.issues.forEach(i => this.selectedIssueIds.add(i.id));
                }

                setTimeout(() => {
                    this.renderResults(this.currentAnalysis);
                }, 700);
            } else {
                throw new Error(resultData.message || 'Analysis failed');
            }
        } catch (err) {
            document.getElementById('loading-card').classList.add('hidden');
            document.getElementById('input-card').classList.remove('hidden');
            this.showToast(`Error: ${err.message}`, 'error');
        }
    }

    // Progress Animation
    runStepAnimation() {
        const steps = ['step-1', 'step-2', 'step-3', 'step-4', 'step-5'];
        const labels = [
            '1. Language identification & syntax validation...',
            '2. Multi-engine static analysis & heuristic scanning...',
            '3. Sandboxed compilation & dynamic execution...',
            '4. Complexity metrics & quality scoring...',
            '5. Machine learning & AI recommendation engine...'
        ];

        steps.forEach((id) => {
            const el = document.getElementById(id);
            if (el) el.className = 'step-row';
        });

        let idx = 0;
        const stepInterval = setInterval(() => {
            if (idx < steps.length) {
                const cur = document.getElementById(steps[idx]);
                if (cur) cur.classList.add('active');
                document.getElementById('loading-step-text').innerText = labels[idx];
                if (idx > 0) {
                    const prev = document.getElementById(steps[idx - 1]);
                    if (prev) {
                        prev.classList.remove('active');
                        prev.classList.add('done');
                    }
                }
                idx++;
            } else {
                clearInterval(stepInterval);
            }
        }, 300);
    }

    // 7. Render Execution Terminal Output
    renderExecutionOutput(exec) {
        if (!exec) return;
        const card = document.getElementById('execution-card');
        card.classList.remove('hidden');

        const statusBadge = document.getElementById('exec-status-badge');
        statusBadge.innerText = exec.status;
        statusBadge.className = 'status-badge';
        if (exec.status === 'SUCCESS') statusBadge.classList.add('success');
        else if (exec.status === 'TIMEOUT') statusBadge.classList.add('timeout');
        else statusBadge.classList.add('failed');

        document.getElementById('exec-time-badge').innerText = `${exec.execution_time}s`;
        document.getElementById('exec-code-badge').innerText = `Exit: ${exec.exit_code}`;

        document.getElementById('exec-stdout-content').innerText = exec.stdout || '// No standard output produced.';

        const stderrBlock = document.getElementById('exec-stderr-block');
        if (exec.stderr && exec.stderr.trim()) {
            stderrBlock.classList.remove('hidden');
            document.getElementById('exec-stderr-content').innerText = exec.stderr;
        } else {
            stderrBlock.classList.add('hidden');
        }

        const compileBlock = document.getElementById('exec-compile-block');
        if (exec.compilation_output && exec.compilation_output.trim() && exec.status === 'COMPILATION_ERROR') {
            compileBlock.classList.remove('hidden');
            document.getElementById('exec-compile-content').innerText = exec.compilation_output;
        } else {
            compileBlock.classList.add('hidden');
        }

        card.scrollIntoView({ behavior: 'smooth' });
    }

    // 8. Render Results Dashboard
    renderResults(data) {
        document.getElementById('loading-card').classList.add('hidden');
        document.getElementById('results-container').classList.remove('hidden');

        if (data.execution) {
            this.renderExecutionOutput(data.execution);
        }

        const summary = data.summary;
        const metrics = data.metrics;
        const issues = data.issues;

        // Quality Score & Donut Animation
        const score = summary.quality_score;
        this.animateCounter('score-val', score, 900);
        
        const circle = document.getElementById('score-circle-bar');
        const offset = 301.59 - (301.59 * score) / 100;
        circle.style.strokeDashoffset = offset;

        if (score >= 80) circle.style.stroke = '#10b981';
        else if (score >= 60) circle.style.stroke = '#0ea5e9';
        else if (score >= 40) circle.style.stroke = '#f59e0b';
        else circle.style.stroke = '#ef4444';

        const gradePill = document.getElementById('grade-pill');
        gradePill.innerText = `GRADE ${summary.score_grade}`;
        document.getElementById('verdict-text').innerText = summary.verdict;

        // Telemetry stats
        this.animateCounter('stat-loc', metrics.lines_of_code, 700);
        document.getElementById('stat-cc').innerText = metrics.cyclomatic_complexity || '1.0';
        document.getElementById('stat-mi').innerText = metrics.maintainability_index || '85.0';
        this.animateCounter('stat-total-issues', issues.length, 700);

        // Severity Distribution
        this.renderSeverityDistribution(summary);

        // ML Model Prediction Telemetry
        if (data.ml_prediction && data.ml_prediction.predicted_label) {
            const ml = data.ml_prediction;
            const labelEl = document.getElementById('ml-predicted-label');
            const pctEl = document.getElementById('ml-risk-pct');
            const barEl = document.getElementById('ml-risk-bar');
            
            labelEl.innerText = ml.predicted_label.replace(/_/g, ' ');
            const riskPct = Math.round((ml.risk_score || 0.1) * 100);
            pctEl.innerText = `${riskPct}%`;
            barEl.style.width = `${Math.max(5, riskPct)}%`;

            if (riskPct >= 60) {
                pctEl.style.color = '#ef4444';
                barEl.style.background = '#ef4444';
            } else if (riskPct >= 30) {
                pctEl.style.color = '#f59e0b';
                barEl.style.background = '#f59e0b';
            } else {
                pctEl.style.color = '#10b981';
                barEl.style.background = '#10b981';
            }
        }

        // Code Architecture & Purpose
        if (data.code_purpose) {
            const cp = data.code_purpose;
            const langBadge = document.getElementById('code-detected-lang-badge');
            if (langBadge) langBadge.innerText = (data.language || 'UNKNOWN').toUpperCase();

            const titleEl = document.getElementById('code-purpose-title');
            if (titleEl && cp.purpose_title) titleEl.innerText = cp.purpose_title;

            const subEl = document.getElementById('code-domain-runtime');
            if (subEl) subEl.innerText = `Domain: ${cp.domain || 'Software Engineering'} • Target Runtime: ${cp.target_runtime || 'Standard'}`;

            const descEl = document.getElementById('code-purpose-desc');
            if (descEl && cp.description) descEl.innerText = cp.description;

            const capBox = document.getElementById('code-capabilities-list');
            if (capBox && cp.capabilities && cp.capabilities.length > 0) {
                capBox.innerHTML = cp.capabilities.map(c => `<span class="cap-tag">${this.escapeHtml(c)}</span>`).join('');
            }
        }

        // Actionable Remediation & Refactoring Roadmap
        if (data.refactoring_roadmap) {
            const rm = data.refactoring_roadmap;
            const subEl = document.getElementById('roadmap-diagnostic-sub');
            if (subEl) subEl.innerText = `Diagnostic: ${rm.total_defects_count || 0} issues detected • Current Score: ${score}/100`;

            const urgencyBadge = document.getElementById('roadmap-urgency-badge');
            if (urgencyBadge) {
                const urg = (rm.action_urgency || '').toUpperCase();
                urgencyBadge.className = 'urgency-pill';
                if (urg.includes('LOW')) {
                    urgencyBadge.innerText = 'LOW RISK';
                    urgencyBadge.classList.add('low');
                } else if (urg.includes('URGENT')) {
                    urgencyBadge.innerText = 'CRITICAL URGENCY';
                    urgencyBadge.classList.add('urgent');
                } else {
                    urgencyBadge.innerText = 'ACTION RECOMMENDED';
                }
            }

            const gainPill = document.getElementById('roadmap-score-gain');
            if (gainPill) gainPill.innerText = `Target: ${rm.projected_score || 100}/100`;

            const diagText = document.getElementById('roadmap-diagnostic-text');
            if (diagText) diagText.innerText = rm.diagnostic_summary || 'Evaluating code health drivers.';

            const stepsContainer = document.getElementById('roadmap-steps-list');
            if (stepsContainer && rm.refactoring_steps) {
                stepsContainer.innerHTML = rm.refactoring_steps.map(s => `
                    <div class="step-card">
                        <div class="step-number">${s.step}</div>
                        <div class="step-main">
                            <div class="step-top-line">
                                <span class="step-title-text">${this.escapeHtml(s.title)}</span>
                                <span class="step-gain-badge">${this.escapeHtml(s.expected_gain)}</span>
                            </div>
                            <div class="step-problem"><strong>Problem / Root Cause:</strong> ${this.escapeHtml(s.problem)}</div>
                            <div class="step-solution"><strong>Required Change:</strong> ${this.escapeHtml(s.solution)} &bull; <em>Target: ${this.escapeHtml(s.target)}</em></div>
                        </div>
                    </div>
                `).join('');
            }
        }

        // AI Executive Summary
        if (data.ai_summary && data.ai_summary.executive_summary) {
            document.getElementById('ai-exec-summary').innerText = data.ai_summary.executive_summary;
        }

        // Render Issue Cards with Interactive Checkboxes
        this.renderIssues(issues);
        this.updateSelectedCountTag();

        document.getElementById('results-container').scrollIntoView({ behavior: 'smooth' });
    }

    renderSeverityDistribution(summary) {
        const total = Math.max(1, summary.total_issues);
        const setBar = (id, countId, count) => {
            const bar = document.getElementById(id);
            const countEl = document.getElementById(countId);
            countEl.innerText = count;
            const pct = Math.min(100, Math.round((count / total) * 100));
            bar.style.width = `${pct}%`;
        };

        setBar('bar-critical', 'count-critical', summary.critical);
        setBar('bar-high', 'count-high', summary.high);
        setBar('bar-medium', 'count-medium', summary.medium);
        setBar('bar-low', 'count-low', summary.low);
    }

    // 9. Render Interactive Issue Findings
    renderIssues(issues) {
        const container = document.getElementById('issues-list-container');
        container.innerHTML = '';
        document.getElementById('findings-count-tag').innerText = `${issues.length} finding${issues.length !== 1 ? 's' : ''}`;

        if (!issues || issues.length === 0) {
            container.innerHTML = `
                <div class="card" style="padding: 2rem; text-align: center; color: #10b981;">
                    <h4 style="margin-bottom: 4px; font-weight: 600;">Zero Deficiencies Detected</h4>
                    <p style="color: #94a3b8; font-size: 0.85rem;">Source code satisfies all static, security, and runtime checks.</p>
                </div>
            `;
            return;
        }

        issues.forEach((iss, index) => {
            const card = document.createElement('div');
            card.className = `issue-item issue-sev-${iss.severity}`;
            card.setAttribute('data-severity', iss.severity);
            card.setAttribute('data-category', iss.category);
            card.id = `issue-card-${iss.id}`;

            const isChecked = this.selectedIssueIds.has(iss.id);
            const ai = iss.ai_analysis || {};

            card.innerHTML = `
                <div class="issue-row-header" onclick="app.onIssueRowClick(event, ${index}, ${iss.line})">
                    <div class="issue-left-meta">
                        <div class="issue-cb-wrap" onclick="event.stopPropagation()">
                            <input type="checkbox" class="issue-cb" data-id="${iss.id}" ${isChecked ? 'checked' : ''} onchange="app.onIssueSelectionChange(event, '${iss.id}')">
                        </div>
                        <span class="badge-sev ${iss.severity}">${iss.severity}</span>
                        <span class="issue-msg-text">${this.escapeHtml(iss.message)}</span>
                    </div>
                    <div class="issue-right-meta">
                        <span>Line ${iss.line}</span>
                        <span>[${iss.tool}]</span>
                        <span class="chevron-icon" id="chevron-${index}">▼</span>
                    </div>
                </div>
                <div class="issue-detail-panel hidden" id="issue-body-${index}">
                    <div class="snippet-display" onclick="app.jumpToLine(${iss.line})">
                        <span class="snippet-line-ref">Line ${iss.line}:</span><span class="snippet-highlight">${this.escapeHtml(iss.source || '// Source context')}</span>
                    </div>
                    <div class="remediation-box">
                        <div class="remediation-title">AI Exact Diagnosis &amp; Remediation</div>
                        <div class="remediation-point"><strong>Why it matters:</strong> ${this.escapeHtml(ai.explanation || 'Code pattern exhibits maintainability or security risks.')}</div>
                        <div class="remediation-point"><strong>Potential Impact:</strong> ${this.escapeHtml(ai.impact || 'System reliability, unhandled exceptions, or exploit surface.')}</div>
                        <div class="remediation-point"><strong>Recommended Action:</strong> ${this.escapeHtml(ai.recommendation || iss.suggested_fix || 'Refactor according to standard language practices.')}</div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    }

    onIssueRowClick(event, index, line) {
        this.toggleIssueAccordion(index);
        this.jumpToLine(line);
    }

    toggleIssueAccordion(index) {
        const body = document.getElementById(`issue-body-${index}`);
        const chevron = document.getElementById(`chevron-${index}`);
        if (body.classList.contains('hidden')) {
            body.classList.remove('hidden');
            chevron.innerText = '▲';
        } else {
            body.classList.add('hidden');
            chevron.innerText = '▼';
        }
    }

    jumpToLine(line) {
        const textarea = document.getElementById('code-input');
        if (!textarea) return;

        const lines = textarea.value.split('\n');
        if (line > lines.length) return;

        let charPos = 0;
        for (let i = 0; i < line - 1; i++) {
            charPos += lines[i].length + 1;
        }

        const lineEnd = charPos + (lines[line - 1] ? lines[line - 1].length : 0);
        textarea.focus();
        textarea.setSelectionRange(charPos, lineEnd);

        // Scroll editor
        const lineHeight = 21;
        textarea.scrollTop = Math.max(0, (line - 4) * lineHeight);
    }

    // 10. Issue Selection Management
    selectAllIssues() {
        if (!this.currentAnalysis || !this.currentAnalysis.issues) return;
        this.currentAnalysis.issues.forEach(i => this.selectedIssueIds.add(i.id));
        document.querySelectorAll('.issue-cb').forEach(cb => cb.checked = true);
        this.updateSelectedCountTag();
    }

    deselectAllIssues() {
        this.selectedIssueIds.clear();
        document.querySelectorAll('.issue-cb').forEach(cb => cb.checked = false);
        this.updateSelectedCountTag();
    }

    onIssueSelectionChange(event, issueId) {
        if (event.target.checked) {
            this.selectedIssueIds.add(issueId);
        } else {
            this.selectedIssueIds.delete(issueId);
        }
        this.updateSelectedCountTag();
    }

    updateSelectedCountTag() {
        const tag = document.getElementById('selected-count-tag');
        if (tag) {
            tag.innerText = `${this.selectedIssueIds.size} selected`;
        }
    }

    filterIssues(filter) {
        this.activeFilter = filter;
        document.querySelectorAll('.filter-group .filter-btn').forEach(c => c.classList.remove('active'));
        if (event && event.target) event.target.classList.add('active');

        const cards = document.querySelectorAll('.issue-item');
        cards.forEach(card => {
            const sev = card.getAttribute('data-severity');
            const cat = card.getAttribute('data-category');

            if (filter === 'ALL') {
                card.classList.remove('hidden');
            } else if (filter === 'security') {
                if (cat === 'security') card.classList.remove('hidden');
                else card.classList.add('hidden');
            } else {
                if (sev === filter) card.classList.remove('hidden');
                else card.classList.add('hidden');
            }
        });
    }

    // 11. AI Fix Actions
    async fixSelectedIssues() {
        if (this.selectedIssueIds.size === 0) {
            this.showToast('Please select at least one issue to fix.', 'error');
            return;
        }

        const textarea = document.getElementById('code-input');
        const code = textarea.value;
        const language = document.getElementById('language-select').value;
        const analysisId = this.currentAnalysis ? this.currentAnalysis.analysis_id : '';

        this.showToast(`🤖 Generating verified AI fix for ${this.selectedIssueIds.size} selected issue(s)...`);

        try {
            const res = await fetch('/api/ai/fix', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_code: code,
                    language: language,
                    analysis_id: analysisId,
                    selected_issue_ids: Array.from(this.selectedIssueIds),
                    fix_all: false
                })
            });

            const data = await res.json();
            if (res.ok && data.status === 'success') {
                this.renderAIFixPreview(data);
                this.showToast('AI Fix and verification complete.');
            } else {
                throw new Error(data.message || 'AI Fix generation failed');
            }
        } catch (err) {
            this.showToast(`AI Fix error: ${err.message}`, 'error');
        }
    }

    async fixAllIssues() {
        const textarea = document.getElementById('code-input');
        const code = textarea.value;
        const language = document.getElementById('language-select').value;
        const analysisId = this.currentAnalysis ? this.currentAnalysis.analysis_id : '';

        this.showToast('🤖 Generating comprehensive verified AI fix for all issues...');

        try {
            const res = await fetch('/api/ai/fix-all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_code: code,
                    language: language,
                    analysis_id: analysisId
                })
            });

            const data = await res.json();
            if (res.ok && data.status === 'success') {
                this.renderAIFixPreview(data);
                this.showToast('Comprehensive AI Fix generated and verified.');
            } else {
                throw new Error(data.message || 'Fix All failed');
            }
        } catch (err) {
            this.showToast(`AI Fix error: ${err.message}`, 'error');
        }
    }

    // 12. Render AI Fix Preview & Side-by-Side Diff
    renderAIFixPreview(fixData) {
        const card = document.getElementById('ai-fix-preview-card');
        card.classList.remove('hidden');

        const fixTab = document.getElementById('wnav-fix');
        if (fixTab) fixTab.classList.remove('hidden');

        this.candidateFixedCode = fixData.candidate_fixed_code;

        // Verification Badge
        const verif = fixData.verification || {};
        const vPill = document.getElementById('verification-status-pill');
        vPill.innerText = verif.status || 'VERIFIED';
        vPill.className = 'verification-pill';
        if (verif.status === 'FAILED_VERIFICATION') vPill.classList.add('failed');
        else if (verif.status === 'PARTIALLY_VERIFIED') vPill.classList.add('partial');

        document.getElementById('verification-summary-text').innerText = verif.summary || 'Fix candidate verified by backend execution.';

        // Explanations list
        const expList = document.getElementById('fix-explanations-list');
        expList.innerHTML = '';
        if (fixData.fix_results && fixData.fix_results.length > 0) {
            fixData.fix_results.forEach(f => {
                const item = document.createElement('div');
                item.className = 'fix-exp-item';
                item.innerHTML = `
                    <div class="fix-exp-title">🔧 ${this.escapeHtml(f.problem)}</div>
                    <div class="fix-exp-grid">
                        <div><strong>Root Cause:</strong> ${this.escapeHtml(f.root_cause)}</div>
                        <div><strong>Action:</strong> ${this.escapeHtml(f.exact_fix)}</div>
                        <div><strong>Summary:</strong> ${this.escapeHtml(f.change_summary)}</div>
                    </div>
                `;
                expList.appendChild(item);
            });
        }

        // Render Side-by-Side Diff
        this.renderDiffGrid(fixData.code_comparison);

        this.showWorkspaceTab('fix');
    }

    renderDiffGrid(codeComp) {
        const container = document.getElementById('diff-body-grid');
        container.innerHTML = '';

        if (!codeComp || !codeComp.diff_lines) {
            container.innerHTML = `<div style="padding:12px;color:#94a3b8;">No code differences detected.</div>`;
            return;
        }

        codeComp.diff_lines.forEach(row => {
            const diffRow = document.createElement('div');
            diffRow.className = `diff-row row-${row.type}`;

            const origNum = row.line_orig !== null ? row.line_orig : '';
            const fixedNum = row.line_fixed !== null ? row.line_fixed : '';

            diffRow.innerHTML = `
                <div class="diff-cell">
                    <span class="diff-num">${origNum}</span>
                    <span class="diff-text">${this.escapeHtml(row.orig_text || '')}</span>
                </div>
                <div class="diff-cell">
                    <span class="diff-num">${fixedNum}</span>
                    <span class="diff-text">${this.escapeHtml(row.fixed_text || '')}</span>
                </div>
            `;
            container.appendChild(diffRow);
        });
    }

    // Workspace Tab & Mode Switcher
    showWorkspaceTab(tab) {
        const inputCard = document.getElementById('input-card');
        const resultsContainer = document.getElementById('results-container');
        const fixCard = document.getElementById('ai-fix-preview-card');
        const compCard = document.getElementById('comparison-dashboard-card');
        const execCard = document.getElementById('execution-card');

        // Nav tabs
        ['editor', 'report', 'fix', 'comp'].forEach(t => {
            const btn = document.getElementById(`wnav-${t}`);
            if (btn) {
                if (t === tab) btn.classList.add('active');
                else btn.classList.remove('active');
            }
        });

        if (tab === 'editor') {
            inputCard.classList.remove('hidden');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else if (tab === 'report') {
            resultsContainer.classList.remove('hidden');
            resultsContainer.scrollIntoView({ behavior: 'smooth' });
        } else if (tab === 'fix') {
            fixCard.classList.remove('hidden');
            fixCard.scrollIntoView({ behavior: 'smooth' });
        } else if (tab === 'comp') {
            compCard.classList.remove('hidden');
            compCard.scrollIntoView({ behavior: 'smooth' });
        }
    }

    // 13. Run Fixed Code Independently
    async runFixedCode() {
        if (!this.candidateFixedCode) return;
        const language = document.getElementById('language-select').value;

        this.showToast('⚡ Running candidate fixed code in sandbox...');
        try {
            const res = await fetch('/api/run-fixed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fixed_code: this.candidateFixedCode,
                    language: language
                })
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                const box = document.getElementById('fixed-exec-box');
                box.classList.remove('hidden');
                document.getElementById('fixed-exec-status').innerText = data.execution.status;
                document.getElementById('fixed-exec-stdout').innerText = data.execution.stdout || data.execution.stderr || '// Executed cleanly with no output.';
                this.showToast('Fixed code executed successfully.');
            }
        } catch (err) {
            this.showToast(`Fixed execution error: ${err.message}`, 'error');
        }
    }

    // 14. Apply Code to Main Editor (Manual or 1-Click Auto Re-Analyze)
    applyFixedCode() {
        if (!this.candidateFixedCode) return;
        const textarea = document.getElementById('code-input');
        textarea.value = this.candidateFixedCode;

        const banner = document.getElementById('editor-version-banner');
        if (banner) banner.classList.remove('hidden');

        const versionTag = document.getElementById('code-version-tag');
        if (versionTag) {
            versionTag.innerText = 'v2 (AI Fixed)';
            versionTag.classList.remove('hidden');
        }

        textarea.dispatchEvent(new Event('input'));
        this.showToast('✓ AI Fixed code applied to main editor (v2).');
        this.showWorkspaceTab('editor');
    }

    async applyAndAutoReanalyze() {
        if (!this.candidateFixedCode) return;
        const textarea = document.getElementById('code-input');
        textarea.value = this.candidateFixedCode;

        const banner = document.getElementById('editor-version-banner');
        if (banner) banner.classList.remove('hidden');

        const versionTag = document.getElementById('code-version-tag');
        if (versionTag) {
            versionTag.innerText = 'v2 (AI Fixed)';
            versionTag.classList.remove('hidden');
        }

        textarea.dispatchEvent(new Event('input'));
        this.showToast('⚡ AI Fixed code applied! Running full re-analysis and generating comparison...');
        
        await this.reanalyzeAppliedCode();
    }

    revertToOriginal() {
        if (!this.originalCode) return;
        const textarea = document.getElementById('code-input');
        textarea.value = this.originalCode;

        const banner = document.getElementById('editor-version-banner');
        if (banner) banner.classList.add('hidden');

        const versionTag = document.getElementById('code-version-tag');
        if (versionTag) {
            versionTag.innerText = 'v1 (Original)';
        }

        textarea.dispatchEvent(new Event('input'));
        this.showToast('↺ Restored editor to original source code (v1).');
    }

    discardFix() {
        this.candidateFixedCode = '';
        document.getElementById('ai-fix-preview-card').classList.add('hidden');
        const fixTab = document.getElementById('wnav-fix');
        if (fixTab) fixTab.classList.add('hidden');
        this.showToast('Candidate AI fix discarded. Original code retained.');
    }

    // 15. Re-analyze Applied Code & Report Comparison
    async reanalyzeAppliedCode() {
        const textarea = document.getElementById('code-input');
        const code = textarea.value.trim();
        const language = document.getElementById('language-select').value;
        const origId = this.originalAnalysis ? this.originalAnalysis.analysis_id : '';

        if (!code) {
            this.showToast('Editor is empty.', 'error');
            return;
        }

        this.showToast('📊 Running comprehensive re-analysis and calculating comparison report...');

        try {
            const res = await fetch('/api/reanalyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_code: code,
                    original_analysis_id: origId,
                    original_code: this.originalCode,
                    language: language
                })
            });

            const data = await res.json();
            if (res.ok && data.status === 'success') {
                this.currentAnalysis = data.new_analysis;
                this.reportComparison = data.comparison;

                this.renderResults(data.new_analysis);
                if (data.comparison) {
                    this.renderReportComparison(data.comparison);
                    const compTab = document.getElementById('wnav-comp');
                    if (compTab) compTab.classList.remove('hidden');
                    this.showWorkspaceTab('comp');
                }
                this.showToast('✓ Re-analysis & Report Comparison complete!');
            } else {
                throw new Error(data.message || 'Re-analysis failed');
            }
        } catch (err) {
            this.showToast(`Re-analysis error: ${err.message}`, 'error');
        }
    }

    // 16. Render Report Comparison Dashboard
    renderReportComparison(comp) {
        const card = document.getElementById('comparison-dashboard-card');
        card.classList.remove('hidden');

        document.getElementById('comp-score-before').innerText = comp.score_before;
        document.getElementById('comp-grade-before').innerText = `Grade ${comp.grade_before}`;

        document.getElementById('comp-score-after').innerText = comp.score_after;
        document.getElementById('comp-grade-after').innerText = `Grade ${comp.grade_after}`;

        const deltaStr = comp.score_delta >= 0 ? `+${comp.score_delta} Points Gain` : `${comp.score_delta} Points`;
        document.getElementById('comp-score-delta').innerText = deltaStr;

        // Resolved issues list
        const resolvedList = document.getElementById('comp-resolved-list');
        resolvedList.innerHTML = '';
        document.getElementById('comp-resolved-count').innerText = comp.resolved_issues.length;
        if (comp.resolved_issues.length === 0) {
            resolvedList.innerHTML = '<li>No issues resolved yet.</li>';
        } else {
            comp.resolved_issues.forEach(i => {
                resolvedList.innerHTML += `<li><strong>✓ Line ${i.line}:</strong> ${this.escapeHtml(i.message)}</li>`;
            });
        }

        // Remaining issues list
        const remainingList = document.getElementById('comp-remaining-list');
        remainingList.innerHTML = '';
        document.getElementById('comp-remaining-count').innerText = comp.remaining_issues.length;
        if (comp.remaining_issues.length === 0) {
            remainingList.innerHTML = '<li>✨ Zero remaining issues! Clean codebase.</li>';
        } else {
            comp.remaining_issues.forEach(i => {
                remainingList.innerHTML += `<li><strong>⚠ Line ${i.line}:</strong> ${this.escapeHtml(i.message)}</li>`;
            });
        }

        // New issues list
        const newList = document.getElementById('comp-new-list');
        newList.innerHTML = '';
        document.getElementById('comp-new-count').innerText = comp.new_issues.length;
        if (comp.new_issues.length === 0) {
            newList.innerHTML = '<li>✨ Zero regressions introduced by fix.</li>';
        } else {
            comp.new_issues.forEach(i => {
                newList.innerHTML += `<li style="color:#ef4444;"><strong>! Line ${i.line}:</strong> ${this.escapeHtml(i.message)}</li>`;
            });
        }

        // Metrics Table
        const tbody = document.getElementById('comp-metrics-tbody');
        tbody.innerHTML = '';
        if (comp.metrics_comparison) {
            for (const [key, row] of Object.entries(comp.metrics_comparison)) {
                const tr = document.createElement('tr');
                const dVal = row.delta;
                const dStr = dVal > 0 ? `+${dVal}` : `${dVal}`;
                const color = row.improved ? '#10b981' : '#ef4444';

                tr.innerHTML = `
                    <td style="font-weight:600;">${row.label || key}</td>
                    <td style="text-align:center;">${row.before}</td>
                    <td style="text-align:center;font-weight:bold;">${row.after}</td>
                    <td style="text-align:center;color:${color};font-weight:700;">${dStr}</td>
                `;
                tbody.appendChild(tr);
            }
        }

        card.scrollIntoView({ behavior: 'smooth' });
    }

    // 17. Comprehensive Download Actions: Original, Fixed, Comparison, Full ZIP Package
    downloadOriginalReport(format = 'html') {
        if (!this.originalAnalysis) {
            this.showToast('No original analysis found.', 'error');
            return;
        }
        const id = this.originalAnalysis.analysis_id;
        window.open(`/api/report/${id}?format=${format}&download=true`, '_blank');
        this.showToast(`📥 Downloading Original Report (${format.toUpperCase()})...`);
    }

    downloadFixedReport(format = 'html') {
        if (!this.currentAnalysis) {
            this.showToast('No fixed analysis report found.', 'error');
            return;
        }
        const id = this.currentAnalysis.analysis_id;
        window.open(`/api/report/${id}?format=${format}&download=true`, '_blank');
        this.showToast(`📥 Downloading Fixed Report (${format.toUpperCase()})...`);
    }

    downloadComparisonReport(format = 'html') {
        if (!this.reportComparison) {
            this.showToast('Please re-analyze code to generate comparison report first.', 'error');
            return;
        }
        const cmpId = this.reportComparison.comparison_id;
        window.open(`/api/report/comparison/${cmpId}?format=${format}&download=true`, '_blank');
        this.showToast(`📥 Downloading Comparison Report (${format.toUpperCase()})...`);
    }

    downloadAllReportsPackage() {
        if (!this.reportComparison) {
            // Fallback to single analysis ZIP
            if (this.currentAnalysis) {
                const aid = this.currentAnalysis.analysis_id;
                window.open(`/api/report/${aid}?format=zip&download=true`, '_blank');
                this.showToast('📦 Downloading CodePulse Single Audit Report ZIP package...');
                return;
            }
            this.showToast('Please analyze or re-analyze code to generate full report package.', 'error');
            return;
        }
        const cmpId = this.reportComparison.comparison_id;
        window.open(`/api/report/download-all/${cmpId}`, '_blank');
        this.showToast('📦 Downloading complete CodePulse All-Reports ZIP Package (Original + Fixed + Comparison + Codes)...');
    }

    // 18. Share & Export Modal Management
    openShareModal() {
        if (!this.currentAnalysis) {
            this.showToast('Please perform an analysis before exporting.', 'error');
            return;
        }

        const id = this.currentAnalysis.analysis_id;
        const shareUrl = `${window.location.origin}/api/report/${id}?format=html`;
        
        const inputField = document.getElementById('share-link-input');
        if (inputField) {
            inputField.value = shareUrl;
        }

        this.selectExportFormat(this.selectedExportFormat || 'pdf');

        const modal = document.getElementById('share-export-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    closeShareModal() {
        const modal = document.getElementById('share-export-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    handleModalOverlayClick(e) {
        if (e.target && e.target.id === 'share-export-modal') {
            this.closeShareModal();
        }
    }

    selectExportFormat(format) {
        this.selectedExportFormat = format;

        document.querySelectorAll('.format-card').forEach((card) => {
            if (card.getAttribute('data-format') === format) {
                card.classList.add('active');
            } else {
                card.classList.remove('active');
            }
        });

        const previewEl = document.getElementById('modal-filename-preview');
        if (previewEl && this.currentAnalysis) {
            if (format === 'zip') {
                previewEl.innerText = `CodePulse_Report_Package_${this.currentAnalysis.analysis_id}.zip`;
            } else {
                const extMap = { pdf: 'pdf', doc: 'doc', html: 'html', json: 'json', md: 'md' };
                const ext = extMap[format] || 'pdf';
                previewEl.innerText = `CodePulse_Report_${this.currentAnalysis.analysis_id}.${ext}`;
            }
        }
    }

    copyShareLink() {
        const inputField = document.getElementById('share-link-input');
        if (!inputField) return;

        navigator.clipboard.writeText(inputField.value).then(() => {
            this.showToast('📋 Web report link copied to clipboard!');
        }).catch(() => {
            inputField.select();
            document.execCommand('copy');
            this.showToast('📋 Web report link copied to clipboard!');
        });
    }

    openShareLink() {
        const inputField = document.getElementById('share-link-input');
        if (inputField && inputField.value) {
            window.open(inputField.value, '_blank');
        } else if (this.currentAnalysis) {
            window.open(`/api/report/${this.currentAnalysis.analysis_id}?format=html`, '_blank');
        }
    }

    async nativeShare() {
        if (!this.currentAnalysis) return;
        const id = this.currentAnalysis.analysis_id;
        const shareUrl = `${window.location.origin}/api/report/${id}?format=html`;
        const shareTitle = `CodePulse Audit: ${this.currentAnalysis.filename}`;
        const shareText = `Code Quality Score: ${this.currentAnalysis.summary.quality_score}/100 (Grade ${this.currentAnalysis.summary.score_grade}) - Findings: ${this.currentAnalysis.issues.length}`;

        if (navigator.share) {
            try {
                await navigator.share({
                    title: shareTitle,
                    text: shareText,
                    url: shareUrl
                });
                this.showToast('Report shared successfully.');
            } catch (err) {
                if (err.name !== 'AbortError') {
                    this.copyShareLink();
                }
            }
        } else {
            this.copyShareLink();
        }
    }

    downloadSelectedFormat() {
        if (!this.currentAnalysis) {
            this.showToast('No active analysis to download.', 'error');
            return;
        }

        const id = this.currentAnalysis.analysis_id;
        const format = this.selectedExportFormat || 'pdf';

        if (format === 'zip') {
            if (this.reportComparison) {
                this.downloadAllReportsPackage();
            } else {
                // Single download fallback
                window.open(`/api/report/${id}?format=json&download=true`, '_blank');
                this.showToast('Downloading report archive...');
            }
            this.closeShareModal();
            return;
        }

        if (format === 'pdf') {
            window.open(`/api/report/${id}?format=html`, '_blank');
            this.showToast('Opening print dialog to save as PDF on your PC...');
            setTimeout(() => {
                this.closeShareModal();
            }, 600);
            return;
        }

        const downloadUrl = `/api/report/${id}?format=${format}&download=true`;
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.setAttribute('download', `CodePulse_Report_${id}.${format}`);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        this.showToast(`📥 Saving CodePulse_Report_${id}.${format} to your PC's Downloads folder...`);
        setTimeout(() => {
            this.closeShareModal();
        }, 800);
    }

    resetWorkspace() {
        document.getElementById('results-container').classList.add('hidden');
        document.getElementById('execution-card').classList.add('hidden');
        document.getElementById('ai-fix-preview-card').classList.add('hidden');
        document.getElementById('comparison-dashboard-card').classList.add('hidden');
        document.getElementById('input-card').classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast-msg';
        toast.innerHTML = `<span>${type === 'error' ? '⚠️' : 'ℹ️'}</span> ${message}`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 3200);
    }

    animateCounter(id, target, duration) {
        const el = document.getElementById(id);
        if (!el) return;
        const startTime = performance.now();
        const update = (now) => {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            el.innerText = Math.floor(progress * target);
            if (progress < 1) requestAnimationFrame(update);
            else el.innerText = target;
        };
        requestAnimationFrame(update);
    }

    escapeHtml(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

// Initialize CodePulse singleton
window.app = new CodePulseApp();
