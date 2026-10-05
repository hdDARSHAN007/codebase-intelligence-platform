from app.retrieval.hybrid_search import hybrid_search
from app.evaluation.test_set import TEST_QUESTIONS


def is_hit(results: list[dict], correct_symbols: list[str]) -> bool:
    """True if any of the returned chunks is one of the known correct symbols."""
    return any(r["symbol"] in correct_symbols for r in results)


def run():
    hits = 0
    print(f"Running {len(TEST_QUESTIONS)} test questions against hybrid search (top 5)\n")

    for case in TEST_QUESTIONS:
        result = hybrid_search(case["question"], repo=case["repo"], limit=5)
        results = result["results"]
        hit = is_hit(results, case["correct_symbols"])
        hits += hit

        status = "HIT " if hit else "MISS"
        found = ", ".join(r["symbol"] for r in results)
        print(f"[{status}] {case['question']}")
        print(f"       expected one of: {case['correct_symbols']}")
        print(f"       got: {found}\n")

    precision = hits / len(TEST_QUESTIONS)
    print(f"Precision@5: {hits}/{len(TEST_QUESTIONS)} = {precision:.0%}")


if __name__ == "__main__":
    run()