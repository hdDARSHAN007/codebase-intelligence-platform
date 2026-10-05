EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp", ".c": "c", ".h": "c", ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "shell",
}

def detect_language(extension: str) -> str:
    return EXTENSION_TO_LANGUAGE.get(extension, "unknown")

def summarize_languages(files: list[dict]) -> dict:
    """Returns {language: file_count} for a quick repo overview."""
    summary = {}
    for f in files:
        if f["kind"] != "code":
            continue
        lang = detect_language(f["extension"])
        summary[lang] = summary.get(lang, 0) + 1
    return summary