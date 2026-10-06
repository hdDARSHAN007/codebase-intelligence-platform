from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
import tree_sitter_java as tsjava

# Build Language objects once, reuse across all parsing calls
LANGUAGES = {
    "python": Language(tspython.language()),
    "javascript": Language(tsjavascript.language()),
    "typescript": Language(tstypescript.language_typescript()),
    "java": Language(tsjava.language()),
}

_parsers: dict[str, Parser] = {}

def get_parser(language: str) -> Parser | None:
    """Returns a cached Parser for the given language, or None if unsupported."""
    if language not in LANGUAGES:
        return None

    if language not in _parsers:
        parser = Parser(LANGUAGES[language])
        _parsers[language] = parser

    return _parsers[language]

def parse_file(file_path: str, language: str):
    """
    Reads a file and returns its tree-sitter parse tree, or None
    if the language isn't supported yet.
    """
    parser = get_parser(language)
    if parser is None:
        return None

    with open(file_path, "rb") as f:
        source_bytes = f.read()

    tree = parser.parse(source_bytes)
    return tree, source_bytes