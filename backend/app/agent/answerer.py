import os
import time
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-3.5-flash-lite"
MAX_RETRIES = 4
WAIT_SECONDS = 15
MAX_TOOL_CALLS = 2

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


TOOLS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="search_more",
            description="Search the repository again with a different, more specific question, when the current code excerpts don't fully answer the user's question.",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "A new, more specific search query."}},
                "required": ["query"],
            },
        ),
        types.FunctionDeclaration(
            name="read_file",
            description="Read every chunk already stored for one exact file path, when you know which file has the answer but don't have enough of it yet.",
            parameters={
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "The exact file path, as shown in an excerpt's File: line."}},
                "required": ["file_path"],
            },
        ),
    ])
]


def _format_chunks(chunks: list[dict], start_index: int) -> tuple[str, int]:
    blocks = []
    i = start_index
    for c in chunks:
        where = f'in class {c["parent_class"]}' if c.get("parent_class") else ""
        blocks.append(
            f'[{i}] {c["type"].upper()} {c["symbol"]} {where}\n'
            f'File: {c["file"]} (lines {c["lines"]})\n'
            f'```\n{c["text"]}\n```'
        )
        i += 1
    return "\n\n".join(blocks), i


def _call_with_retry(client, contents):
    for attempt in range(MAX_RETRIES):
        try:
            return client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(tools=TOOLS),
            )
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"[answerer] Gemini call failed ({e}); waiting {WAIT_SECONDS}s and retrying...")
            time.sleep(WAIT_SECONDS)


def answer_question(question: str, chunks: list[dict], repo: str) -> dict:
    """
    Answers using the given chunks. The model may call search_more or
    read_file up to MAX_TOOL_CALLS times first, if the given chunks
    aren't enough, then writes a final cited answer.
    """
    from app.retrieval.search import vector_search
    from app.retrieval.file_lookup import get_file_chunks

    if not chunks:
        return {"answer": "I couldn't find any relevant code for this question in the repository.", "sources": []}

    all_chunks = list(chunks)
    context, next_index = _format_chunks(all_chunks, 1)

    system_prompt = """You are a code assistant answering questions about a GitHub repository.
Use ONLY the code excerpts to answer. Cite the excerpt number (like [1]) for every claim you make.
If the excerpts don't fully answer the question, call search_more or read_file to get what's missing,
rather than guessing or saying information is unavailable. Once you have enough, write the final answer."""

    contents = [
        types.Content(role="user", parts=[types.Part(text=f"{system_prompt}\n\nCode excerpts:\n{context}\n\nQuestion: {question}")])
    ]

    client = get_client()
    tool_calls_made = 0

    while True:
        response = _call_with_retry(client, contents)
        part = response.candidates[0].content.parts[0]

        if part.function_call and tool_calls_made < MAX_TOOL_CALLS:
            tool_calls_made += 1
            call = part.function_call
            args = dict(call.args)

            if call.name == "search_more":
                new_chunks = vector_search(args["query"], limit=5, repo=repo)
            elif call.name == "read_file":
                new_chunks = get_file_chunks(repo, args["file_path"])
            else:
                new_chunks = []

            new_block, next_index = _format_chunks(new_chunks, next_index)
            all_chunks.extend(new_chunks)

            contents.append(types.Content(role="model", parts=[part]))
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_function_response(
                    name=call.name,
                    response={"result": new_block or "No additional results found."},
                )],
            ))
            continue

        break

    seen = set()
    sources = []
    for c in all_chunks:
        key = (c["file"], c["lines"])
        if key in seen:
            continue
        seen.add(key)
        sources.append({"ref": len(sources) + 1, "file": c["file"], "lines": c["lines"], "symbol": c["symbol"]})

    return {"answer": response.text, "sources": sources}