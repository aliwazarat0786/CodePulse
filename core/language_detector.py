"""
Language detection module for CodePulse AI.
Supports Mode A (manual selection) and Mode B (extension & content heuristics).
"""
import re
from typing import Tuple

EXTENSION_MAP = {
    ".py": "python",
    ".pyw": "python",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".hh": "cpp",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "javascript",
    ".tsx": "javascript",
    ".sql": "sql",
    ".pgsql": "sql",
    ".psql": "sql",
    ".mysql": "sql",
    ".sqlite": "sql"
}

GENERIC_FILENAMES = {
    "snippet.py", "snippet.js", "snippet.c", "snippet.cpp", "snippet.java", "snippet.sql",
    "snippet.txt", "snippet", "example.py", "test.py", "code.txt", "untitled", ""
}

def detect_language(filename: str, source_code: str, requested_lang: str = "auto") -> Tuple[str, float, str]:
    """
    Detect language using extension and deep content heuristics.
    Returns: (language_name, confidence, reason)
    """
    req = (requested_lang or "").strip().lower()
    if req and req != "auto" and req in ["python", "java", "c", "cpp", "javascript", "sql"]:
        return req, 1.0, "Manually specified"

    clean_fn = (filename or "").strip().lower()
    code = source_code.strip() if source_code else ""

    # If code is empty and a non-generic filename is given, match extension
    if not code:
        if clean_fn:
            for ext, lang in EXTENSION_MAP.items():
                if clean_fn.endswith(ext):
                    return lang, 0.95, f"Matched file extension '{ext}'"
        return "python", 0.1, "Default fallback for empty content"

    # Step 1: Content Signature Analysis
    scores = {
        "python": 0,
        "javascript": 0,
        "java": 0,
        "cpp": 0,
        "c": 0,
        "sql": 0
    }

    code_upper = code.upper()

    # --- SQL / PostgreSQL / MySQL / SQLite Signatures ---
    if re.search(r'\b(SELECT\s+.*?\s+FROM|INSERT\s+INTO\s+\w+|UPDATE\s+\w+\s+SET|DELETE\s+FROM\s+\w+)\b', code_upper):
        scores["sql"] += 60
    if re.search(r'\b(CREATE\s+(TABLE|FUNCTION|PROCEDURE|VIEW|INDEX|DATABASE|TRIGGER)|ALTER\s+TABLE|DROP\s+(TABLE|DATABASE|VIEW|INDEX))\b', code_upper):
        scores["sql"] += 60
    if re.search(r'\b(PRIMARY\s+KEY|FOREIGN\s+KEY|REFERENCES\s+\w+|VARCHAR|TIMESTAMPTZ|PLPGSQL|LANGUAGE\s+PLPGSQL|SERIAL\s+PRIMARY\s+KEY)\b', code_upper):
        scores["sql"] += 50
    if re.search(r'\b(GROUP\s+BY|ORDER\s+BY|HAVING|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|CROSS\s+JOIN|UNION\s+ALL)\b', code_upper):
        scores["sql"] += 45
    if re.search(r'^\s*--(.*?)$', code, re.MULTILINE):
        scores["sql"] += 35
    if re.search(r'\b(BEGIN\s+TRANSACTION|COMMIT;|ROLLBACK;|RETURNS\s+(SETOF|TABLE|VOID|TRIGGER)|END;\s*\$\$\s*LANGUAGE)\b', code_upper):
        scores["sql"] += 50

    # --- Python / Django / Flask / FastAPI Signatures ---
    if re.search(r'^\s*def\s+[a-zA-Z_]\w*\s*\(.*?\):', code, re.MULTILINE):
        scores["python"] += 50
    if re.search(r'^\s*class\s+[a-zA-Z_]\w*(\(.*?\))?:', code, re.MULTILINE) and "{" not in code:
        scores["python"] += 40
    if re.search(r'^\s*(from\s+[\w.]+\s+import\s+[\w.*, ]+|import\s+[\w., ]+)', code, re.MULTILINE):
        scores["python"] += 40
    if re.search(r'\b(elif|except|self|__init__|__name__|None|True|False)\b', code):
        scores["python"] += 30
    if re.search(r'@(app\.(route|get|post|put|delete)|router\.|csrf_exempt|classmethod|staticmethod|property|login_required)\b', code):
        scores["python"] += 45
    if re.search(r'\b(django|flask|fastapi|sqlalchemy|pymongo|pydantic|render_template_string|render_template|models\.Model|models\.CharField)\b', code):
        scores["python"] += 45
    if "print(" in code and ";" not in code:
        scores["python"] += 20
    if re.search(r':\s*$', code, re.MULTILINE) and "{" not in code and "}" not in code:
        scores["python"] += 20

    # --- JavaScript / TypeScript / React / Node.js / MongoDB Signatures ---
    if re.search(r'\b(const|let|var)\s+([a-zA-Z_$][\w$]*|\{[^}]+\}|\[[^\]]+\])\s*=', code):
        scores["javascript"] += 50
    if re.search(r'function\s+[a-zA-Z_$][\w$]*\s*\(|=>\s*\{|=>', code):
        scores["javascript"] += 45
    if re.search(r'\bimport\s+.*?from\s+[\'"][^\'"]+[\'"]', code):
        scores["javascript"] += 45
    if re.search(r'\b(document\.|window\.|console\.(log|warn|error)|addEventListener|querySelector|getElementById)\b', code):
        scores["javascript"] += 50
    if re.search(r'\b(useState|useEffect|useContext|useReducer|useCallback|useMemo|useRef|dangerouslySetInnerHTML)\b', code):
        scores["javascript"] += 55
    if re.search(r'\b(module\.exports|export\s+default|export\s+const|require\(["\'])', code):
        scores["javascript"] += 45
    if re.search(r'\b(express\(\)|app\.(use|get|post|put|delete)\(|mongoose\.model|mongoose\.Schema|jwt\.sign|\$where)\b', code):
        scores["javascript"] += 50
    if "===" in code or "!==" in code:
        scores["javascript"] += 35
    if re.search(r'<\/?([A-Z]\w+|div|span|button|input|section|main|p|h[1-6])(\s+[^>]*)?>', code) and "class" in code:
        scores["javascript"] += 35

    # --- Java / Spring Signatures ---
    if re.search(r'public\s+(final\s+|abstract\s+)?class\s+\w+', code):
        scores["java"] += 60
    if re.search(r'public\s+static\s+void\s+main\s*\(\s*String\s*(\[\s*\]|\.\.\.)\s*\w+\s*\)', code):
        scores["java"] += 65
    if "System.out.print" in code or "System.err.print" in code:
        scores["java"] += 50
    if re.search(r'^\s*package\s+[a-zA-Z0-9_.]+;', code, re.MULTILINE):
        scores["java"] += 50
    if re.search(r'^\s*import\s+java\.', code, re.MULTILINE) or re.search(r'^\s*import\s+org\.springframework', code, re.MULTILINE):
        scores["java"] += 45
    if re.search(r'@(SpringBootApplication|RestController|Service|Repository|Autowired|Override|GetMapping|PostMapping)\b', code):
        scores["java"] += 50
    if re.search(r'\b(public|private|protected)\s+(static\s+)?(void|int|double|String|boolean|float|List<[^>]+>|Map<[^>]+>)\s+\w+\s*\(', code):
        scores["java"] += 40

    # --- C++ Signatures ---
    if re.search(r'#include\s+<(iostream|vector|memory|string|map|algorithm|thread|mutex)>', code):
        scores["cpp"] += 60
    if "std::cout" in code or "std::cin" in code or "std::endl" in code or "std::string" in code or "std::make_unique" in code or "std::vector" in code:
        scores["cpp"] += 55
    if re.search(r'\b(namespace\s+\w+|template\s*<|nullptr|constexpr|std::|std::shared_ptr|std::unique_ptr)\b', code):
        scores["cpp"] += 50
    if "using namespace std;" in code or "cout <<" in code or "cin >>" in code:
        scores["cpp"] += 50

    # --- C Signatures ---
    if re.search(r'#include\s+<(stdio\.h|stdlib\.h|string\.h|unistd\.h|stdbool\.h|pthread\.h)>', code):
        scores["c"] += 55
        scores["cpp"] += 15
    if re.search(r'\b(printf|scanf|malloc|calloc|realloc|free|strcpy|strlen|strncpy|fopen|fgets)\s*\(', code):
        scores["c"] += 40
        scores["cpp"] += 10
    if re.search(r'\bint\s+main\s*\(\s*(void|int\s+argc)?', code):
        scores["c"] += 30
        scores["cpp"] += 20
    if re.search(r'\bstruct\s+\w+\s*\{', code) and "class" not in code and "public" not in code:
        scores["c"] += 30

    # If code contains high Python or JS/C/Java host signals, reduce false SQL score from SQL strings
    host_scores = [scores["python"], scores["javascript"], scores["java"], scores["cpp"], scores["c"]]
    max_host = max(host_scores)
    if max_host >= 60 and scores["sql"] < 100:
        # Host language code embedding raw SQL strings should be classified as the host language
        if scores["python"] >= 40:
            scores["sql"] = min(scores["sql"], scores["python"] - 10)
        elif scores["javascript"] >= 40:
            scores["sql"] = min(scores["sql"], scores["javascript"] - 10)
        elif scores["java"] >= 40:
            scores["sql"] = min(scores["sql"], scores["java"] - 10)

    best_lang = max(scores, key=scores.get)
    max_score = scores[best_lang]

    # If content gives a clear match (>= 30), prefer it over generic extension
    if max_score >= 30:
        confidence = min(0.99, max_score / 60.0)
        return best_lang, round(confidence, 2), f"Syntax heuristic match score {max_score}"

    # Step 2: Fallback to non-generic filename extension
    clean_fn = (filename or "").strip().lower()
    if clean_fn and clean_fn not in GENERIC_FILENAMES:
        for ext, lang in EXTENSION_MAP.items():
            if clean_fn.endswith(ext):
                return lang, 0.90, f"Matched file extension '{ext}'"

    # Step 3: Best heuristic with lower threshold
    if max_score > 0:
        return best_lang, 0.65, f"Partial pattern match score {max_score}"

    return "python", 0.40, "Default fallback; language could not be determined unambiguously"
