from dataclasses import dataclass, field

@dataclass
class Chunk:
    text: str                # the actual code
    symbol_name: str         # function/class name
    symbol_type: str         # "function" or "class" or "method"
    file_path: str
    start_line: int
    end_line: int
    language: str
    parent_class: str | None = None   # if this is a method, its class name
    imports: list[str] = field(default_factory=list)

# Node types that represent a "chunkable" unit, per language
CHUNK_NODE_TYPES = {
    "python": {"function_definition", "class_definition"},
    "javascript": {"function_declaration", "class_declaration", "method_definition", "variable_declarator"},
    "typescript": {"function_declaration", "class_declaration", "method_definition", "variable_declarator"},
    "java": {"method_declaration", "class_declaration", "interface_declaration", "constructor_declaration"},
}

# Node types that count as a "class"-like container whose children we
# should keep recursing into (to find methods inside them).
CLASS_LIKE_TYPES = {"class_definition", "class_declaration", "interface_declaration"}

def get_node_text(node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

def get_symbol_name(node, source_bytes: bytes) -> str | None:
    """Finds the 'name' child node (function/class identifier)."""
    for child in node.children:
        if child.type in ("identifier", "type_identifier"):
            return get_node_text(child, source_bytes)
    return None

def is_function_value_declarator(node) -> bool:
    """
    True if this variable_declarator's value is an arrow_function or
    function_expression, e.g. `const foo = () => {}` or
    `const foo = function() {}`. False for `const x = 5` etc.
    """
    if node.type != "variable_declarator":
        return False
    for child in node.children:
        if child.type in ("arrow_function", "function_expression"):
            return True
    return False


def find_call_with_function_arg(node):
    """
    If this node is a call_expression with a function/arrow_function
    argument (e.g. test('main', t => {...})), returns
    (call_node, function_arg_node, inferred_name).
    Otherwise returns None.
    """
    if node.type != "call_expression":
        return None

    call_name = None
    string_name = None
    function_arg = None

    for child in node.children:
        if child.type in ("identifier", "member_expression"):
            call_name = child.text.decode("utf-8", errors="replace")
        if child.type == "arguments":
            for arg in child.children:
                if arg.type == "string":
                    # strip quotes from the string literal
                    string_name = arg.text.decode("utf-8", errors="replace").strip("'\"")
                if arg.type in ("arrow_function", "function_expression"):
                    function_arg = arg

    if function_arg is None:
        return None

    inferred_name = string_name or call_name or "<anonymous>"
    return (node, function_arg, inferred_name)

def extract_imports(root_node, source_bytes: bytes, language: str) -> list[str]:
    """Grabs top-level import statements to attach as context."""
    import_types = {"import_statement", "import_from_statement"}
    imports = []
    for child in root_node.children:
        if child.type in import_types:
            imports.append(get_node_text(child, source_bytes).strip())
    return imports


def extract_chunks(tree, source_bytes: bytes, file_path: str, language: str) -> list[Chunk]:
    chunk_types = CHUNK_NODE_TYPES.get(language, set())
    if not chunk_types:
        return []

    root = tree.root_node
    imports = extract_imports(root, source_bytes, language)
    chunks: list[Chunk] = []

    def get_chunk_node(node):
        """
        If this node is wrapped in a decorated_definition (i.e. it has
        decorators above it), return that wrapper node instead, so the
        chunk text includes the @decorator lines. Otherwise return the
        node itself.
        """
        if node.parent is not None and node.parent.type == "decorated_definition":
            return node.parent
        return node

    def walk(node, parent_class: str | None = None):
        for child in node.children:
            is_plain_chunk_type = child.type in (
                "function_declaration", "class_declaration", "method_definition",
                "function_definition", "class_definition",
                "method_declaration", "interface_declaration", "constructor_declaration",
            )
            is_named_function_var = is_function_value_declarator(child)
            call_with_fn = find_call_with_function_arg(child) if child.type == "call_expression" else None

            if is_plain_chunk_type or is_named_function_var:
                name = get_symbol_name(child, source_bytes) or "<anonymous>"
                chunk_node = get_chunk_node(child)
                is_class_like = child.type in CLASS_LIKE_TYPES

                if is_class_like:
                    symbol_type = "class"
                    chunk_parent = None
                    recurse_parent = name
                elif parent_class:
                    symbol_type = "method"
                    chunk_parent = parent_class
                    recurse_parent = parent_class
                else:
                    symbol_type = "function"
                    chunk_parent = None
                    recurse_parent = None

                chunks.append(Chunk(
                    text=get_node_text(chunk_node, source_bytes),
                    symbol_name=name,
                    symbol_type=symbol_type,
                    file_path=file_path,
                    start_line=chunk_node.start_point[0] + 1,
                    end_line=chunk_node.end_point[0] + 1,
                    language=language,
                    parent_class=chunk_parent,
                    imports=imports,
                ))

                if is_class_like:
                    walk(child, parent_class=recurse_parent)

            elif call_with_fn is not None:
                call_node, function_arg_node, inferred_name = call_with_fn
                chunks.append(Chunk(
                    text=get_node_text(call_node, source_bytes),
                    symbol_name=inferred_name,
                    symbol_type="function",
                    file_path=file_path,
                    start_line=call_node.start_point[0] + 1,
                    end_line=call_node.end_point[0] + 1,
                    language=language,
                    parent_class=parent_class,
                    imports=imports,
                ))
                # Don't recurse further into this call — we've captured
                # the whole thing (including the arrow function body) as
                # one chunk already.

            else:
                walk(child, parent_class=parent_class)

    walk(root)
    return chunks