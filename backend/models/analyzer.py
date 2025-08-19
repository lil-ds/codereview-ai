# backend/models/analyzer.py
import ast
import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class CodeIssue:
    line_number: int
    issue_type: str
    severity: str  # "error", "warning", "info"
    message: str
    suggestion: str = ""

class PythonCodeAnalyzer:
    def __init__(self):
        self.issues = []
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Main analysis function that returns structured feedback"""
        self.issues = []
        
        try:
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # Run various analysis checks
            self._check_function_length(tree, code)
            self._check_missing_docstrings(tree)
            self._check_unused_imports(tree, code)
            self._check_complex_conditions(tree)
            self._check_naming_conventions(tree)
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score()
            
            return {
                "quality_score": quality_score,
                "issues": [
                    {
                        "line": issue.line_number,
                        "type": issue.issue_type,
                        "severity": issue.severity,
                        "message": issue.message,
                        "suggestion": issue.suggestion
                    }
                    for issue in self.issues
                ],
                "total_issues": len(self.issues),
                "lines_of_code": len(code.split('\n'))
            }
            
        except SyntaxError as e:
            return {
                "quality_score": 0,
                "issues": [{
                    "line": e.lineno or 1,
                    "type": "syntax_error",
                    "severity": "error", 
                    "message": f"Syntax error: {e.msg}",
                    "suggestion": "Fix the syntax error before analysis can continue"
                }],
                "total_issues": 1,
                "lines_of_code": len(code.split('\n'))
            }
    
    def _check_function_length(self, tree: ast.AST, code: str):
        """Check for overly long functions"""
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate function length
                end_line = node.end_lineno or node.lineno
                func_length = end_line - node.lineno + 1
                
                if func_length > 50:
                    self.issues.append(CodeIssue(
                        line_number=node.lineno,
                        issue_type="function_length",
                        severity="warning",
                        message=f"Function '{node.name}' is {func_length} lines long",
                        suggestion="Consider breaking this function into smaller functions"
                    ))
                elif func_length > 20:
                    self.issues.append(CodeIssue(
                        line_number=node.lineno,
                        issue_type="function_length",
                        severity="info",
                        message=f"Function '{node.name}' is {func_length} lines long",
                        suggestion="Consider if this function could be simplified"
                    ))
    
    def _check_missing_docstrings(self, tree: ast.AST):
        """Check for missing docstrings in functions and classes"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # Check if first statement is a docstring
                has_docstring = (
                    node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                )
                
                if not has_docstring:
                    node_type = "function" if isinstance(node, ast.FunctionDef) else "class"
                    self.issues.append(CodeIssue(
                        line_number=node.lineno,
                        issue_type="missing_docstring",
                        severity="info",
                        message=f"{node_type.title()} '{node.name}' is missing a docstring",
                        suggestion=f"Add a docstring to document what this {node_type} does"
                    ))
    
    def _check_unused_imports(self, tree: ast.AST, code: str):
        """Check for potentially unused imports (simple heuristic)"""
        imports = []
        
        # Collect all imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append(alias.name)
        
        # Simple check: if import name doesn't appear elsewhere in code
        for import_name in imports:
            # Count occurrences (excluding import statements)
            import_pattern = rf'\b{re.escape(import_name)}\b'
            matches = re.findall(import_pattern, code)
            
            # If only appears once (in the import), might be unused
            if len(matches) <= 1:
                # Find line number of import
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        names = [alias.name for alias in node.names]
                        if import_name in names:
                            self.issues.append(CodeIssue(
                                line_number=node.lineno,
                                issue_type="unused_import",
                                severity="info",
                                message=f"Import '{import_name}' appears to be unused",
                                suggestion="Remove unused imports to keep code clean"
                            ))
                            break
    
    def _check_complex_conditions(self, tree: ast.AST):
        """Check for overly complex conditional statements"""
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Count boolean operators in condition
                bool_ops = len([n for n in ast.walk(node.test) if isinstance(n, (ast.And, ast.Or))])
                
                if bool_ops > 3:
                    self.issues.append(CodeIssue(
                        line_number=node.lineno,
                        issue_type="complex_condition",
                        severity="warning",
                        message="Complex conditional statement with multiple boolean operators",
                        suggestion="Consider breaking this into multiple conditions or using a helper function"
                    ))
    
    def _check_naming_conventions(self, tree: ast.AST):
        """Check Python naming conventions"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Function names should be snake_case
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name) and not node.name.startswith('__'):
                    self.issues.append(CodeIssue(
                        line_number=node.lineno,
                        issue_type="naming_convention",
                        severity="info",
                        message=f"Function '{node.name}' doesn't follow snake_case convention",
                        suggestion="Use snake_case for function names (e.g., my_function)"
                    ))
            
            elif isinstance(node, ast.ClassDef):
                # Class names should be PascalCase
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    self.issues.append(CodeIssue(
                        line_number=node.lineno,
                        issue_type="naming_convention",
                        severity="info",
                        message=f"Class '{node.name}' doesn't follow PascalCase convention",
                        suggestion="Use PascalCase for class names (e.g., MyClass)"
                    ))
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score from 0-100"""
        if not self.issues:
            return 100.0
        
        # Weighted scoring based on severity
        severity_weights = {
            "error": -20,
            "warning": -10, 
            "info": -5
        }
        
        total_deduction = sum(severity_weights[issue.severity] for issue in self.issues)
        
        # Start with 100 and apply deductions
        score = max(0, 100 + total_deduction)
        
        return round(score, 1)