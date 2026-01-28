"""Parser for extracting flow metadata and inferring connections from code.

This module uses pure AST analysis to discover flows and steps without executing code.
"""

import ast
import warnings
from pathlib import Path

from flowdoc.models import Edge, FlowData, StepData


class FlowCallVisitor(ast.NodeVisitor):
    """AST visitor to find calls to other @step decorated functions/methods.

    Handles three patterns:
    1. Method calls: self.other_method()
    2. Function calls: other_function()
    3. Async calls: await other_function()
    """

    def __init__(self, decorated_steps: set[str]) -> None:
        """Initialize visitor.

        :param decorated_steps: set of function/method names that have @step decorator
        """
        self.decorated_steps = decorated_steps
        self.calls_to_steps: list[Edge] = []
        self.current_branch: str | None = None  # Track if we're in an if/else

    def visit_Call(self, node: ast.Call) -> None:
        """Visit Call nodes to detect step calls.

        :param node: AST Call node to analyze
        """
        target_name: str | None = None

        # Pattern 1: Method call like self.other_method()
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "self":
                target_name = node.func.attr

        # Pattern 2: Direct function call like other_function()
        elif isinstance(node.func, ast.Name):
            target_name = node.func.id

        if target_name and target_name in self.decorated_steps:
            self.calls_to_steps.append(
                Edge(
                    from_step="",
                    to_step=target_name,
                    branch=self.current_branch,
                    line_number=node.lineno,
                )
            )

        self.generic_visit(node)

    def visit_Await(self, node: ast.Await) -> None:
        """Visit Await nodes for async function calls.

        :param node: AST Await node to analyze
        """
        # The actual Call node is inside the Await, so just continue traversal
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Visit If nodes to track branching.

        :param node: AST If node to analyze
        """
        # Visit the if branch
        old_branch = self.current_branch
        self.current_branch = "if"
        for child in node.body:
            self.visit(child)

        # Visit the else branch
        if node.orelse:
            self.current_branch = "else"
            for child in node.orelse:
                self.visit(child)

        self.current_branch = old_branch


class FlowParser:
    """Parses Python files to extract flow metadata using pure AST analysis.

    No code execution - completely safe for untrusted input.
    """

    # Recognized decorator names
    FLOW_DECORATOR_NAMES = {"flow", "business_flow"}
    STEP_DECORATOR_NAMES = {"step", "business_step", "flow_step"}

    def parse_file(self, file_path: Path) -> list[FlowData]:
        """Extract all flows from a Python file using AST analysis.

        :param file_path: Path to Python source file
        :return: List of flow data dictionaries
        """
        # Read source code
        with open(file_path, encoding="utf-8") as f:
            source = f.read()

        # Parse into AST
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise SyntaxError(f"Cannot parse {file_path}: {e}") from e

        flows: list[FlowData] = []

        # First pass: collect all @step decorated functions/methods
        all_steps = self._collect_all_steps(tree)

        # Second pass: extract class-based flows (with @flow decorator)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                flow_data = self._extract_class_flow(node, all_steps, tree)
                if flow_data:
                    flows.append(flow_data)

        # Third pass: extract function-based flow (standalone @step functions)
        function_steps = self._extract_function_steps(tree, all_steps)
        if function_steps:
            # Create an implicit flow from standalone functions
            flow_data = self._create_function_flow(function_steps, all_steps, tree)
            flows.append(flow_data)

        return flows

    def _collect_all_steps(self, tree: ast.Module) -> dict[str, ast.FunctionDef]:
        """Collect all @step decorated functions and methods from AST.

        :param tree: AST Module node
        :return: Dictionary mapping step function names to their AST nodes
        """
        steps: dict[str, ast.FunctionDef] = {}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._has_step_decorator(node):
                    steps[node.name] = node

        return steps

    def _has_step_decorator(self, node: ast.FunctionDef) -> bool:
        """Check if function has @step decorator.

        :param node: Function definition node
        :return: True if decorated with @step
        """
        for decorator in node.decorator_list:
            if self._is_step_decorator(decorator):
                return True
        return False

    def _is_step_decorator(self, decorator: ast.expr) -> bool:
        """Check if decorator is a @step variant.

        Supports:
        - @step(...)
        - @flowdoc.step(...)
        - @business_step(...)

        :param decorator: Decorator AST node
        :return: True if it's a step decorator
        """
        # Pattern 1: @step(name="...")
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id in self.STEP_DECORATOR_NAMES
            # Pattern 2: @flowdoc.step(name="...")
            if isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr in self.STEP_DECORATOR_NAMES

        # Pattern 3: @step (no arguments)
        if isinstance(decorator, ast.Name):
            return decorator.id in self.STEP_DECORATOR_NAMES

        return False

    def _has_flow_decorator(self, node: ast.ClassDef) -> bool:
        """Check if class has @flow decorator.

        :param node: Class definition node
        :return: True if decorated with @flow
        """
        for decorator in node.decorator_list:
            if self._is_flow_decorator(decorator):
                return True
        return False

    def _is_flow_decorator(self, decorator: ast.expr) -> bool:
        """Check if decorator is a @flow variant.

        :param decorator: Decorator AST node
        :return: True if it's a flow decorator
        """
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id in self.FLOW_DECORATOR_NAMES
            if isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr in self.FLOW_DECORATOR_NAMES

        if isinstance(decorator, ast.Name):
            return decorator.id in self.FLOW_DECORATOR_NAMES

        return False

    @staticmethod
    def _extract_decorator_args(decorator: ast.expr) -> dict[str, str]:
        """Extract arguments from decorator call.

        Only supports literal string arguments. Dynamic arguments are skipped with warning.

        :param decorator: Decorator AST node (must be ast.Call)
        :return: Dictionary of argument name -> value
        """
        args: dict[str, str] = {}

        if not isinstance(decorator, ast.Call):
            return args

        for keyword in decorator.keywords:
            if keyword.arg is None:
                continue

            # Only support literal strings
            if isinstance(keyword.value, ast.Constant):
                if isinstance(keyword.value.value, str):
                    args[keyword.arg] = keyword.value.value
            else:
                # Dynamic argument (f-string, variable, etc.)
                warnings.warn(
                    f"Skipping dynamic decorator argument '{keyword.arg}' - "
                    f"only literal strings are supported",
                    UserWarning,
                    stacklevel=2,
                )

        return args

    def _extract_class_flow(
        self,
        class_node: ast.ClassDef,
        all_steps: dict[str, ast.FunctionDef],
        tree: ast.Module,
    ) -> FlowData | None:
        """Extract flow metadata from a @flow decorated class.

        :param class_node: Class definition AST node
        :param all_steps: All available @step functions/methods
        :param tree: Full module AST tree
        :return: Flow data dictionary or None if not a flow class
        """
        # Check if this class has @flow decorator
        if not self._has_flow_decorator(class_node):
            return None

        # Extract flow metadata from decorator
        flow_name = class_node.name  # Default to class name
        flow_description = ""

        for decorator in class_node.decorator_list:
            if self._is_flow_decorator(decorator):
                args = self._extract_decorator_args(decorator)
                flow_name = args.get("name", class_node.name)
                flow_description = args.get("description", "")
                break

        steps: list[StepData] = []
        edges: list[Edge] = []

        # Find all @step decorated methods in this class
        decorated_methods: dict[str, ast.FunctionDef] = {}
        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._has_step_decorator(node):
                    decorated_methods[node.name] = node

        # Get all callable step names (for call detection)
        callable_steps = set(all_steps.keys())

        # Parse each method to find calls to other steps
        for method_name, method_node in decorated_methods.items():
            step_data = self._extract_step_metadata(method_node)

            # Find calls to other @step decorated functions/methods
            connections = self._find_step_calls(method_node, callable_steps)
            step_data.calls = connections

            # Create edges from this step to called steps
            for call in connections:
                edges.append(Edge(from_step=method_name, to_step=call.to_step, branch=call.branch))

            steps.append(step_data)

        return FlowData(
            name=flow_name, type="class", steps=steps, edges=edges, description=flow_description
        )

    @staticmethod
    def _extract_function_steps(
        tree: ast.Module, all_steps: dict[str, ast.FunctionDef]
    ) -> list[ast.FunctionDef]:
        """Extract standalone @step decorated functions (not in classes).

        :param tree: Module AST node
        :param all_steps: All available @step functions/methods
        :return: list of standalone function AST nodes
        """
        function_steps: list[ast.FunctionDef] = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in all_steps:
                    function_steps.append(node)

        return function_steps

    def _create_function_flow(
        self,
        function_steps: list[ast.FunctionDef],
        all_steps: dict[str, ast.FunctionDef],
        tree: ast.Module,
    ) -> FlowData:
        """Create a flow from standalone @step functions.

        :param function_steps: List of function AST nodes
        :param all_steps: All available @step functions/methods
        :param tree: Full module AST tree
        :return: FlowData object
        """
        steps: list[StepData] = []
        edges: list[Edge] = []

        callable_steps = set(all_steps.keys())

        # Parse each function to find calls to other steps
        for func_node in function_steps:
            step_data = self._extract_step_metadata(func_node)

            # Find calls to other @step decorated functions
            connections = self._find_step_calls(func_node, callable_steps)
            step_data.calls = connections

            # Create edges from this step to called steps
            for call in connections:
                edges.append(
                    Edge(from_step=func_node.name, to_step=call.to_step, branch=call.branch)
                )

            steps.append(step_data)

        # Create implicit flow name
        flow_name = "Function Flow"

        return FlowData(
            name=flow_name,
            type="function",
            steps=steps,
            edges=edges,
            description="Flow derived from standalone function",
        )

    def _extract_step_metadata(self, func_node: ast.FunctionDef) -> StepData:
        """Extract step metadata from decorated function AST node.

        :param func_node: Function definition AST node
        :return: StepData object
        """
        step_name = func_node.name  # Default to function name
        step_description = ""

        # Find @step decorator and extract arguments
        for decorator in func_node.decorator_list:
            if self._is_step_decorator(decorator):
                args = self._extract_decorator_args(decorator)
                step_name = args.get("name", func_node.name)
                step_description = args.get("description", "")
                break

        return StepData(
            name=step_name,
            function_name=func_node.name,
            description=step_description,
        )

    @staticmethod
    def _find_step_calls(function_node: ast.FunctionDef, decorated_steps: set[str]) -> list[Edge]:
        """Find all calls to @step decorated functions/methods within a function.

        :param function_node: Function definition AST node
        :param decorated_steps: Set of names of decorated steps
        :return: List of call dictionaries
        """
        visitor = FlowCallVisitor(decorated_steps)
        visitor.visit(function_node)
        return visitor.calls_to_steps
