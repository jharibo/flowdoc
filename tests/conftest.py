"""Shared test fixtures for FlowDoc tests."""

from pathlib import Path
from textwrap import dedent

import pytest

from flowdoc.models import Edge, FlowData, StepData


@pytest.fixture
def sample_flow_data() -> FlowData:
    """A flow with decision, regular, and terminal nodes.

    Structure: start -> validate -> {process, reject}
    - start: regular (1 outgoing)
    - validate: decision (2 outgoing, branched)
    - process: terminal (0 outgoing)
    - reject: terminal (0 outgoing)
    """
    return FlowData(
        name="Test Flow",
        type="class",
        description="A test flow",
        steps=[
            StepData(name="Start", function_name="start", description=""),
            StepData(name="Validate", function_name="validate", description=""),
            StepData(name="Process", function_name="process", description=""),
            StepData(name="Reject", function_name="reject", description=""),
        ],
        edges=[
            Edge(from_step="start", to_step="validate"),
            Edge(from_step="validate", to_step="process", branch="if"),
            Edge(from_step="validate", to_step="reject", branch="else"),
        ],
    )


@pytest.fixture
def linear_flow_data() -> FlowData:
    """A simple linear flow: A -> B -> C."""
    return FlowData(
        name="Linear Flow",
        type="class",
        description="A linear test flow",
        steps=[
            StepData(name="Step A", function_name="step_a", description=""),
            StepData(name="Step B", function_name="step_b", description=""),
            StepData(name="Step C", function_name="step_c", description=""),
        ],
        edges=[
            Edge(from_step="step_a", to_step="step_b"),
            Edge(from_step="step_b", to_step="step_c"),
        ],
    )


@pytest.fixture
def sample_source_file(tmp_path: Path) -> Path:
    """Create a sample Python file with a decorated flow."""
    source = dedent("""
        from flowdoc import flow, step

        @flow(name="Sample Flow", description="A sample flow for testing")
        class SampleFlow:
            @step(name="Start")
            def start(self):
                return self.process()

            @step(name="Process")
            def process(self):
                pass
    """)
    file_path = tmp_path / "sample_flow.py"
    file_path.write_text(source)
    return file_path
