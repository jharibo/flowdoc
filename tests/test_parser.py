"""Tests for the FlowParser and AST analysis."""

from pathlib import Path
from textwrap import dedent

from flowdoc.decorators import clear_flow_registry
from flowdoc.models import Edge, StepData
from flowdoc.parser import FlowParser, StepRegistry


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


class TestTryExceptParsing:
    """Tests for parsing try/except/finally branching."""

    def setup_method(self) -> None:
        clear_flow_registry()

    def test_try_except_labels_handler_with_exception_type(self, tmp_path: Path) -> None:
        """Try body and except handler each get labeled branch edges."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Payment Flow")
            class PaymentFlow:
                @step(name="Process")
                def process(self):
                    try:
                        return self.charge()
                    except PaymentError:
                        return self.send_failure()

                @step(name="Charge")
                def charge(self):
                    pass

                @step(name="Send Failure")
                def send_failure(self):
                    pass
        """)

        test_file = tmp_path / "try_flow.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        edges = flows[0].edges

        process_to_charge = [e for e in edges if e.from_step == "process" and e.to_step == "charge"]
        process_to_failure = [
            e for e in edges if e.from_step == "process" and e.to_step == "send_failure"
        ]

        assert len(process_to_charge) == 1
        assert process_to_charge[0].branch == "try"

        assert len(process_to_failure) == 1
        assert process_to_failure[0].branch == "except PaymentError"

    def test_try_except_bare_handler(self, tmp_path: Path) -> None:
        """Bare `except:` clause labels edges as "except"."""
        source = dedent("""
            from flowdoc import step

            @step(name="Process")
            def process():
                try:
                    charge()
                except:
                    log_error()

            @step(name="Charge")
            def charge():
                pass

            @step(name="Log Error")
            def log_error():
                pass
        """)
        test_file = tmp_path / "bare_except.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)
        edges = flows[0].edges

        to_log = [e for e in edges if e.to_step == "log_error"]
        assert len(to_log) == 1
        assert to_log[0].branch == "except"

    def test_try_except_multiple_handlers(self, tmp_path: Path) -> None:
        """Each except handler gets its own typed branch label."""
        source = dedent("""
            from flowdoc import step

            @step(name="Process")
            def process():
                try:
                    charge()
                except PaymentError:
                    send_failure()
                except NetworkError:
                    retry()

            @step(name="Charge")
            def charge():
                pass

            @step(name="Send Failure")
            def send_failure():
                pass

            @step(name="Retry")
            def retry():
                pass
        """)
        test_file = tmp_path / "multi_handler.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)
        edges = flows[0].edges

        to_failure = [e for e in edges if e.to_step == "send_failure"]
        to_retry = [e for e in edges if e.to_step == "retry"]

        assert len(to_failure) == 1
        assert to_failure[0].branch == "except PaymentError"
        assert len(to_retry) == 1
        assert to_retry[0].branch == "except NetworkError"

    def test_try_except_tuple_of_exceptions(self, tmp_path: Path) -> None:
        """Tuple of exception types joins names with ' | '."""
        source = dedent("""
            from flowdoc import step

            @step(name="Process")
            def process():
                try:
                    charge()
                except (PaymentError, NetworkError):
                    handle()

            @step(name="Charge")
            def charge():
                pass

            @step(name="Handle")
            def handle():
                pass
        """)
        test_file = tmp_path / "tuple_except.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)
        edges = flows[0].edges

        to_handle = [e for e in edges if e.to_step == "handle"]
        assert len(to_handle) == 1
        assert to_handle[0].branch == "except PaymentError | NetworkError"

    def test_try_except_with_finally(self, tmp_path: Path) -> None:
        """Finally block calls are labeled as "finally"."""
        source = dedent("""
            from flowdoc import step

            @step(name="Process")
            def process():
                try:
                    charge()
                except PaymentError:
                    send_failure()
                finally:
                    log_attempt()

            @step(name="Charge")
            def charge():
                pass

            @step(name="Send Failure")
            def send_failure():
                pass

            @step(name="Log Attempt")
            def log_attempt():
                pass
        """)
        test_file = tmp_path / "finally.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)
        edges = flows[0].edges

        to_log = [e for e in edges if e.to_step == "log_attempt"]
        assert len(to_log) == 1
        assert to_log[0].branch == "finally"

    def test_try_except_dotted_exception_type(self, tmp_path: Path) -> None:
        """Qualified exception types like mymod.MyError use the attr name."""
        source = dedent("""
            from flowdoc import step
            import errors

            @step(name="Process")
            def process():
                try:
                    charge()
                except errors.PaymentError:
                    send_failure()

            @step(name="Charge")
            def charge():
                pass

            @step(name="Send Failure")
            def send_failure():
                pass
        """)
        test_file = tmp_path / "dotted_except.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)
        edges = flows[0].edges

        to_failure = [e for e in edges if e.to_step == "send_failure"]
        assert len(to_failure) == 1
        assert to_failure[0].branch == "except PaymentError"

    def test_try_inside_if_does_not_crash(self, tmp_path: Path) -> None:
        """Nested try inside if/else traverses without error; inner labels win."""
        source = dedent("""
            from flowdoc import step

            @step(name="Process")
            def process():
                if True:
                    try:
                        charge()
                    except:
                        log_error()
                else:
                    skip()

            @step(name="Charge")
            def charge():
                pass

            @step(name="Log Error")
            def log_error():
                pass

            @step(name="Skip")
            def skip():
                pass
        """)
        test_file = tmp_path / "nested.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)
        edges = flows[0].edges

        to_charge = [e for e in edges if e.to_step == "charge"]
        to_log = [e for e in edges if e.to_step == "log_error"]
        to_skip = [e for e in edges if e.to_step == "skip"]

        assert len(to_charge) == 1 and to_charge[0].branch == "try"
        assert len(to_log) == 1 and to_log[0].branch == "except"
        assert len(to_skip) == 1 and to_skip[0].branch == "else"


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


class TestFactoryFunctionFlows:
    """Tests for @flow decorated factory functions with nested @step inner functions."""

    def setup_method(self) -> None:
        clear_flow_registry()

    def test_factory_function_with_nested_steps(self, tmp_path: Path) -> None:
        """@flow on a factory function discovers nested @step inner functions."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Order API")
            def create_order_api():
                @step(name="Create Order")
                def create_order():
                    return validate_order()

                @step(name="Validate Order")
                def validate_order():
                    pass

                return create_order
        """)

        test_file = tmp_path / "factory.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]
        assert flow.name == "Order API"
        assert len(flow.steps) == 2
        step_names = {s.name for s in flow.steps}
        assert step_names == {"Create Order", "Validate Order"}

        assert len(flow.edges) == 1
        assert flow.edges[0].from_step == "create_order"
        assert flow.edges[0].to_step == "validate_order"

    def test_factory_flow_metadata_extracted(self, tmp_path: Path) -> None:
        """Factory function @flow(name=..., description=...) args land on FlowData."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Order API", description="HTTP order endpoints")
            def create_api():
                @step(name="Endpoint")
                def endpoint():
                    pass
        """)
        test_file = tmp_path / "metadata.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        assert flows[0].name == "Order API"
        assert flows[0].description == "HTTP order endpoints"

    def test_empty_factory_flow(self, tmp_path: Path) -> None:
        """@flow factory with no nested @step still produces a flow with zero steps."""
        source = dedent("""
            from flowdoc import flow

            @flow(name="Empty Factory")
            def create_empty():
                return None
        """)
        test_file = tmp_path / "empty.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        assert flows[0].name == "Empty Factory"
        assert flows[0].steps == []
        assert flows[0].edges == []

    def test_async_factory_function(self, tmp_path: Path) -> None:
        """@flow on async factory function with async nested steps."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Async Factory")
            async def create_app():
                @step(name="Start")
                async def start():
                    await finish()

                @step(name="Finish")
                async def finish():
                    pass
        """)
        test_file = tmp_path / "async_factory.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]
        assert flow.name == "Async Factory"
        assert len(flow.steps) == 2
        assert any(e.from_step == "start" and e.to_step == "finish" for e in flow.edges)

    def test_fastapi_style_factory(self, tmp_path: Path) -> None:
        """Factory with FastAPI-style @app.post + @step stacked decorators."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Order API")
            def create_app():
                app = FastAPI()

                @app.post("/orders")
                @step(name="Create Order Endpoint")
                async def create_order():
                    await validate()

                @step(name="Validate")
                async def validate():
                    pass

                return app
        """)
        test_file = tmp_path / "fastapi_factory.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 1
        flow = flows[0]
        assert len(flow.steps) == 2
        step_names = {s.name for s in flow.steps}
        assert step_names == {"Create Order Endpoint", "Validate"}
        assert any(e.from_step == "create_order" and e.to_step == "validate" for e in flow.edges)

    def test_factory_plus_top_level_steps(self, tmp_path: Path) -> None:
        """A factory flow and top-level standalone @step functions coexist as separate flows."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Factory Flow")
            def factory():
                @step(name="Nested A")
                def nested_a():
                    pass

            @step(name="Top Level B")
            def top_b():
                pass
        """)
        test_file = tmp_path / "coexist.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        assert len(flows) == 2
        factory_flow = next(f for f in flows if f.name == "Factory Flow")
        function_flow = next(f for f in flows if f.name != "Factory Flow")

        assert [s.name for s in factory_flow.steps] == ["Nested A"]
        assert [s.name for s in function_flow.steps] == ["Top Level B"]

    def test_factory_step_calls_top_level_step(self, tmp_path: Path) -> None:
        """A nested @step inside a factory can call a top-level @step."""
        source = dedent("""
            from flowdoc import flow, step

            @step(name="Helper")
            def helper():
                pass

            @flow(name="API")
            def create():
                @step(name="Endpoint")
                def endpoint():
                    helper()
        """)
        test_file = tmp_path / "cross_call.py"
        test_file.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(test_file)

        factory_flow = next(f for f in flows if f.name == "API")
        assert any(e.from_step == "endpoint" and e.to_step == "helper" for e in factory_flow.edges)


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


class TestStepRegistry:
    """Tests for StepRegistry."""

    def test_register_and_resolve_qualified(self) -> None:
        """Steps can be resolved by qualified name."""
        registry = StepRegistry()
        step = StepData(name="Validate", function_name="validate", description="")
        registry.register("orders.validation", step)

        result = registry.resolve("some.module", "orders.validation.validate")
        assert result is not None
        assert result.name == "Validate"

    def test_resolve_relative_to_module(self) -> None:
        """Steps can be resolved relative to calling module."""
        registry = StepRegistry()
        step = StepData(name="Validate", function_name="validate", description="")
        registry.register("orders.validation", step)

        result = registry.resolve("orders.validation", "validate")
        assert result is not None
        assert result.name == "Validate"

    def test_resolve_by_function_name(self) -> None:
        """Steps can be resolved by bare function name (suffix match)."""
        registry = StepRegistry()
        step = StepData(name="Check Inventory", function_name="check_inventory", description="")
        registry.register("orders.validation", step)

        result = registry.resolve("orders.processor", "check_inventory")
        assert result is not None
        assert result.name == "Check Inventory"

    def test_resolve_returns_none_for_unknown(self) -> None:
        """Unknown calls return None."""
        registry = StepRegistry()
        result = registry.resolve("some.module", "unknown_function")
        assert result is None

    def test_all_steps(self) -> None:
        """all_steps() returns all registered steps."""
        registry = StepRegistry()
        step1 = StepData(name="Step A", function_name="step_a", description="")
        step2 = StepData(name="Step B", function_name="step_b", description="")
        registry.register("mod1", step1)
        registry.register("mod2", step2)

        steps = registry.all_steps()
        assert len(steps) == 2
        names = {s.name for s in steps}
        assert names == {"Step A", "Step B"}


class TestPathToModule:
    """Tests for _path_to_module()."""

    def test_simple_file(self, tmp_path: Path) -> None:
        """Convert simple .py file to module name."""
        parser = FlowParser()
        result = parser._path_to_module(tmp_path / "orders.py", tmp_path)
        assert result == "orders"

    def test_nested_file(self, tmp_path: Path) -> None:
        """Convert nested file to dotted path."""
        parser = FlowParser()
        result = parser._path_to_module(tmp_path / "pkg" / "sub" / "module.py", tmp_path)
        assert result == "pkg.sub.module"

    def test_init_file(self, tmp_path: Path) -> None:
        """__init__.py converts to package name."""
        parser = FlowParser()
        result = parser._path_to_module(tmp_path / "pkg" / "__init__.py", tmp_path)
        assert result == "pkg"


class TestParseDirectory:
    """Tests for parse_directory()."""

    def test_parse_directory_finds_flows(self) -> None:
        """parse_directory discovers flows in fixture directory."""
        fixtures_dir = Path(__file__).parent / "fixtures" / "cross_module"
        parser = FlowParser()
        flows = parser.parse_directory(fixtures_dir)

        assert len(flows) > 0
        flow_names = [f.name for f in flows]
        assert "Order Processing" in flow_names

    def test_parse_directory_single_file(self, tmp_path: Path) -> None:
        """parse_directory works with a single file."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Test Flow")
            class TestFlow:
                @step(name="Start")
                def start(self):
                    pass
        """)
        file_path = tmp_path / "flow.py"
        file_path.write_text(source)

        parser = FlowParser()
        flows = parser.parse_directory(file_path)
        assert len(flows) == 1
        assert flows[0].name == "Test Flow"

    def test_parse_directory_with_factory_flow(self, tmp_path: Path) -> None:
        """parse_directory discovers @flow factory functions with nested steps."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Order API")
            def create_app():
                @step(name="Create Order")
                def create_order():
                    return validate_order()

                @step(name="Validate Order")
                def validate_order():
                    pass
        """)
        file_path = tmp_path / "factory_flow.py"
        file_path.write_text(source)

        parser = FlowParser()
        flows = parser.parse_directory(file_path)

        assert len(flows) == 1
        flow = flows[0]
        assert flow.name == "Order API"
        assert len(flow.steps) == 2
        assert any(
            e.from_step == "create_order" and e.to_step == "validate_order" for e in flow.edges
        )

    def test_unresolved_calls_ignored(self, tmp_path: Path) -> None:
        """Calls to non-step functions don't create edges."""
        source = dedent("""
            from flowdoc import step

            @step(name="Start")
            def start():
                helper_function()
                return end()

            @step(name="End")
            def end():
                pass

            def helper_function():
                pass
        """)
        file_path = tmp_path / "flow.py"
        file_path.write_text(source)

        parser = FlowParser()
        flows = parser.parse_directory(file_path)
        assert len(flows) == 1
        edge_targets = [e.to_step for e in flows[0].edges]
        assert "end" in edge_targets
        assert "helper_function" not in edge_targets


class TestDocstringExtraction:
    """Tests for docstring extraction."""

    def setup_method(self) -> None:
        clear_flow_registry()

    def test_docstring_extraction(self, tmp_path: Path) -> None:
        """Docstrings are extracted from decorated functions."""
        source = dedent("""
            from flowdoc import step

            @step(name="Process")
            def process():
                \"\"\"Process the incoming data.\"\"\"
                pass
        """)
        file_path = tmp_path / "flow.py"
        file_path.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(file_path)
        assert flows[0].steps[0].docstring == "Process the incoming data."

    def test_docstring_none_when_missing(self, tmp_path: Path) -> None:
        """Docstring is None when function has no docstring."""
        source = dedent("""
            from flowdoc import step

            @step(name="Process")
            def process():
                pass
        """)
        file_path = tmp_path / "flow.py"
        file_path.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(file_path)
        assert flows[0].steps[0].docstring is None

    def test_docstring_multiline(self, tmp_path: Path) -> None:
        """Multiline docstrings are extracted correctly."""
        source = dedent("""
            from flowdoc import step

            @step(name="Process")
            def process():
                \"\"\"Process the incoming data.

                This step handles all incoming data
                and validates it before processing.
                \"\"\"
                pass
        """)
        file_path = tmp_path / "flow.py"
        file_path.write_text(source)

        parser = FlowParser()
        flows = parser.parse_file(file_path)
        docstring = flows[0].steps[0].docstring
        assert docstring is not None
        assert "Process the incoming data." in docstring
        assert "validates it before processing." in docstring
