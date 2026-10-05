import re

# A query that is mostly one identifier-like token (has underscores, or is
# camelCase, or is short with no spaces) is probably a symbol lookup.
SYMBOL_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def analyze_query(question: str) -> dict:
    """
    Looks at the shape of a question and returns which search type should
    be trusted more. Doesn't call any search itself.
    """
    stripped = question.strip()
    looks_like_symbol = bool(SYMBOL_PATTERN.match(stripped)) and (
        "_" in stripped or any(c.isupper() for c in stripped[1:])
    )

    if looks_like_symbol:
        return {
            "query_type": "symbol_lookup",
            "vector_pool": 10,
            "keyword_pool": 30,
        }

    return {
        "query_type": "concept",
        "vector_pool": 30,
        "keyword_pool": 10,
    }