"""
parser.py — Language-Agnostic Pluggable Parser & AST Mutation Adapters
=====================================================================
Contains the abstract interface and standard AST adapters for identifying
and applying syntactic mutations.
"""

import ast
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseASTAdapter(ABC):
    """Abstract Base Class for language-specific AST manipulation and mutation generation."""

    @abstractmethod
    def parse_mutations(self, file_path: str, file_content: str) -> List[Dict[str, Any]]:
        """
        Scan code content and return candidate mutation records.
        Each candidate dict must include:
           - mutant_id (str)
           - file_path (str)
           - line_number (int)
           - col_offset (int)
           - operator_type (str): e.g. "arithmetic", "comparison", "logical"
           - original_code (str)
           - mutated_value (Any)
           - explanation (str)
        """
        pass

    @abstractmethod
    def apply_mutation(self, file_content: str, mutant_id: str, candidates: List[Dict[str, Any]]) -> str:
        """Apply a selected mutation candidate to the source content and return mutated source."""
        pass


class PythonASTMutationScanner(ast.NodeVisitor):
    """AST Walker that identifies potential mutation locations in Python source code."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.candidates: List[Dict[str, Any]] = []
        self._count = 0

    def _next_id(self) -> str:
        self._count += 1
        return f"mut_{self._count:03d}"

    def visit_BinOp(self, node: ast.BinOp):
        """Handle arithmetic operations: + - * / // % **"""
        op_map = {
            ast.Add: ("sub", "-"),
            ast.Sub: ("add", "+"),
            ast.Mult: ("div", "/"),
            ast.Div: ("mult", "*"),
            ast.FloorDiv: ("mult", "*"),
            ast.Mod: ("mult", "*"),
        }
        node_class = type(node.op)
        if node_class in op_map:
            mut_op_name, mut_op_str = op_map[node_class]
            orig_str = {
                ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
                ast.FloorDiv: "//", ast.Mod: "%"
            }.get(node_class, "?")

            self.candidates.append({
                "mutant_id": self._next_id(),
                "file_path": self.file_path,
                "line_number": node.lineno,
                "col_offset": node.col_offset,
                "operator_type": "arithmetic_substitution",
                "original_code": orig_str,
                "mutated_value": mut_op_name,
                "explanation": f"Swap arithmetic '{orig_str}' with '{mut_op_str}'"
            })
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        """Handle comparison boundaries: < <= > >= == !="""
        comp_map = {
            ast.Lt: ("GtE", ">="),
            ast.LtE: ("Gt", ">"),
            ast.Gt: ("LtE", "<="),
            ast.GtE: ("Lt", "<"),
            ast.Eq: ("NotEq", "!="),
            ast.NotEq: ("Eq", "=="),
        }
        # Simplify checking the first operator
        if node.ops:
            op = node.ops[0]
            node_class = type(op)
            if node_class in comp_map:
                mut_name, mut_str = comp_map[node_class]
                orig_str = {
                    ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=",
                    ast.Eq: "==", ast.NotEq: "!="
                }.get(node_class, "?")

                self.candidates.append({
                    "mutant_id": self._next_id(),
                    "file_path": self.file_path,
                    "line_number": node.lineno,
                    "col_offset": node.col_offset,
                    "operator_type": "relational_operator_replacement",
                    "original_code": orig_str,
                    "mutated_value": mut_name,
                    "explanation": f"Swap comparison boundary '{orig_str}' with '{mut_str}'"
                })
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        """Handle logical connectors: and <-> or"""
        node_class = type(node.op)
        if node_class == ast.And:
            self.candidates.append({
                "mutant_id": self._next_id(),
                "file_path": self.file_path,
                "line_number": node.lineno,
                "col_offset": node.col_offset,
                "operator_type": "boolean_inversion",
                "original_code": "and",
                "mutated_value": "Or",
                "explanation": "Swap logical connective 'and' with 'or'"
            })
        elif node_class == ast.Or:
            self.candidates.append({
                "mutant_id": self._next_id(),
                "file_path": self.file_path,
                "line_number": node.lineno,
                "col_offset": node.col_offset,
                "operator_type": "boolean_inversion",
                "original_code": "or",
                "mutated_value": "And",
                "explanation": "Swap logical connective 'or' with 'and'"
            })
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        """Handle unary boolean inversion by removing explicit 'not'."""
        if isinstance(node.op, ast.Not):
            self.candidates.append({
                "mutant_id": self._next_id(),
                "file_path": self.file_path,
                "line_number": node.lineno,
                "col_offset": node.col_offset,
                "operator_type": "boolean_inversion",
                "original_code": "not",
                "mutated_value": "RemoveNot",
                "explanation": "Remove unary logical negation 'not'"
            })
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        """Handle boundary tweaks (ints) and boolean literal inversion."""
        if isinstance(node.value, bool):
            self.candidates.append({
                "mutant_id": self._next_id(),
                "file_path": self.file_path,
                "line_number": node.lineno,
                "col_offset": node.col_offset,
                "operator_type": "boolean_inversion",
                "original_code": str(node.value),
                "mutated_value": "False" if node.value else "True",
                "explanation": "Invert boolean literal value"
            })
        elif isinstance(node.value, int):
            tweaked = node.value + 1
            self.candidates.append({
                "mutant_id": self._next_id(),
                "file_path": self.file_path,
                "line_number": node.lineno,
                "col_offset": node.col_offset,
                "operator_type": "boundary_value_tweak",
                "original_code": str(node.value),
                "mutated_value": str(tweaked),
                "explanation": f"Adjust integer boundary from {node.value} to {tweaked}"
            })
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return):
        """Handle stripping concrete return values."""
        if node.value is not None:
            self.candidates.append({
                "mutant_id": self._next_id(),
                "file_path": self.file_path,
                "line_number": node.lineno,
                "col_offset": node.col_offset,
                "operator_type": "return_value_stripping",
                "original_code": "return",
                "mutated_value": "StripReturnValue",
                "explanation": "Strip return expression to default None"
            })
        self.generic_visit(node)


class PythonASTMutationModifier(ast.NodeTransformer):
    """AST Transformer that modifies a single matching node to perform the mutation."""

    def __init__(self, target_line: int, target_col: int, operator_type: str, mutated_value: str):
        self.target_line = target_line
        self.target_col = target_col
        self.operator_type = operator_type
        self.mutated_value = mutated_value
        self.applied = False

    def visit_BinOp(self, node: ast.BinOp):
        self.generic_visit(node)
        if node.lineno == self.target_line and node.col_offset == self.target_col:
            op_classes = {
                "sub": ast.Sub(),
                "add": ast.Add(),
                "mult": ast.Mult(),
                "div": ast.Div(),
            }
            if self.mutated_value in op_classes:
                node.op = op_classes[self.mutated_value]
                self.applied = True
        return node

    def visit_Compare(self, node: ast.Compare):
        self.generic_visit(node)
        if node.lineno == self.target_line and node.col_offset == self.target_col:
            comp_classes = {
                "GtE": ast.GtE(),
                "Gt": ast.Gt(),
                "LtE": ast.LtE(),
                "Lt": ast.Lt(),
                "Eq": ast.Eq(),
                "NotEq": ast.NotEq(),
            }
            if self.mutated_value in comp_classes:
                node.ops = [comp_classes[self.mutated_value]]
                self.applied = True
        return node

    def visit_BoolOp(self, node: ast.BoolOp):
        self.generic_visit(node)
        if node.lineno == self.target_line and node.col_offset == self.target_col:
            if self.mutated_value == "Or":
                node.op = ast.Or()
                self.applied = True
            elif self.mutated_value == "And":
                node.op = ast.And()
                self.applied = True
        return node

    def visit_UnaryOp(self, node: ast.UnaryOp):
        self.generic_visit(node)
        if node.lineno == self.target_line and node.col_offset == self.target_col:
            if self.mutated_value == "RemoveNot" and isinstance(node.op, ast.Not):
                self.applied = True
                return node.operand
        return node

    def visit_Constant(self, node: ast.Constant):
        self.generic_visit(node)
        if node.lineno == self.target_line and node.col_offset == self.target_col:
            if isinstance(node.value, bool):
                if self.mutated_value == "True":
                    node.value = True
                    self.applied = True
                elif self.mutated_value == "False":
                    node.value = False
                    self.applied = True
            elif isinstance(node.value, int):
                try:
                    node.value = int(self.mutated_value)
                    self.applied = True
                except ValueError:
                    pass
        return node

    def visit_Return(self, node: ast.Return):
        self.generic_visit(node)
        if node.lineno == self.target_line and node.col_offset == self.target_col:
            if self.mutated_value == "StripReturnValue":
                node.value = None
                self.applied = True
        return node


class PythonASTAdapter(BaseASTAdapter):
    """Fully compliant Python AST Parser and Mutator Adapter."""

    def parse_mutations(self, file_path: str, file_content: str) -> List[Dict[str, Any]]:
        try:
            tree = ast.parse(file_content)
            scanner = PythonASTMutationScanner(file_path)
            scanner.visit(tree)
            return scanner.candidates
        except Exception as e:
            print(f"Error parsing Python AST: {e}")
            return []

    def apply_mutation(self, file_content: str, mutant_id: str, candidates: List[Dict[str, Any]]) -> str:
        match = next((c for c in candidates if c["mutant_id"] == mutant_id), None)
        if not match:
            raise ValueError(f"Mutant ID '{mutant_id}' not found in candidate set.")

        tree = ast.parse(file_content)
        modifier = PythonASTMutationModifier(
            target_line=match["line_number"],
            target_col=match["col_offset"],
            operator_type=match["operator_type"],
            mutated_value=match["mutated_value"]
        )
        modified_tree = modifier.visit(tree)
        ast.fix_missing_locations(modified_tree)
        return ast.unparse(modified_tree)


class TreeSitterAdapter(BaseASTAdapter):
    """
    Template Tree-Sitter Adapter to demonstrate language-agnostic extensibility.
    This would plug into tree-sitter for multiple languages (JS, C/C++, etc.).
    """

    def parse_mutations(self, file_path: str, file_content: str) -> List[Dict[str, Any]]:
        # In a full multi-language setup, this loads language-specific AST query bindings
        # and runsTree-sitter expressions like `((binary_operator) @op)` to generate mutants.
        return []

    def apply_mutation(self, file_content: str, mutant_id: str, candidates: List[Dict[str, Any]]) -> str:
        return file_content


class CppASTAdapter(BaseASTAdapter):
    """
    Highly reliable, dependency-free C++ AST-style Lexical Parser and Mutator.
    Scans C++ files to identify candidate operator coordinates and perform mutations.
    """

    def parse_mutations(self, file_path: str, file_content: str) -> List[Dict[str, Any]]:
        candidates = []
        lines = file_content.splitlines()
        mutant_idx = 0

        # Operator mapping definitions matching Python parser schema
        arithmetic_transitions = {
            "+": ("sub", "-"),
            "-": ("add", "+"),
            "*": ("div", "/"),
            "/": ("mult", "*"),
        }
        comparison_transitions = {
            "<": ("GtE", ">="),
            "<=": ("Gt", ">"),
            ">": ("LtE", "<="),
            ">=": ("Lt", "<"),
            "==": ("NotEq", "!="),
            "!=": ("Eq", "=="),
        }
        logical_transitions = {
            "&&": ("Or", "||"),
            "||": ("And", "&&"),
        }

        in_block_comment = False
        for line_no, line in enumerate(lines, start=1):
            line_strip = line.strip()
            
            if in_block_comment:
                if "*/" in line:
                    in_block_comment = False
                continue
                
            if "/*" in line_strip:
                if "*/" not in line_strip:
                    in_block_comment = True
                continue

            # Ignore single-line comments or preprocessors
            if line_strip.startswith("//") or line_strip.startswith("#"):
                continue

            idx = 0
            while idx < len(line):
                double_op = line[idx:idx+2]
                single_op = line[idx:idx+1]

                matched_op = None
                op_type = None
                mut_name = None
                mut_str = None

                if double_op in comparison_transitions:
                    matched_op = double_op
                    op_type = "relational_operator_replacement"
                    mut_name, mut_str = comparison_transitions[double_op]
                    idx += 2
                elif double_op in logical_transitions:
                    matched_op = double_op
                    op_type = "boolean_inversion"
                    mut_name, mut_str = logical_transitions[double_op]
                    idx += 2
                elif single_op in comparison_transitions:
                    # Guard stream insertion/extraction, templates or include directives
                    if idx + 1 < len(line) and line[idx+1] in ['<', '>', '=']:
                        idx += 1
                        continue
                    if idx > 0 and line[idx-1] in ['<', '>']:
                        idx += 1
                        continue
                    matched_op = single_op
                    op_type = "relational_operator_replacement"
                    mut_name, mut_str = comparison_transitions[single_op]
                    idx += 1
                elif single_op in arithmetic_transitions:
                    # Guard syntax like ++, --, +=, -=
                    if idx + 1 < len(line) and line[idx+1] in ['+', '-', '=']:
                        idx += 1
                        continue
                    if idx > 0 and line[idx-1] in ['+', '-', '*']:
                        idx += 1
                        continue
                    matched_op = single_op
                    op_type = "arithmetic_substitution"
                    mut_name, mut_str = arithmetic_transitions[single_op]
                    idx += 1
                else:
                    idx += 1
                    continue

                if matched_op:
                    mutant_idx += 1
                    candidates.append({
                        "mutant_id": f"mut_cpp_{mutant_idx:03d}",
                        "file_path": file_path,
                        "line_number": line_no,
                        "col_offset": idx - len(matched_op),
                        "operator_type": op_type,
                        "original_code": matched_op,
                        "mutated_value": mut_name,
                        "explanation": f"Swap C++ '{matched_op}' with '{mut_str}'"
                    })

            # Boolean literal inversion
            for match in re.finditer(r"\b(true|false)\b", line):
                token = match.group(1)
                mutant_idx += 1
                candidates.append({
                    "mutant_id": f"mut_cpp_{mutant_idx:03d}",
                    "file_path": file_path,
                    "line_number": line_no,
                    "col_offset": match.start(1),
                    "operator_type": "boolean_inversion",
                    "original_code": token,
                    "mutated_value": "false" if token == "true" else "true",
                    "explanation": f"Invert boolean literal '{token}'"
                })

            # Boundary value tweaks on integer literals
            for match in re.finditer(r"\b\d+\b", line):
                token = match.group(0)
                try:
                    tweaked = str(int(token) + 1)
                except ValueError:
                    continue
                mutant_idx += 1
                candidates.append({
                    "mutant_id": f"mut_cpp_{mutant_idx:03d}",
                    "file_path": file_path,
                    "line_number": line_no,
                    "col_offset": match.start(0),
                    "operator_type": "boundary_value_tweak",
                    "original_code": token,
                    "mutated_value": tweaked,
                    "explanation": f"Adjust numeric boundary from {token} to {tweaked}"
                })

            # Return value stripping for non-string return expressions
            ret_match = re.search(r"\breturn\s+([^;]+);", line)
            if ret_match:
                expr = ret_match.group(1).strip()
                if expr and '"' not in expr and "'" not in expr:
                    expr_col = line.find(expr)
                    if expr_col >= 0:
                        mutant_idx += 1
                        candidates.append({
                            "mutant_id": f"mut_cpp_{mutant_idx:03d}",
                            "file_path": file_path,
                            "line_number": line_no,
                            "col_offset": expr_col,
                            "operator_type": "return_value_stripping",
                            "original_code": expr,
                            "mutated_value": "0",
                            "explanation": "Strip return expression to default scalar value"
                        })

        return candidates

    def apply_mutation(self, file_content: str, mutant_id: str, candidates: List[Dict[str, Any]]) -> str:
        match = next((c for c in candidates if c["mutant_id"] == mutant_id), None)
        if not match:
            raise ValueError(f"Mutant ID '{mutant_id}' not found in candidate set.")

        lines = file_content.splitlines()
        line_idx = match["line_number"] - 1
        col_offset = match["col_offset"]
        orig = match["original_code"]

        op_translation = {
            "sub": "-", "add": "+", "mult": "*", "div": "/",
            "GtE": ">=", "Gt": ">", "LtE": "<=", "Lt": "<",
            "Eq": "==", "NotEq": "!=", "Or": "||", "And": "&&"
        }
        mut_char = op_translation.get(match["mutated_value"], match["mutated_value"])

        if line_idx < 0 or line_idx >= len(lines):
            return file_content

        target_line = lines[line_idx]
        if match.get("operator_type") == "return_value_stripping":
            if col_offset >= 0 and col_offset + len(orig) <= len(target_line):
                lines[line_idx] = target_line[:col_offset] + mut_char + target_line[col_offset + len(orig):]
            else:
                lines[line_idx] = re.sub(r"\breturn\s+[^;]+;", f"return {mut_char};", target_line, count=1)
        elif col_offset >= 0 and col_offset + len(orig) <= len(target_line) and target_line[col_offset : col_offset + len(orig)] == orig:
            lines[line_idx] = target_line[:col_offset] + mut_char + target_line[col_offset + len(orig):]
        else:
            # Fallback inline string swap
            target_line = target_line.replace(orig, mut_char, 1)
            lines[line_idx] = target_line

        return "\n".join(lines)
