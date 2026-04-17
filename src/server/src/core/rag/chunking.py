import json

from tree_sitter import Language, Parser
import tree_sitter_javascript
from langchain_core.documents import Document


# Setting the Language
JS_LANGUAGE = Language(tree_sitter_javascript.language())

# Initializing the parser
parser = Parser(JS_LANGUAGE)


def extract_js_entities(node, code_bytes, chunks):
    """
    Recursively traverse a tree-sitter AST to extract js entities into structured form 
    """
    def get_text(n):
        if not n: return ""
        return code_bytes[n.start_byte:n.end_byte]
    
    node_type = node.type
    
    # Handle Class Declaration
    if node_type == "class_declaration":
        sig = get_class_signature(node, code_bytes)

        class_fields = []

        for child in node.children:
            if child.type == "class_body":
                for member in child.children:
                    if member.type in ["public_field_definition", "field_definition"]:
                        class_fields.append(get_text(member))
        
        class_code = []
        
        class_code.append(sig)
        class_code.append("{")
        class_code.extend(class_fields)
        class_code.append("}")

        chunks.append({
            "type": "class",
            "name": extract_class_name(node, get_text),
            "code": "\n".join(class_code),
            "byte_range": {"start": node.start_byte, "end": node.end_byte}
        })
        
    # Handle Method Definition
    if node_type == "method_definition":
        # CHANGED: Fallback to positional if field name fails
        name_node = node.child_by_field_name("name") or node.named_child(0)
        chunks.append({
            "type": "method",
            "name": get_text(name_node) or "anonymous",
            "code": get_text(node),
            "byte_range": {"start": node.start_byte, "end": node.end_byte}
        })

    # Handle Function Declarations
    elif node_type == "function_declaration":
        name_node = node.child_by_field_name("name") or node.named_child(0)
        chunks.append({
            "type": "function",
            "name": get_text(name_node) or "anonymous",
            "code": get_text(node)
        })

    # Handle Variables & Imports
    elif node_type == "variable_declarator":
        id_node = node.named_child(0)
        value_node = node.named_child(1) if node.named_child_count > 1 else None
        
        if id_node:
            name = get_text(id_node)
            full_code = get_text(node.parent)
            
            if value_node and value_node.type == "call_expression":
                fn_name = get_text(value_node.named_child(0))
                if fn_name == "require":
                    args = value_node.named_child(1) 
                    source = "unknown"
                    if args:
                        for arg in args.named_children:
                            if "string" in arg.type:
                                source = clean_string(get_text(arg))
                                break
                    
                    if id_node.type == "object_pattern":
                        for shorthand in id_node.named_children:
                            actual_id = shorthand.child_by_field_name("value") or shorthand
                            chunks.append({
                                "type": "import",
                                "name": get_text(actual_id),
                                "source": source,
                                "code": full_code,
                                "byte_range": {"start": node.start_byte, "end": node.end_byte}
                            })
                    else:
                        chunks.append({"type": "import", "name": name, "source": source, "code": full_code, "byte_range": {"start": node.start_byte, "end": node.end_byte}})
                else:
                    chunks.append({"type": "variable", "name": name, "code": full_code, "byte_range": {"start": node.start_byte, "end": node.end_byte}})
            
            elif value_node and value_node.type in ["arrow_function", "function_expression"]:
                chunks.append({"type": "function", "name": name, "code": full_code, "byte_range": {"start": node.start_byte, "end": node.end_byte}})
            else:
                chunks.append({"type": "variable", "name": name, "code": full_code, "byte_range": {"start": node.start_byte, "end": node.end_byte}})

    # Handle Exports/Assignments
    elif node_type == "assignment_expression":
        left = node.named_child(0)
        right = node.named_child(1)
        
        if left and right:
            name = get_text(left)
            full_code = get_text(node) 

            if left.type == "member_expression":
                prop = left.named_child(left.named_child_count - 1)
                obj_text = get_text(left.named_child(0))
                if "exports" in obj_text:
                    name = get_text(prop)

            val_text = get_text(right)
            # Captures functions and wrapped functions (catchAsync)
            if right.type in ["arrow_function", "function_expression"] or "=>" in val_text or "async" in val_text:
                chunks.append({"type": "function", "name": name, "code": full_code, "byte_range": {"start": node.start_byte, "end": node.end_byte}})
            else:
                chunks.append({"type": "variable", "name": name, "code": full_code, "byte_range": {"start": node.start_byte, "end": node.end_byte}})

    # Recursion
    if node_type not in ["function_declaration", "arrow_function", "function_expression", "method_definition"]:
        for child in node.children:
            extract_js_entities(child, code_bytes, chunks)

def split_and_chunk_entities(docs):
    """
    Takes chunks as an argument, generated from extract_js_entities and returns
    them as Document object
    """
    split_docs = []
    
    for doc in docs:
        print(f"Chunking {doc.metadata['source']}")
        code = doc.page_content 
        tree = parser.parse(bytes(code, 'utf-8'))
        root = tree.root_node
        
        chunks = []
        extract_js_entities(root, code, chunks)
        
        doc_chunks = []
        
        # grouping all import statements
        import_statements = [chunk['code'] for chunk in chunks if chunk['type'] == 'import']
        
        if import_statements:
            all_imports = {
                'type': 'import',
                'code': "\n".join(import_statements)
            }
            
            doc_chunks.append(create_doc(json.dumps(all_imports), {
                'source': doc.metadata['source'],
                'source_file': doc.metadata['source_file'],
                'file_type': doc.metadata['file_type']
            }))
            
        for chunk in chunks:
            if chunk['type'] != 'import':
                doc_chunks.append(create_doc(json.dumps(chunk), {
                    'source': doc.metadata['source'],
                    'source_file': doc.metadata['source_file'],
                    'file_type': doc.metadata['file_type'],
                    'byte_range': json.dumps(chunk["byte_range"])
                }))    
        
        split_docs.append(doc_chunks)
    return split_docs

def create_doc(page_content, metadata):
    doc = Document(
        page_content=page_content,
        metadata=metadata
    )
    return doc

def clean_string(s):
    return s.strip().strip('"').strip("'")

def get_class_signature(node, source_code):
    for child in node.children:
        if child.type == "class_body":
            return source_code[node.start_byte:child.start_byte].strip()
    return ""


def extract_class_name(node, fn):
    name_node = node.child_by_field_name("name") or node.named_child(0)
    return fn(name_node) if name_node else "anonymous"