"""
CodeSandbox - Safe code execution environment for RPA.

Provides isolated execution of code snippets with:
- Timeout protection
- Resource limits
- Output capture
- Error handling
- Safety restrictions
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import ast
import sys
import traceback
import threading
import signal
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a code execution."""
    success: bool
    output: str
    error: Optional[str] = None
    error_type: Optional[str] = None
    return_value: Any = None
    execution_time_ms: float = 0.0
    timed_out: bool = False
    memory_used_kb: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "error_type": self.error_type,
            "return_value": str(self.return_value) if self.return_value is not None else None,
            "execution_time_ms": self.execution_time_ms,
            "timed_out": self.timed_out,
            "memory_used_kb": self.memory_used_kb,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SafetyViolation:
    """Represents a safety violation in code."""
    violation_type: str
    description: str
    line_number: Optional[int] = None
    severity: str = "high"  # high, medium, low
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "violation_type": self.violation_type,
            "description": self.description,
            "line_number": self.line_number,
            "severity": self.severity,
            "suggestion": self.suggestion,
        }


class CodeAnalyzer:
    """
    Static code analyzer for safety checks.
    
    Analyzes code before execution to detect potential safety issues.
    """

    # Dangerous imports that should be blocked
    BLOCKED_IMPORTS = {
        "os", "subprocess", "sys", "builtins", "importlib",
        "socket", "requests", "urllib", "http", "ftplib",
        "telnetlib", "smtplib", "poplib", "imaplib",
        "pickle", "shelve", "marshal", "shutil",
        "tempfile", "multiprocessing", "threading",
        "signal", "ctypes", "code", "codeop",
        "commands", "popen2", "pty", "fcntl",
    }

    # Dangerous function calls
    BLOCKED_CALLS = {
        "eval", "exec", "compile", "open", "input",
        "breakpoint", "exit", "quit", "help",
        "__import__", "globals", "locals", "vars",
    }

    # Allowed built-in functions
    ALLOWED_BUILTINS = {
        "abs", "all", "any", "ascii", "bin", "bool", "bytearray",
        "bytes", "callable", "chr", "classmethod", "complex",
        "dict", "dir", "divmod", "enumerate", "filter", "float",
        "format", "frozenset", "getattr", "hasattr", "hash",
        "hex", "id", "int", "isinstance", "issubclass", "iter",
        "len", "list", "map", "max", "min", "next", "object",
        "oct", "ord", "pow", "print", "property", "range",
        "repr", "reversed", "round", "set", "setattr", "slice",
        "sorted", "staticmethod", "str", "sum", "super", "tuple",
        "type", "zip", "True", "False", "None",
    }

    def analyze(self, code: str) -> List[SafetyViolation]:
        """
        Analyze code for safety violations.

        Args:
            code: The code to analyze

        Returns:
            List of safety violations found
        """
        violations = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            violations.append(SafetyViolation(
                violation_type="syntax_error",
                description=f"Syntax error: {e.msg}",
                line_number=e.lineno,
                severity="high",
                suggestion="Fix syntax errors before execution"
            ))
            return violations

        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module in self.BLOCKED_IMPORTS:
                        violations.append(SafetyViolation(
                            violation_type="blocked_import",
                            description=f"Import of '{module}' is not allowed",
                            line_number=node.lineno,
                            severity="high",
                            suggestion=f"Remove the import of '{module}'"
                        ))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    if module in self.BLOCKED_IMPORTS:
                        violations.append(SafetyViolation(
                            violation_type="blocked_import",
                            description=f"Import from '{module}' is not allowed",
                            line_number=node.lineno,
                            severity="high",
                            suggestion=f"Remove the import from '{module}'"
                        ))

            # Check function calls
            elif isinstance(node, ast.Call):
                func_name = self._get_func_name(node)
                if func_name in self.BLOCKED_CALLS:
                    violations.append(SafetyViolation(
                        violation_type="blocked_call",
                        description=f"Call to '{func_name}' is not allowed",
                        line_number=node.lineno,
                        severity="high",
                        suggestion=f"Use alternative to '{func_name}'"
                    ))

            # Check for attribute access that could be dangerous
            elif isinstance(node, ast.Attribute):
                if node.attr.startswith('_') and not node.attr.endswith('_'):
                    violations.append(SafetyViolation(
                        violation_type="private_access",
                        description=f"Access to private attribute '{node.attr}'",
                        line_number=node.lineno,
                        severity="medium",
                        suggestion="Avoid accessing private attributes"
                    ))

            # Check for exec/eval in unusual ways
            elif isinstance(node, ast.Name):
                if node.id in ("exec", "eval", "compile"):
                    violations.append(SafetyViolation(
                        violation_type="dangerous_reference",
                        description=f"Reference to dangerous function '{node.id}'",
                        line_number=node.lineno,
                        severity="high",
                        suggestion=f"Remove reference to '{node.id}'"
                    ))

        return violations

    def _get_func_name(self, node: ast.Call) -> str:
        """Get the function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def is_safe(self, code: str) -> Tuple[bool, List[SafetyViolation]]:
        """
        Check if code is safe to execute.

        Args:
            code: The code to check

        Returns:
            Tuple of (is_safe, violations)
        """
        violations = self.analyze(code)
        high_severity = [v for v in violations if v.severity == "high"]
        return len(high_severity) == 0, violations


class RestrictedGlobals:
    """Restricted globals for safe execution."""

    def __init__(self, allowed_builtins: Optional[set] = None):
        """
        Initialize restricted globals.

        Args:
            allowed_builtins: Set of allowed builtin names
        """
        self._allowed = allowed_builtins or CodeAnalyzer.ALLOWED_BUILTINS
        self._builtins = {}
        
        # Build safe builtins dict
        import builtins
        for name in self._allowed:
            if hasattr(builtins, name):
                self._builtins[name] = getattr(builtins, name)

    def get_globals(self) -> Dict[str, Any]:
        """Get the restricted globals dictionary."""
        return {"__builtins__": self._builtins}


class CodeSandbox:
    """
    Sandboxed code execution environment.

    Provides safe execution of code with:
    - Timeout protection
    - Memory limits
    - Output capture
    - Restricted builtins
    - Safety analysis
    """

    def __init__(
        self,
        timeout_seconds: float = 5.0,
        max_output_size: int = 10000,
        enable_safety_check: bool = True,
        allowed_builtins: Optional[set] = None,
    ):
        """
        Initialize the CodeSandbox.

        Args:
            timeout_seconds: Maximum execution time
            max_output_size: Maximum output size in characters
            enable_safety_check: Whether to perform safety analysis
            allowed_builtins: Set of allowed builtin names
        """
        self.timeout = timeout_seconds
        self.max_output_size = max_output_size
        self.enable_safety_check = enable_safety_check
        self.analyzer = CodeAnalyzer()
        self.restricted_globals = RestrictedGlobals(allowed_builtins)
        
        # Execution history
        self._history: List[ExecutionResult] = []
        self._max_history = 100

    def execute(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_override: Optional[float] = None,
    ) -> ExecutionResult:
        """
        Execute code in the sandbox.

        Args:
            code: The code to execute
            context: Optional context variables to inject
            timeout_override: Override the default timeout

        Returns:
            ExecutionResult with execution details
        """
        start_time = datetime.now()
        timeout = timeout_override or self.timeout

        # Safety check
        if self.enable_safety_check:
            is_safe, violations = self.analyzer.is_safe(code)
            if not is_safe:
                violation_strs = [v.description for v in violations if v.severity == "high"]
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Safety violations detected: {'; '.join(violation_strs)}",
                    error_type="SafetyViolation",
                    metadata={"violations": [v.to_dict() for v in violations]}
                )

        # Prepare execution environment
        exec_globals = self.restricted_globals.get_globals()
        if context:
            exec_globals.update(context)

        exec_locals = {}

        # Capture output
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        # Result tracking
        result = ExecutionResult(success=False, output="")
        timed_out = False

        def execute_code():
            nonlocal result, timed_out
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # Execute the code
                    exec(code, exec_globals, exec_locals)
                    
                # Check for return value
                if "result" in exec_locals:
                    result.return_value = exec_locals["result"]
                elif "return_value" in exec_locals:
                    result.return_value = exec_locals["return_value"]

                result.success = True
                result.output = stdout_capture.getvalue()
                
                # Truncate output if too long
                if len(result.output) > self.max_output_size:
                    result.output = result.output[:self.max_output_size] + "\n... (truncated)"
                    result.metadata["output_truncated"] = True

            except Exception as e:
                result.error = str(e)
                result.error_type = type(e).__name__
                result.output = stdout_capture.getvalue()
                result.metadata["traceback"] = traceback.format_exc()

        # Run with timeout
        thread = threading.Thread(target=execute_code)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            # Thread is still running - timeout
            timed_out = True
            result.timed_out = True
            result.error = f"Execution timed out after {timeout} seconds"
            result.error_type = "TimeoutError"

        # Calculate execution time
        end_time = datetime.now()
        result.execution_time_ms = (end_time - start_time).total_seconds() * 1000

        # Store in history
        self._history.append(result)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        return result

    def execute_function(
        self,
        code: str,
        function_name: str,
        *args,
        **kwargs
    ) -> ExecutionResult:
        """
        Execute a specific function from code.

        Args:
            code: Code containing the function
            function_name: Name of the function to call
            *args: Arguments to pass
            **kwargs: Keyword arguments to pass

        Returns:
            ExecutionResult with execution details
        """
        # Wrap code in function call
        wrapper_code = f"""
{code}
result = {function_name}(*{args!r}, **{kwargs!r})
"""
        return self.execute(wrapper_code)

    def test_pattern(
        self,
        pattern_code: str,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Test a pattern against multiple test cases.

        Args:
            pattern_code: Code implementing the pattern
            test_cases: List of test cases with 'input' and 'expected'

        Returns:
            Test results summary
        """
        results = {
            "total": len(test_cases),
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": []
        }

        for i, test_case in enumerate(test_cases):
            test_input = test_case.get("input", {})
            expected = test_case.get("expected")
            description = test_case.get("description", f"Test case {i+1}")

            # Create test wrapper
            if isinstance(test_input, dict):
                input_str = ", ".join(f"{k}={v!r}" for k, v in test_input.items())
            else:
                input_str = repr(test_input)

            test_code = f"""
{pattern_code}
_test_result = pattern({input_str})
result = _test_result
"""

            exec_result = self.execute(test_code)

            detail = {
                "test_case": i + 1,
                "description": description,
                "success": exec_result.success,
                "expected": expected,
                "actual": exec_result.return_value,
                "error": exec_result.error,
            }

            if exec_result.success:
                actual = exec_result.return_value
                if actual == expected:
                    results["passed"] += 1
                    detail["passed"] = True
                else:
                    results["failed"] += 1
                    detail["passed"] = False
                    results["errors"].append(f"Test {i+1}: Expected {expected}, got {actual}")
            else:
                results["failed"] += 1
                detail["passed"] = False
                results["errors"].append(f"Test {i+1}: {exec_result.error}")

            results["details"].append(detail)

        return results

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history."""
        recent = self._history[-limit:] if limit else self._history
        return [r.to_dict() for r in recent]

    def clear_history(self) -> None:
        """Clear execution history."""
        self._history.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get sandbox statistics."""
        if not self._history:
            return {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "timed_out": 0,
                "avg_execution_time_ms": 0,
            }

        successful = sum(1 for r in self._history if r.success)
        timed_out = sum(1 for r in self._history if r.timed_out)
        avg_time = sum(r.execution_time_ms for r in self._history) / len(self._history)

        return {
            "total_executions": len(self._history),
            "successful": successful,
            "failed": len(self._history) - successful,
            "timed_out": timed_out,
            "avg_execution_time_ms": avg_time,
        }


class ExecutionLogger:
    """
    Logger for tracking code execution history.

    Provides detailed logging and analysis of code executions.
    """

    def __init__(self, max_entries: int = 1000):
        """
        Initialize the execution logger.

        Args:
            max_entries: Maximum number of entries to keep
        """
        self.max_entries = max_entries
        self._entries: List[Dict[str, Any]] = []

    def log_execution(
        self,
        code: str,
        result: ExecutionResult,
        session_id: Optional[str] = None,
        pattern_id: Optional[str] = None,
    ) -> str:
        """
        Log an execution.

        Args:
            code: The code that was executed
            result: The execution result
            session_id: Optional session ID
            pattern_id: Optional pattern ID

        Returns:
            Log entry ID
        """
        import uuid
        entry_id = str(uuid.uuid4())[:8]

        entry = {
            "entry_id": entry_id,
            "code": code[:500] + "..." if len(code) > 500 else code,
            "result": result.to_dict(),
            "session_id": session_id,
            "pattern_id": pattern_id,
            "timestamp": datetime.now().isoformat(),
        }

        self._entries.append(entry)

        # Enforce limit
        if len(self._entries) > self.max_entries:
            self._entries.pop(0)

        return entry_id

    def get_entries(
        self,
        session_id: Optional[str] = None,
        pattern_id: Optional[str] = None,
        success_only: bool = False,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get log entries.

        Args:
            session_id: Filter by session ID
            pattern_id: Filter by pattern ID
            success_only: Only return successful executions
            limit: Maximum number of entries

        Returns:
            List of matching entries
        """
        entries = self._entries

        if session_id:
            entries = [e for e in entries if e.get("session_id") == session_id]
        if pattern_id:
            entries = [e for e in entries if e.get("pattern_id") == pattern_id]
        if success_only:
            entries = [e for e in entries if e["result"]["success"]]

        return entries[-limit:]

    def get_error_patterns(self) -> List[Dict[str, Any]]:
        """
        Analyze error patterns in execution history.

        Returns:
            List of error pattern summaries
        """
        error_entries = [e for e in self._entries if not e["result"]["success"]]
        
        # Group by error type
        error_types: Dict[str, List[Dict]] = {}
        for entry in error_entries:
            error_type = entry["result"].get("error_type", "Unknown")
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(entry)

        patterns = []
        for error_type, entries in error_types.items():
            patterns.append({
                "error_type": error_type,
                "count": len(entries),
                "recent_examples": entries[-3:],
            })

        return sorted(patterns, key=lambda x: -x["count"])

    def clear(self) -> None:
        """Clear all log entries."""
        self._entries.clear()
