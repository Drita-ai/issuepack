import os
import io
from contextlib import redirect_stdout

from tree_sitter import Language, Parser
import tree_sitter_javascript

from .file_explorer import _get_all_files, _read_file_contents, get_directory_tree


# Setting the Language
JS_LANGUAGE = Language(tree_sitter_javascript.language())

# Initializing the parser
parser = Parser(JS_LANGUAGE)

def skeletonize(root_dir):
    # Get all files to skeletonize
    all_files = list(_get_all_files(root_dir)) 
    
    # Get file contents
    file_contents = _read_file_contents(all_files)
    
    skeletonized_contents = []
    
    # Add directory structure
    dir_tree = get_directory_tree(root_dir)
    skeletonized_contents.append(f"--- Directory structure ---\n{dir_tree}")
    
    for content in file_contents:
        skeleton = _generate_file_skeleton(content)
        
        formatted_skeleton = f"--- File: {content['file_name']} ---\n{skeleton}"
        skeletonized_contents.append(formatted_skeleton)
    
    separator = "\n\n" + "="*40 + "\n\n" 
    final_text = separator.join(skeletonized_contents)
    
    output_filename = "skeleton.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_text)
        
    print(f"Success! Final skeleton saved to: {os.path.abspath(output_filename)}")

def _generate_file_skeleton(file_data):
    # only include file with js extension (as ERROR with DOCKERFILE)
    syntax_tree = parser.parse(bytes(file_data['file_content'], 'utf-8'))
    root_node = syntax_tree.root_node
    
    output_segments = []
    
    __skeletonize(root_node, file_data['file_content'], output_segments)
    
    return "\n".join(output_segments)

# TODO: Same what's done for variable_declarator needs to be done for 
# assignment_expression, if possible ?
def __skeletonize(root, content, chunks):
    def __extract_node_pair():
        name_node = root.named_child(0)
        value_node = root.named_child(1) if root.named_child_count > 1 else None
        
        return [name_node, value_node]
        
    def __get_text(node):
        return (node.text).decode('utf-8') if hasattr(node, 'text') else ''
    
    # TODO: look into fns which are too shortened
    def __skeletonize_arrow_fn(node, identifier, is_const_declared=True):
        # Check if fn is async or not
        async_modifier = "async" if __get_text(node.children[0]) == "async" else ''
        parameter_string = __get_text(node.named_child(0))
        
        # TODO: programatically extract const/let 
        skeletonized_fn = f'{"const" if is_const_declared else ""} {identifier} = {async_modifier} {parameter_string} {{...}}'
        
        return skeletonized_fn.strip()
    
    def __skeletonize_call_expression(identifier, call_exp_identifier, is_const_declared=True):
        return f'{"const" if is_const_declared else ""} {identifier} = {call_exp_identifier}(...)'.strip()

    def __skeletonize_new_fn(node, identifier):
        node_name = __get_text(node.named_child(0))
         
        return f'const {identifier} = new {node_name}(...)'
    
    def __skeletonize_standard_fn(node, identifier):
        async_modifier = "async" if __get_text(node.children[0]) == "async" else ''
        params_string = __get_text(node.named_child(0))
        
        return f'{identifier} = {async_modifier} function {params_string} {{...}}'
    
    def __skeletonize_method(node):
        method_segments = []
        
        method_name = __get_text(node.named_child(0))
        
        if method_name == "constructor":
            method_segments.append(__get_text(node))

        elif method_name != 'constructor':
            method_segments.append(f'{method_name}{__get_text(node.named_child(1))} {{...}}')
        
        # TODO: getter and setter
        return method_segments
        
    def __skeletonize_class(node):
        class_fields = []
        
        for child in node.children:
            if child.type == "class_body":
                for member in child.children:
                    if member.type in ["public_field_definition", "field_definition"]:
                        class_fields.append(__get_text(member))
                        
                    if member.type in ["method_definition"]:
                        class_fields.extend(__skeletonize_method(member))
                        
        return class_fields
    
    current_type = root.type
    
    _code = __get_text(root)
    
    if current_type == "variable_declarator": 
        name_node, value_node = __extract_node_pair()
        
        if name_node:
            identifier_name = __get_text(name_node)
            
            # import statements
            # if "require" in _code: 
            #     chunks.append(__get_text(root.parent))
            #     _flag = True
            
            # For simple arrow fn 
            # const a = (a,b) => {...}
            if value_node: 
                if value_node.type == "arrow_function":
                    chunks.append(__skeletonize_arrow_fn(value_node, identifier_name))
                    return

                # TODO: have to look out for call expressions with too much stuffs inside it
                elif value_node.type == "call_expression":
                    chunks.append(__get_text(root.parent))
                    return
                
                elif value_node.type == "binary_expression":
                    chunks.append(__get_text(root.parent))
                    return
                
                elif value_node.type == "new_expression":
                    chunks.append(__skeletonize_new_fn(value_node, identifier_name))
                    return
    
    elif current_type == "assignment_expression":
        left_node, right_node = __extract_node_pair()
        
        if left_node and right_node:
            # for exports like : exports.signup
            if left_node.type == "member_expression":
                # Flag to check whether to add const while forming skeleton or not
                _has_const = False
                identifier_name = __get_text(left_node)
                
                if identifier_name == "module.exports" and "function" not in right_node.type :
                    chunks.append(__get_text(root))
                    return
                
                # TODO: implementation for async 
                # eg. - async catchAsync(...)
                
                # for fn like : catchAsync(async (req,res,next) => {...})
                if right_node.type == "call_expression":
                    call_exp_identifier = __get_text(right_node.named_child(0))
                    chunks.append(__skeletonize_call_expression(identifier_name, call_exp_identifier, _has_const))
                    return
                
                elif right_node.type == "arrow_function":
                    chunks.append(__skeletonize_arrow_fn(right_node, identifier_name, _has_const))
                    return
                
                elif right_node.type == "function_expression":
                    chunks.append(__skeletonize_standard_fn(right_node, identifier_name))
                    return
    
    elif current_type == "class_declaration":
        class_structure = []
        
        class_name = __get_text(root.named_child(0))
        inheritance_suffix = __get_text(root.named_child(1)) if __get_text(root.named_child(1)) == "class_heritage" else ''

        class_structure.append(f'class {class_name} {inheritance_suffix}')
        class_structure.append('{')
        class_structure.extend(__skeletonize_class(root))
        class_structure.append('}')
        
        chunks.extend(class_structure)
        return
            
    elif current_type == "if_statement":
        chunks.append(_code)
        return
    
    elif current_type == "call_expression":
        chunks.append(_code)
        return

    if current_type not in ["function_declaration", "arrow_function", "function_expression", "method_definition"]:
        for child in root.children:
            __skeletonize(child, content, chunks) 
