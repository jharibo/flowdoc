"""Tests for the @flow and @step decorators."""

from flowdoc.decorators import (
    FlowMetadata,
    StepMetadata,
    clear_flow_registry,
    flow,
    get_flow_registry,
    step,
)


class TestFlowDecorator:
    """Tests for the @flow decorator."""

    def setup_method(self) -> None:
        """Clear the flow registry before each test."""
        clear_flow_registry()

    def test_flow_decorator_adds_metadata(self) -> None:
        """Test that @flow decorator adds metadata to a class."""

        @flow(name="Test Flow", description="A test flow")
        class TestClass:
            pass

        assert hasattr(TestClass, "_flowdoc_meta")
        meta = TestClass._flowdoc_meta
        assert isinstance(meta, FlowMetadata)
        assert meta.name == "Test Flow"
        assert meta.description == "A test flow"

    def test_flow_decorator_registers_in_global_registry(self) -> None:
        """Test that @flow decorator registers the flow in the global registry."""

        @flow(name="Test Flow")
        class TestClass:
            pass

        registry = get_flow_registry()
        assert len(registry) == 1

        # Check that the flow is registered with correct ID
        flow_id = f"{TestClass.__module__}.{TestClass.__name__}"
        assert flow_id in registry
        flow_obj, meta = registry[flow_id]
        assert flow_obj is TestClass
        assert meta.name == "Test Flow"

    def test_flow_decorator_without_description(self) -> None:
        """Test that @flow decorator works without description parameter."""

        @flow(name="Simple Flow")
        class SimpleClass:
            pass

        meta = SimpleClass._flowdoc_meta
        assert meta.name == "Simple Flow"
        assert meta.description == ""

    def test_multiple_flows_registered(self) -> None:
        """Test that multiple flows can be registered."""

        @flow(name="Flow 1")
        class Flow1:
            pass

        @flow(name="Flow 2")
        class Flow2:
            pass

        registry = get_flow_registry()
        assert len(registry) == 2

    def test_clear_flow_registry(self) -> None:
        """Test that clear_flow_registry() clears the global registry."""

        @flow(name="Test Flow")
        class TestClass:
            pass

        assert len(get_flow_registry()) == 1
        clear_flow_registry()
        assert len(get_flow_registry()) == 0


class TestStepDecorator:
    """Tests for the @step decorator."""

    def test_step_decorator_adds_metadata(self) -> None:
        """Test that @step decorator adds metadata to a function."""

        @step(name="Test Step", description="A test step")
        def test_function() -> None:
            pass

        assert hasattr(test_function, "_flowdoc_step")
        meta = test_function._flowdoc_step
        assert isinstance(meta, StepMetadata)
        assert meta.name == "Test Step"
        assert meta.description == "A test step"
        assert meta.func_name == "test_function"

    def test_step_decorator_without_description(self) -> None:
        """Test that @step decorator works without description parameter."""

        @step(name="Simple Step")
        def simple_function() -> None:
            pass

        meta = simple_function._flowdoc_step
        assert meta.name == "Simple Step"
        assert meta.description == ""

    def test_step_decorator_preserves_function_behavior(self) -> None:
        """Test that @step decorator doesn't alter function execution."""

        @step(name="Add Numbers")
        def add(a: int, b: int) -> int:
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_step_decorator_preserves_function_name(self) -> None:
        """Test that @step decorator preserves function __name__."""

        @step(name="Test Step")
        def original_name() -> None:
            pass

        assert original_name.__name__ == "original_name"

    def test_step_decorator_on_method(self) -> None:
        """Test that @step decorator works on class methods."""

        class TestClass:
            @step(name="Process Data")
            def process(self, data: str) -> str:
                return data.upper()

        obj = TestClass()
        result = obj.process("hello")
        assert result == "HELLO"

        # Check metadata is preserved on the method
        assert hasattr(TestClass.process, "_flowdoc_step")
        meta = TestClass.process._flowdoc_step
        assert meta.name == "Process Data"


class TestIntegration:
    """Integration tests for @flow and @step working together."""

    def setup_method(self) -> None:
        """Clear the flow registry before each test."""
        clear_flow_registry()

    def test_flow_with_multiple_steps(self) -> None:
        """Test a complete flow with multiple steps."""

        @flow(name="Order Processing", description="Process customer orders")
        class OrderProcessor:
            @step(name="Receive Order", description="Accept order from customer")
            def receive_order(self, order_data: dict) -> dict:
                return {"order_id": 1, "data": order_data}

            @step(name="Validate Order")
            def validate_order(self, order: dict) -> bool:
                return bool(order.get("data"))

            @step(name="Process Payment")
            def process_payment(self, order: dict) -> bool:
                return True

        # Check flow metadata
        assert hasattr(OrderProcessor, "_flowdoc_meta")
        flow_meta = OrderProcessor._flowdoc_meta
        assert flow_meta.name == "Order Processing"
        assert flow_meta.description == "Process customer orders"

        # Check step metadata
        assert hasattr(OrderProcessor.receive_order, "_flowdoc_step")
        assert hasattr(OrderProcessor.validate_order, "_flowdoc_step")
        assert hasattr(OrderProcessor.process_payment, "_flowdoc_step")

        # Check functionality is preserved
        processor = OrderProcessor()
        order = processor.receive_order({"item": "widget"})
        assert order["order_id"] == 1
        assert processor.validate_order(order) is True
        assert processor.process_payment(order) is True

    def test_flow_registered_with_steps(self) -> None:
        """Test that flow is properly registered even with step decorators."""

        @flow(name="Simple Flow")
        class SimpleFlow:
            @step(name="Step 1")
            def step1(self) -> None:
                pass

            @step(name="Step 2")
            def step2(self) -> None:
                pass

        registry = get_flow_registry()
        assert len(registry) == 1

        flow_id = f"{SimpleFlow.__module__}.{SimpleFlow.__name__}"
        assert flow_id in registry
