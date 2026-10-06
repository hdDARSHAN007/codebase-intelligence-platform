from app.ingestion.parser import parse_file
from app.ingestion.chunker import extract_chunks
import tempfile
import os


def _chunk_source(code: str, language: str, filename: str):
    """Writes code to a temp file, parses it, and returns its chunks."""
    suffix = {"python": ".py", "javascript": ".js", "typescript": ".ts", "java": ".java"}[language]
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(code)
        tree, source_bytes = parse_file(path, language)
        return extract_chunks(tree, source_bytes, filename, language)
    finally:
        os.remove(path)


def test_decorator_is_included_in_chunk_text():
    code = '''
class Foo:
    @property
    def bar(self):
        return 1
'''
    chunks = _chunk_source(code, "python", "foo.py")
    method = next(c for c in chunks if c.symbol_name == "bar")
    assert method.text.strip().startswith("@property")


def test_nested_class_parent_is_correct():
    code = '''
class Outer:
    class Inner:
        def inner_method(self):
            pass

    def outer_method(self):
        pass
'''
    chunks = _chunk_source(code, "python", "nested.py")

    outer = next(c for c in chunks if c.symbol_name == "Outer")
    inner = next(c for c in chunks if c.symbol_name == "Inner")
    inner_method = next(c for c in chunks if c.symbol_name == "inner_method")
    outer_method = next(c for c in chunks if c.symbol_name == "outer_method")

    assert outer.parent_class is None
    assert inner.parent_class is None
    assert inner_method.parent_class == "Inner"
    assert outer_method.parent_class == "Outer"


def test_nested_function_not_extracted_separately():
    code = '''
def outer(f):
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper
'''
    chunks = _chunk_source(code, "python", "wrap.py")
    names = [c.symbol_name for c in chunks]
    assert "outer" in names
    assert "wrapper" not in names


def test_empty_file_produces_no_chunks():
    chunks = _chunk_source("", "python", "empty.py")
    assert chunks == []


def test_js_named_arrow_function_is_captured():
    code = '''
const add = (a, b) => {
  return a + b;
};
'''
    chunks = _chunk_source(code, "javascript", "math.js")
    names = [c.symbol_name for c in chunks]
    assert "add" in names


def test_js_arrow_function_as_call_argument_is_captured():
    code = '''
test('adds numbers', () => {
  console.log(1 + 1);
});
'''
    chunks = _chunk_source(code, "javascript", "test.js")
    names = [c.symbol_name for c in chunks]
    assert "adds numbers" in names

def test_java_constructor_and_interface():
    code = '''
    public class Calculator {
        public Calculator() {}
        public int add(int a, int b) { return a + b; }
        interface Operation {
            int apply(int x, int y);
        }
    }
    '''
    chunks = _chunk_source(code, "java", "calc.java")

    calculator_class = next(c for c in chunks if c.symbol_name == "Calculator" and c.symbol_type == "class")
    constructor = next(c for c in chunks if c.symbol_name == "Calculator" and c.symbol_type == "method")
    add_method = next(c for c in chunks if c.symbol_name == "add")
    operation = next(c for c in chunks if c.symbol_name == "Operation")
    apply_method = next(c for c in chunks if c.symbol_name == "apply")

    assert calculator_class.parent_class is None
    assert constructor.parent_class == "Calculator"
    assert add_method.parent_class == "Calculator"
    assert operation.symbol_type == "class"
    assert apply_method.parent_class == "Operation"