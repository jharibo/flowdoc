"""Decorators for marking business flows and steps.

This module provides the @flow and @step decorators that allow developers to
annotate their code with business process metadata.
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

# Type variables for decorator typing
F = TypeVar("F", bound=Callable[..., Any])
C = TypeVar("C", bound=type)


class FlowMetadata:
    """Stores flow-level metadata for a decorated class or function."""

    def __init__(self, name: str, description: str = "") -> None:
        """Initialize flow metadata.

        :param name: Human-readable name of the business flow
        :param description: Optional description of what the flow does
        """
        self.name = name
        self.description = description
        self.steps: list[str] = []


class StepMetadata:
    """Stores step-level metadata for a decorated method or function."""

    def __init__(
        self,
        func: Callable[..., Any],
        name: str,
        description: str = "",
    ) -> None:
        """Initialize step metadata.

        :param func: The decorated function
        :param name: Human-readable name of the business step
        :param description: Optional description of what the step does
        """
        self.func = func
        self.name = name
        self.description = description
        self.func_name = func.__name__


# Global registry to track all flows
# Format: {flow_id: (flow_object, FlowMetadata)}
_flow_registry: dict[str, tuple[type | Callable, FlowMetadata]] = {}


def get_flow_registry() -> dict[str, tuple[Any, FlowMetadata]]:
    """Get the global flow registry.

    :return: Dictionary mapping flow IDs to (flow_object, FlowMetadata) tuples
    """
    return _flow_registry


def clear_flow_registry() -> None:
    """Clear the global flow registry.

    Useful for testing to ensure clean state between tests.
    """
    _flow_registry.clear()


def flow(name: str, description: str = "") -> Callable[[C], C]:
    """Decorator to mark a class or function as a business flow.

    This decorator adds metadata to the decorated object and registers it in the
    global flow registry for later discovery by the parser.

    :param name: Human-readable name of the business flow (e.g., "Order Processing")
    :param description: Optional description of what the flow does
    :return: Decorator function that adds flow metadata to the object

    Example::

        @flow(name="Order Processing", description="Handle customer orders")
        class OrderProcessor:
            @step(name="Receive Order")
            def receive_order(self, order_data):
                ...
    """

    def decorator(obj: C) -> C:
        flow_meta = FlowMetadata(name, description)

        # Store metadata on the object
        obj._flowdoc_meta = flow_meta

        # Register in global registry
        module = inspect.getmodule(obj)
        module_name = module.__name__ if module else "unknown"
        flow_id = f"{module_name}.{obj.__name__}"
        _flow_registry[flow_id] = (obj, flow_meta)

        return obj

    return decorator


def step(name: str, description: str = "") -> Callable[[F], F]:
    """Decorator to mark a function as a business process step.

    FlowDoc will analyze the function's code to determine:

    - Which other @step methods are called (creates edges in the flow)
    - Branching logic (if/else statements calling different steps)
    - Terminal steps (no other @step methods called)

    The decorator stores metadata but does not alter function behavior.

    :param name: Human-readable name of the step (e.g., "Validate Payment")
    :param description: Optional description of what the step does
    :return: Decorator function that adds step metadata to the function

    Example::

        @step(name="Validate Payment", description="Check payment method")
        def validate_payment(self, order):
            if payment_service.validate(order):
                return self.process_order(order)  # FlowDoc detects this edge
            else:
                return self.send_failure_email(order)  # And this edge
    """

    def decorator(func: F) -> F:
        # Store metadata on the function
        step_meta = StepMetadata(
            func=func,
            name=name,
            description=description,
        )

        func._flowdoc_step = step_meta

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Execute the original function unchanged
            return func(*args, **kwargs)

        # Preserve metadata on wrapper
        wrapper._flowdoc_step = step_meta

        return cast(F, wrapper)

    return decorator
