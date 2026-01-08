#!/usr/bin/env python3
"""
Code Quality Scanner for AI Interviewer Project
Scans for unused imports, functions, and potential bugs
"""

import os
import ast
import sys
from pathlib import Path
from collections import defaultdict

class CodeScanner:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.issues = defaultdict(list)
        
    def scan_file(self, filepath):
        """Scan a single Python file for issues"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(filepath))
                
            # Check for unused imports
            self.check_unused_imports(filepath, tree, content)
            
            # Check for potential bugs
            self.check_potential_bugs(filepath, tree)
            
            # Check for code smells
            self.check_code_smells(filepath, tree)
            
        except SyntaxError as e:
            self.issues[filepath].append(f"Syntax Error: {e}")
        except Exception as e:
            self.issues[filepath].append(f"Error scanning: {e}")
    
    def check_unused_imports(self, filepath, tree, content):
        """Check for potentially unused imports"""
        imports = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = f"{node.module}.{alias.name}"
        
        # Check if imports are used
        for name, full_name in imports.items():
            # Simple check - not perfect but catches obvious cases
            if content.count(name) == 1:  # Only appears in import line
                self.issues[filepath].append(f"Potentially unused import: {full_name}")
    
    def check_potential_bugs(self, filepath, tree):
        """Check for potential bugs"""
        for node in ast.walk(tree):
            # Check for bare except
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.issues[filepath].append(
                        f"Line {node.lineno}: Bare except clause (catches all exceptions)"
                    )
            
            # Check for mutable default arguments
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        self.issues[filepath].append(
                            f"Line {node.lineno}: Mutable default argument in {node.name}()"
                        )
    
    def check_code_smells(self, filepath, tree):
        """Check for code smells"""
        for node in ast.walk(tree):
            # Check for very long functions
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno
                    if length > 100:
                        self.issues[filepath].append(
                            f"Line {node.lineno}: Very long function {node.name}() ({length} lines)"
                        )
            
            # Check for too many arguments
            if isinstance(node, ast.FunctionDef):
                arg_count = len(node.args.args)
                if arg_count > 7:
                    self.issues[filepath].append(
                        f"Line {node.lineno}: Too many arguments in {node.name}() ({arg_count})"
                    )
    
    def scan_directory(self, directory):
        """Scan all Python files in directory"""
        for filepath in Path(directory).rglob("*.py"):
            # Skip virtual environments and cache
            if any(part in filepath.parts for part in ['venv', '__pycache__', 'node_modules', '.git']):
                continue
            
            self.scan_file(filepath)
    
    def generate_report(self):
        """Generate a report of all issues found"""
        report = []
        report.append("=" * 80)
        report.append("CODE QUALITY SCAN REPORT")
        report.append("=" * 80)
        report.append("")
        
        if not self.issues:
            report.append("✅ No issues found!")
            return "\n".join(report)
        
        total_issues = sum(len(issues) for issues in self.issues.values())
        report.append(f"Found {total_issues} potential issues in {len(self.issues)} files")
        report.append("")
        
        for filepath, issues in sorted(self.issues.items()):
            report.append(f"\n📄 {filepath}")
            report.append("-" * 80)
            for issue in issues:
                report.append(f"  ⚠️  {issue}")
        
        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS")
        report.append("=" * 80)
        report.append("1. Review all bare except clauses and handle specific exceptions")
        report.append("2. Remove or comment unused imports")
        report.append("3. Refactor long functions into smaller, focused functions")
        report.append("4. Avoid mutable default arguments")
        report.append("5. Consider reducing function parameters using dataclasses or config objects")
        
        return "\n".join(report)

def main():
    # Scan backend directory
    backend_dir = Path(__file__).parent / "backend"
    
    if not backend_dir.exists():
        print(f"Error: Backend directory not found at {backend_dir}")
        return
    
    print("Scanning Python files for code quality issues...")
    print(f"Scanning directory: {backend_dir}")
    print()
    
    scanner = CodeScanner(backend_dir)
    scanner.scan_directory(backend_dir)
    
    report = scanner.generate_report()
    print(report)
    
    # Save report to file
    report_file = Path(__file__).parent / "CODE_QUALITY_REPORT.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n\n📝 Report saved to: {report_file}")

if __name__ == "__main__":
    main()
