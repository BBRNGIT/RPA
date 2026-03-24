"""
CodingAgent - Specialized agent for code generation and analysis.

Extends BaseAgent with:
- Code generation and refactoring
- Code review and debugging
- Code execution via sandbox
- Language-specific pattern recognition
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
import logging
import re

from rpa.agents.base_agent import BaseAgent, Inquiry
from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory, EventType
from rpa.core.graph import Node, NodeType
from rpa.execution.code_sandbox import CodeSandbox, ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class CodeReview:
    """Result of a code review."""
    review_id: str
    code: str
    language: str
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    score: float  # 0.0 to 1.0
    reviewed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "review_id": self.review_id,
            "code": self.code,
            "language": self.language,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "score": self.score,
            "reviewed_at": self.reviewed_at.isoformat(),
        }


@dataclass
class CodePattern:
    """Represents a recognized code pattern."""
    pattern_id: str
    pattern_type: str  # assignment, loop, function, class, etc.
    language: str
    template: str
    variables: List[str]
    examples: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "language": self.language,
            "template": self.template,
            "variables": self.variables,
            "examples": self.examples,
            "metadata": self.metadata,
        }


class CodingAgent(BaseAgent):
    """
    Specialized agent for code generation and analysis.

    Extends BaseAgent with code-specific capabilities:
    - Code generation from descriptions
    - Code refactoring suggestions
    - Code review and analysis
    - Debugging assistance
    - Code execution via sandbox
    """

    SUPPORTED_LANGUAGES = ["python", "javascript", "sql"]
    CODE_PATTERNS = {
        "python": {
            "assignment": r"(\w+)\s*=\s*(.+)",
            "function": r"def\s+(\w+)\s*\((.*?)\)\s*:",
            "class": r"class\s+(\w+).*?:",
            "for_loop": r"for\s+(\w+)\s+in\s+(.+):",
            "while_loop": r"while\s+(.+):",
            "if_statement": r"if\s+(.+):",
            "import": r"import\s+(\w+)",
            "return": r"return\s+(.+)",
        },
        "javascript": {
            "assignment": r"(?:let|const|var)\s+(\w+)\s*=\s*(.+)",
            "function": r"function\s+(\w+)\s*\((.*?)\)",
            "arrow_function": r"(\w+)\s*=\s*\((.*?)\)\s*=>",
            "class": r"class\s+(\w+)",
            "for_loop": r"for\s*\((.+)\)",
            "if_statement": r"if\s*\((.+)\)",
        },
        "sql": {
            "select": r"SELECT\s+(.+?)\s+FROM",
            "insert": r"INSERT\s+INTO\s+(\w+)",
            "update": r"UPDATE\s+(\w+)\s+SET",
            "delete": r"DELETE\s+FROM\s+(\w+)",
        },
    }

    def __init__(
        self,
        language: str = "python",
        agent_id: Optional[str] = None,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
        sandbox: Optional[CodeSandbox] = None,
    ):
        """
        Initialize a CodingAgent.

        Args:
            language: Primary programming language
            agent_id: Optional agent ID
            ltm: Optional LongTermMemory instance
            episodic: Optional EpisodicMemory instance
            sandbox: Optional CodeSandbox instance
        """
        super().__init__(
            domain=f"coding_{language}",
            agent_id=agent_id,
            ltm=ltm,
            episodic=episodic,
        )
        self.language = language
        self.sandbox = sandbox or CodeSandbox()
        self._code_patterns: Dict[str, CodePattern] = {}
        self._reviews: Dict[str, CodeReview] = {}

        # Initialize common patterns
        self._initialize_patterns()

    def _initialize_patterns(self) -> None:
        """Initialize common code patterns."""
        common_patterns = [
            ("assign_var", "assignment", "{var} = {value}", ["var", "value"]),
            ("for_range", "for_loop", "for {var} in range({n}):", ["var", "n"]),
            ("if_condition", "if_statement", "if {condition}:", ["condition"]),
            ("def_func", "function", "def {name}({params}):\n    {body}", ["name", "params", "body"]),
        ]
        for pid, ptype, template, vars in common_patterns:
            self._code_patterns[pid] = CodePattern(
                pattern_id=pid,
                pattern_type=ptype,
                language=self.language,
                template=template,
                variables=vars,
                examples=[],
            )

    def generate_code(
        self,
        task: str,
        language: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate code for a given task.

        Args:
            task: Description of the coding task
            language: Target language (defaults to agent's language)
            context: Optional context for code generation

        Returns:
            Generated code and metadata
        """
        lang = language or self.language
        self._update_activity()

        # Simple pattern-based code generation
        # In production, this would use an LLM or more sophisticated approach
        generated_code = ""
        pattern_used = None

        task_lower = task.lower()

        if "for" in task_lower and "loop" in task_lower:
            pattern_used = self._code_patterns.get("for_range")
            if pattern_used:
                # Extract number from task
                import re
                nums = re.findall(r'\d+', task)
                n = int(nums[0]) if nums else 10
                generated_code = pattern_used.template.format(var="i", n=n)
        elif "if" in task_lower:
            pattern_used = self._code_patterns.get("if_condition")
            if pattern_used:
                generated_code = pattern_used.template.format(condition="True")
        elif "assign" in task_lower or "variable" in task_lower:
            pattern_used = self._code_patterns.get("assign_var")
            if pattern_used:
                generated_code = pattern_used.template.format(var="x", value="0")
        elif "function" in task_lower or "def" in task_lower:
            pattern_used = self._code_patterns.get("def_func")
            if pattern_used:
                generated_code = pattern_used.template.format(
                    name="my_function",
                    params="",
                    body="pass"
                )
        else:
            generated_code = f"# Task: {task}\n# TODO: Implement this in {lang}"

        self.episodic.log_event(
            event_type=EventType.PATTERN_LEARNED,
            session_id=self.agent_id,
            data={
                "action": "generate_code",
                "task": task,
                "language": lang,
                "pattern_used": pattern_used.pattern_id if pattern_used else None,
            },
        )

        return {
            "success": True,
            "code": generated_code,
            "language": lang,
            "pattern_used": pattern_used.pattern_id if pattern_used else None,
            "message": f"Generated code for task: {task}",
        }

    def refactor_code(
        self,
        code: str,
        language: Optional[str] = None,
        style: str = "pep8",
    ) -> Dict[str, Any]:
        """
        Suggest refactoring improvements for code.

        Args:
            code: The code to refactor
            language: Target language
            style: Coding style to follow

        Returns:
            Refactored code and suggestions
        """
        lang = language or self.language
        self._update_activity()

        suggestions = []
        refactored_code = code

        # Basic refactoring suggestions
        if lang == "python":
            # Check for long lines
            lines = code.split("\n")
            for i, line in enumerate(lines):
                if len(line) > 79:
                    suggestions.append(f"Line {i+1}: Consider breaking long line")

            # Check for missing docstrings
            if "def " in code and '"""' not in code and "'''" not in code:
                suggestions.append("Consider adding docstrings to functions")

            # Check for tabs vs spaces
            if "\t" in code:
                refactored_code = refactored_code.replace("\t", "    ")
                suggestions.append("Converted tabs to 4 spaces")

        return {
            "success": True,
            "original_code": code,
            "refactored_code": refactored_code,
            "suggestions": suggestions,
            "language": lang,
            "message": f"Refactoring complete with {len(suggestions)} suggestions",
        }

    def review_code(
        self,
        code: str,
        language: Optional[str] = None,
    ) -> CodeReview:
        """
        Review code for issues and improvements.

        Args:
            code: The code to review
            language: Target language

        Returns:
            CodeReview object with findings
        """
        lang = language or self.language
        self._update_activity()

        issues = []
        suggestions = []
        score = 1.0

        # Analyze code for issues
        patterns = self.CODE_PATTERNS.get(lang, {})

        # Check for syntax patterns
        for pattern_name, pattern_regex in patterns.items():
            matches = re.findall(pattern_regex, code, re.IGNORECASE)
            if matches:
                # Pattern found - could add specific checks here
                pass

        # Basic code quality checks
        lines = code.split("\n")

        # Check for empty lines at end
        if lines and not lines[-1].strip():
            issues.append({
                "type": "style",
                "message": "Remove empty line at end of file",
                "line": len(lines),
                "severity": "low",
            })
            score -= 0.05

        # Check for very long functions (heuristic)
        function_lines = []
        in_function = False
        function_start = 0
        for i, line in enumerate(lines):
            if lang == "python" and line.strip().startswith("def "):
                if in_function and i - function_start > 50:
                    issues.append({
                        "type": "complexity",
                        "message": f"Function starting at line {function_start+1} is very long",
                        "line": function_start + 1,
                        "severity": "medium",
                    })
                    score -= 0.1
                in_function = True
                function_start = i

        # Check for TODO/FIXME comments
        for i, line in enumerate(lines):
            if "TODO" in line or "FIXME" in line:
                suggestions.append(f"Line {i+1}: Resolve {line.strip()}")

        # Add general suggestions
        if len(lines) > 100:
            suggestions.append("Consider breaking this file into smaller modules")

        score = max(0.0, min(1.0, score))

        review = CodeReview(
            review_id=f"review_{uuid.uuid4().hex[:8]}",
            code=code,
            language=lang,
            issues=issues,
            suggestions=suggestions,
            score=score,
        )

        self._reviews[review.review_id] = review

        self.episodic.log_event(
            event_type=EventType.ASSESSMENT_COMPLETED,
            session_id=self.agent_id,
            data={
                "action": "code_review",
                "review_id": review.review_id,
                "score": score,
                "issues_count": len(issues),
            },
        )

        return review

    def debug_code(
        self,
        code: str,
        error: str,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Help debug code with a given error.

        Args:
            code: The problematic code
            error: Error message or description
            language: Target language

        Returns:
            Debug analysis and suggestions
        """
        lang = language or self.language
        self._update_activity()

        suggestions = []
        fix_suggestion = None

        # Analyze error patterns
        error_lower = error.lower()

        if "syntaxerror" in error_lower:
            suggestions.append("Check for missing parentheses, brackets, or colons")
            suggestions.append("Ensure proper indentation")
            if lang == "python":
                suggestions.append("Verify no mix of tabs and spaces")

        elif "nameerror" in error_lower:
            # Try to extract variable name
            import re
            match = re.search(r"name '(\w+)'", error)
            if match:
                var_name = match.group(1)
                suggestions.append(f"Variable '{var_name}' is not defined")
                suggestions.append(f"Check if '{var_name}' is spelled correctly")
                suggestions.append(f"Ensure '{var_name}' is defined before use")
                fix_suggestion = f"Add: {var_name} = ...  # define the variable"

        elif "typeerror" in error_lower:
            suggestions.append("Check types of operands in operations")
            suggestions.append("Verify function arguments match expected types")

        elif "indexerror" in error_lower:
            suggestions.append("Check array/list indices are within bounds")
            suggestions.append("Verify list is not empty before accessing")

        elif "keyerror" in error_lower:
            suggestions.append("Check dictionary key exists")
            suggestions.append("Consider using .get() method with default value")

        elif "zerodivisionerror" in error_lower:
            suggestions.append("Check divisor is not zero before division")
            fix_suggestion = "Add: if divisor != 0: result = numerator / divisor"

        else:
            suggestions.append("Review the error message for specific details")
            suggestions.append("Check recent changes to the code")

        return {
            "success": True,
            "code": code,
            "error": error,
            "language": lang,
            "suggestions": suggestions,
            "fix_suggestion": fix_suggestion,
            "message": "Debug analysis complete",
        }

    def execute_code(
        self,
        code: str,
        language: Optional[str] = None,
        timeout: float = 5.0,
    ) -> ExecutionResult:
        """
        Execute code in the sandbox.

        Args:
            code: Code to execute
            language: Target language (only Python supported currently)
            timeout: Execution timeout in seconds

        Returns:
            ExecutionResult with output
        """
        lang = language or self.language
        self._update_activity()

        # Only Python execution is supported
        if lang != "python":
            return ExecutionResult(
                success=False,
                output="",
                error=f"Language '{lang}' not supported for execution",
                error_type="UnsupportedLanguageError",
            )

        result = self.sandbox.execute(code, timeout_override=timeout)

        self.episodic.log_event(
            event_type=EventType.CODE_EXECUTED,
            session_id=self.agent_id,
            data={
                "code": code[:200] + "..." if len(code) > 200 else code,
                "success": result.success,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
            },
        )

        return result

    def recognize_pattern(
        self,
        code: str,
        language: Optional[str] = None,
    ) -> List[CodePattern]:
        """
        Recognize code patterns in the given code.

        Args:
            code: Code to analyze
            language: Target language

        Returns:
            List of recognized patterns
        """
        lang = language or self.language
        self._update_activity()

        recognized = []
        patterns = self.CODE_PATTERNS.get(lang, {})

        for pattern_type, pattern_regex in patterns.items():
            matches = re.findall(pattern_regex, code, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    pattern = CodePattern(
                        pattern_id=f"recognized_{uuid.uuid4().hex[:6]}",
                        pattern_type=pattern_type,
                        language=lang,
                        template=pattern_regex,
                        variables=[],
                        examples=[str(match)],
                    )
                    recognized.append(pattern)

        return recognized

    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            **super().get_capabilities(),
            "domain_specific": [
                "generate_code",
                "refactor_code",
                "review_code",
                "debug_code",
                "execute_code",
                "recognize_pattern",
            ],
            "supported_languages": self.SUPPORTED_LANGUAGES,
            "primary_language": self.language,
        }

    def get_review(self, review_id: str) -> Optional[CodeReview]:
        """Get a code review by ID."""
        return self._reviews.get(review_id)

    def get_all_reviews(self) -> List[CodeReview]:
        """Get all code reviews."""
        return list(self._reviews.values())

    def __repr__(self) -> str:
        return f"CodingAgent(id={self.agent_id}, language={self.language})"
