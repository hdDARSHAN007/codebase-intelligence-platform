import os

# Directories to skip entirely
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", "target", ".next", ".pytest_cache",
    "vendor", "coverage", ".idea", ".vscode",
}

# File extensions we consider "code" worth parsing
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs",
    ".cpp", ".c", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".sh",
}

# Extensions worth keeping for the "Docs Tool" later, even though not code
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}

def should_skip_dir(dirname: str) -> bool:
    return dirname in IGNORE_DIRS or dirname.startswith(".")

def collect_files(repo_path: str) -> list[dict]:
    """
    Walks the repo, skipping ignored dirs, and returns a list of
    {path, relative_path, extension, kind} for every file worth processing.
    """
    results = []
    for root, dirs, files in os.walk(repo_path):
        # Prune ignored directories in-place so os.walk doesn't descend into them
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]

        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, repo_path)

            if ext in CODE_EXTENSIONS:
                kind = "code"
            elif ext in DOC_EXTENSIONS:
                kind = "doc"
            else:
                continue  # skip binaries, images, lockfiles, etc.

            # Skip huge files (likely generated/minified) — >500KB is a good heuristic
            if os.path.getsize(full_path) > 500_000:
                continue

            results.append({
                "path": full_path,
                "relative_path": rel_path,
                "extension": ext,
                "kind": kind,
            })

    return results