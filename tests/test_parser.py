"""Tests for the FlowParser and AST analysis."""

from pathlib import Path
from textwrap import dedent

from flowdoc.decorators import clear_flow_registry
from flowdoc.models import Edge
from flowdoc.parser import FlowParser


class TestClassBasedFlowParsing:
    """Tests for parsing class-based flows."""

    def setup_method(self) -> None:
        """Clear the flow registry before each test."""
        clear_flow_registry()

    def test_parse_simple_class_flow(self, tmp_path: Path) -> None:
        """Test parsing a simple class-based flow with linear steps."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Simple Flow", description="A simple test flow")
            class SimpleFlow:
                @step(name="Step 1")
                def step1(self):
                    return self.step2()

                @step(name="Step 2")
                def step2(self):
                    return self.step3()

                @step(name="Step 3")
                def step3(self):
                    pass  # Terminal step
        """)

        test_file = tmp_path / "simple_flow.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]
        assert flow.name == "Simple Flow"
        assert flow.description == "A simple test flow"
        assert flow.type == "class"
        assert len(flow.steps) == 3

        # Check edges
        edges = flow.edges
        assert len(edges) == 2

        assert Edge(from_step="step1", to_step="step2", branch=None, line_number=None) in edges
        assert Edge(from_step="step2", to_step="step3", branch=None, line_number=None) in edges

    def test_parse_class_flow_with_branching(self, tmp_path: Path) -> None:
        """Test parsing a class flow with if/else branches."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Branching Flow")
            class BranchingFlow:
                @step(name="Validate")
                def validate(self):
                    if True:
                        return self.process()
                    else:
                        return self.reject()

                @step(name="Process")
                def process(self):
                    pass

                @step(name="Reject")
                def reject(self):
                    pass
        """)

        test_file = tmp_path / "branching_flow.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]

        # Check edges have branch information
        edges = flow.edges
        assert len(edges) == 2

        # Find the edges and check branches
        validate_to_process = [
            e for e in edges if e.from_step == "validate" and e.to_step == "process"
        ]
        validate_to_reject = [
            e for e in edges if e.from_step == "validate" and e.to_step == "reject"
        ]

        assert len(validate_to_process) == 1
        assert validate_to_process[0].branch == "if"

        assert len(validate_to_reject) == 1
        assert validate_to_reject[0].branch == "else"

    def test_parse_class_flow_with_multiple_calls(self, tmp_path: Path) -> None:
        """Test parsing a class flow where a step calls multiple other steps."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Multi Call Flow")
            class MultiCallFlow:
                @step(name="Start")
                def start(self):
                    self.step_a()
                    self.step_b()
                    return self.step_c()

                @step(name="Step A")
                def step_a(self):
                    pass

                @step(name="Step B")
                def step_b(self):
                    pass

                @step(name="Step C")
                def step_c(self):
                    pass
        """)

        test_file = tmp_path / "multi_call_flow.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]

        # Check that start calls all three steps
        edges = flow.edges
        assert len(edges) == 3

        assert Edge(from_step="start", to_step="step_a", branch=None, line_number=None) in edges
        assert Edge(from_step="start", to_step="step_b", branch=None, line_number=None) in edges
        assert Edge(from_step="start", to_step="step_c", branch=None, line_number=None) in edges


class TestFunctionBasedFlowParsing:
    """Tests for parsing function-based flows."""

    def setup_method(self) -> None:
        """Clear the flow registry before each test."""
        clear_flow_registry()

    def test_parse_simple_function_flow(self, tmp_path: Path) -> None:
        """Test parsing standalone functions with @step decorators."""
        source = dedent("""
            from flowdoc import step

            @step(name="Process Order")
            def process_order():
                return validate_order()

            @step(name="Validate Order")
            def validate_order():
                return charge_payment()

            @step(name="Charge Payment")
            def charge_payment():
                pass  # Terminal
        """)

        test_file = tmp_path / "function_flow.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        # Should create one implicit flow from the functions
        assert len(flows) == 1
        flow = flows[0]
        assert flow.type == "function"
        assert len(flow.steps) == 3

        # Check edges
        edges = flow.edges
        assert len(edges) == 2
        assert Edge(from_step="process_order", to_step="validate_order", branch=None) in edges
        assert Edge(from_step="validate_order", to_step="charge_payment", branch=None) in edges

    def test_parse_function_flow_with_branching(self, tmp_path: Path) -> None:
        """Test parsing functions with conditional branches."""
        source = dedent("""
            from flowdoc import step

            @step(name="Validate Payment")
            def validate_payment():
                if True:
                    return process_payment()
                else:
                    return reject_payment()

            @step(name="Process Payment")
            def process_payment():
                pass

            @step(name="Reject Payment")
            def reject_payment():
                pass
        """)

        test_file = tmp_path / "function_branching.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]

        # Check branch edges
        edges = flow.edges
        assert len(edges) == 2

        validate_to_process = [e for e in edges if e.to_step == "process_payment"]
        validate_to_reject = [e for e in edges if e.to_step == "reject_payment"]

        assert len(validate_to_process) == 1
        assert validate_to_process[0].branch == "if"

        assert len(validate_to_reject) == 1
        assert validate_to_reject[0].branch == "else"


class TestAsyncFunctionParsing:
    """Tests for parsing async/await functions."""

    def setup_method(self) -> None:
        """Clear the flow registry before each test."""
        clear_flow_registry()

    def test_parse_async_function_flow(self, tmp_path: Path) -> None:
        """Test parsing async functions with await calls."""
        source = dedent("""
            from flowdoc import step

            @step(name="Create Order")
            async def create_order():
                validated = await validate_order()
                return await save_order()

            @step(name="Validate Order")
            async def validate_order():
                pass

            @step(name="Save Order")
            async def save_order():
                pass
        """)

        test_file = tmp_path / "async_flow.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]

        # Check that async calls are detected
        edges = flow.edges
        assert len(edges) == 2
        assert Edge(from_step="create_order", to_step="validate_order", branch=None) in edges
        assert Edge(from_step="create_order", to_step="save_order", branch=None) in edges

    def test_parse_async_class_methods(self, tmp_path: Path) -> None:
        """Test parsing async methods in a class."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Async Flow")
            class AsyncFlow:
                @step(name="Process")
                async def process(self):
                    return await self.validate()

                @step(name="Validate")
                async def validate(self):
                    pass
        """)

        test_file = tmp_path / "async_class.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]

        edges = flow.edges
        assert len(edges) == 1
        assert Edge(from_step="process", to_step="validate", branch=None) in edges


class TestMixedFlows:
    """Tests for mixed class and function flows."""

    def setup_method(self) -> None:
        """Clear the flow registry before each test."""
        clear_flow_registry()

    def test_parse_file_with_class_and_functions(self, tmp_path: Path) -> None:
        """Test parsing a file with both @flow class and standalone @step functions."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Class Flow")
            class ClassFlow:
                @step(name="Class Step 1")
                def step1(self):
                    pass

            @step(name="Function Step 1")
            def func_step1():
                return func_step2()

            @step(name="Function Step 2")
            def func_step2():
                pass
        """)

        test_file = tmp_path / "mixed_flow.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        # Should have two flows: one from class, one from functions
        assert len(flows) == 2

        # Find each flow
        class_flows = [f for f in flows if f.type == "class"]
        function_flows = [f for f in flows if f.type == "function"]

        assert len(class_flows) == 1
        assert len(function_flows) == 1

        assert class_flows[0].name == "Class Flow"
        assert len(class_flows[0].steps) == 1

        assert len(function_flows[0].steps) == 2


class TestStepMetadataExtraction:
    """Tests for step metadata extraction."""

    def setup_method(self) -> None:
        """Clear the flow registry before each test."""
        clear_flow_registry()

    def test_extract_step_metadata(self, tmp_path: Path) -> None:
        """Test that step metadata (name, description) is correctly extracted."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Test Flow")
            class TestFlow:
                @step(name="Process Data", description="Process incoming data")
                def process(self):
                    pass
        """)

        test_file = tmp_path / "metadata_test.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]

        steps = flow.steps
        assert len(steps) == 1

        step = steps[0]
        assert step.name == "Process Data"
        assert step.description == "Process incoming data"
        assert step.function_name == "process"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def setup_method(self) -> None:
        """Clear the flow registry before each test."""
        clear_flow_registry()

    def test_parse_empty_flow_class(self, tmp_path: Path) -> None:
        """Test parsing a @flow class with no @step methods."""
        source = dedent("""
            from flowdoc import flow

            @flow(name="Empty Flow")
            class EmptyFlow:
                def normal_method(self):
                    pass
        """)

        test_file = tmp_path / "empty_flow.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]
        assert flow.name == "Empty Flow"
        assert len(flow.steps) == 0
        assert len(flow.edges) == 0

    def test_parse_file_with_no_flows(self, tmp_path: Path) -> None:
        """Test parsing a file with no @flow or @step decorators."""
        source = dedent("""
            def normal_function():
                pass

            class NormalClass:
                def method(self):
                    pass
        """)

        test_file = tmp_path / "no_flows.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 0

    def test_step_calls_non_decorated_function(self, tmp_path: Path) -> None:
        """Test that calls to non-decorated functions are ignored."""
        source = dedent("""
            from flowdoc import step

            @step(name="Process")
            def process():
                helper_function()  # Not decorated
                return validate()

            def helper_function():
                pass

            @step(name="Validate")
            def validate():
                pass
        """)

        test_file = tmp_path / "non_decorated_calls.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]

        # Only the call to validate() should be detected
        edges = flow.edges
        assert len(edges) == 1
        assert edges[0].to_step == "validate"

    def test_namespaced_step_decorator(self, tmp_path: Path) -> None:
        """Test @flowdoc.step namespaced decorator syntax."""
        source = dedent("""
            import flowdoc

            @flowdoc.step(name="Process Order")
            def process_order():
                return validate()

            @flowdoc.step(name="Validate")
            def validate():
                pass
        """)

        test_file = tmp_path / "namespaced_step.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]
        assert len(flow.steps) == 2
        step_names = [s.name for s in flow.steps]
        assert "Process Order" in step_names
        assert "Validate" in step_names

    def test_bare_step_decorator(self, tmp_path: Path) -> None:
        """Test @step without parentheses (bare decorator)."""
        source = dedent("""
            from flowdoc import step

            @step
            def process():
                return validate()

            @step
            def validate():
                pass
        """)

        test_file = tmp_path / "bare_step.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]
        # Bare decorators should use function names
        assert len(flow.steps) == 2

    def test_namespaced_flow_decorator(self, tmp_path: Path) -> None:
        """Test @flowdoc.flow namespaced decorator syntax."""
        source = dedent("""
            import flowdoc

            @flowdoc.flow(name="Order Flow")
            class OrderFlow:
                @flowdoc.step(name="Process")
                def process(self):
                    pass
        """)

        test_file = tmp_path / "namespaced_flow.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]
        assert flow.name == "Order Flow"
        assert len(flow.steps) == 1

    def test_bare_flow_decorator(self, tmp_path: Path) -> None:
        """Test @flow without parentheses (bare decorator)."""
        source = dedent("""
            from flowdoc import flow, step

            @flow
            class OrderFlow:
                @step(name="Process")
                def process(self):
                    pass
        """)

        test_file = tmp_path / "bare_flow.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]
        # Bare flow decorator should use class name
        assert flow.name == "OrderFlow"
