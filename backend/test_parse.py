from app.ingestion.parser import parse_file
from app.ingestion.chunker import extract_chunks

code = """
public class Calculator {
    private int total;

    public Calculator() {
        this.total = 0;
    }

    public int add(int a, int b) {
        return a + b;
    }

    interface Operation {
        int apply(int x, int y);
    }
}
"""

with open("test_java_sample.java", "w") as f:
    f.write(code)

result = parse_file("test_java_sample.java", "java")
if result:
    tree, source_bytes = result
    chunks = extract_chunks(tree, source_bytes, "test_java_sample.java", "java")
    print(f"Found {len(chunks)} chunks\n")
    for c in chunks:
        print(f"[{c.symbol_type}] {c.symbol_name}  parent_class={c.parent_class}  (lines {c.start_line}-{c.end_line})")