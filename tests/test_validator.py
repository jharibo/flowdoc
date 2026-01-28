"""Tests for flow validation logic."""

import pytest

from flowdoc.models import Edge, FlowData, StepData
from flowdoc.validator import FlowValidator


@pytest.fixture
def validator() -> FlowValidator:
    return FlowValidator()


class TestValidLinearFlow:
    """Tests for valid flow configurations."""

    def test_valid_linear_flow_no_messages(self, validator: FlowValidator) -> None:
        """A clean linear flow should produce no messages."""
        flow = FlowData(
            name="Valid",
            type="class",
            steps=[
                StepData(name="A", function_name="a", description=""),
                StepData(name="B", function_name="b", description=""),
                StepData(name="C", function_name="c", description=""),
            ],
            edges=[
                Edge(from_step="a", to_step="b"),
                Edge(from_step="b", to_step="c"),
            ],
            description="",
        )
        messages = validator.validate(flow)
        assert len(messages) == 0

    def test_single_step_flow_valid(self, validator: FlowValidator) -> None:
        """A single step flow is valid (it's both entry and terminal)."""
        flow = FlowData(
            name="Single",
            type="class",
            steps=[StepData(name="Only", function_name="only", description="")],
            edges=[],
            description="",
        )
        messages = validator.validate(flow)
        assert len(messages) == 0

    def test_empty_flow_no_messages(self, validator: FlowValidator) -> None:
        """An empty flow produces no messages."""
        flow = FlowData(
            name="Empty",
            type="class",
            steps=[],
            edges=[],
            description="",
        )
        messages = validator.validate(flow)
        assert len(messages) == 0


class TestEntryPointDetection:
    """Tests for entry point validation."""

    def test_no_entry_point_circular(self, validator: FlowValidator) -> None:
        """Circular flow where all steps are targets should produce error."""
        flow = FlowData(
            name="Circular",
            type="class",
            steps=[
                StepData(name="A", function_name="a", description=""),
                StepData(name="B", function_name="b", description=""),
            ],
            edges=[
                Edge(from_step="a", to_step="b"),
                Edge(from_step="b", to_step="a"),
            ],
            description="",
        )
        messages = validator.validate(flow)
        errors = [m for m in messages if m.severity == "error"]
        assert len(errors) == 1
        assert "No entry point" in errors[0].message

    def test_multiple_entry_points(self, validator: FlowValidator) -> None:
        """Multiple entry points should produce a warning."""
        flow = FlowData(
            name="Multi Entry",
            type="class",
            steps=[
                StepData(name="Entry A", function_name="entry_a", description=""),
                StepData(name="Entry B", function_name="entry_b", description=""),
                StepData(name="Shared", function_name="shared", description=""),
            ],
            edges=[
                Edge(from_step="entry_a", to_step="shared"),
                Edge(from_step="entry_b", to_step="shared"),
            ],
            description="",
        )
        messages = validator.validate(flow)
        warnings = [m for m in messages if m.severity == "warning"]
        assert any("Multiple entry points" in w.message for w in warnings)


class TestDeadStepDetection:
    """Tests for dead step detection."""

    def test_dead_step_disconnected(self, validator: FlowValidator) -> None:
        """A step with no incoming or outgoing edges is dead."""
        flow = FlowData(
            name="Dead Step",
            type="class",
            steps=[
                StepData(name="Active", function_name="active", description=""),
                StepData(name="Next", function_name="next_step", description=""),
                StepData(name="Orphan", function_name="orphan", description=""),
            ],
            edges=[Edge(from_step="active", to_step="next_step")],
            description="",
        )
        messages = validator.validate(flow)
        dead = [m for m in messages if "disconnected" in m.message]
        assert len(dead) == 1
        assert dead[0].step_name == "Orphan"

    def test_single_step_not_reported_as_dead(self, validator: FlowValidator) -> None:
        """A single step flow should not report the step as dead."""
        flow = FlowData(
            name="Single",
            type="class",
            steps=[StepData(name="Only", function_name="only", description="")],
            edges=[],
            description="",
        )
        messages = validator.validate(flow)
        dead = [m for m in messages if "disconnected" in m.message]
        assert len(dead) == 0


class TestUnreachableStepDetection:
    """Tests for unreachable step detection."""

    def test_unreachable_step(self, validator: FlowValidator) -> None:
        """A step not reachable from any entry point should be flagged."""
        # island_b is targeted by island_a but island_a is targeted by reachable,
        # so island cluster is only reachable if connected to entry. Here we make
        # island_b targeted by a non-entry step that itself is not reachable.
        flow = FlowData(
            name="Unreachable",
            type="class",
            steps=[
                StepData(name="Start", function_name="start", description=""),
                StepData(name="Reachable", function_name="reachable", description=""),
                StepData(name="Island A", function_name="island_a", description=""),
                StepData(name="Island B", function_name="island_b", description=""),
            ],
            edges=[
                Edge(from_step="start", to_step="reachable"),
                # island_a -> island_b forms a disconnected cluster, but island_a
                # is also an entry point. To make island_b truly unreachable,
                # we need island_a to be targeted (not an entry) but not reachable.
                Edge(from_step="island_a", to_step="island_b"),
                Edge(from_step="island_b", to_step="island_a"),  # circular island
            ],
            description="",
        )
        messages = validator.validate(flow)
        unreachable = [m for m in messages if "not reachable" in m.message]
        # Both island_a and island_b form a cycle not connected to start
        assert len(unreachable) == 2

    def test_all_reachable(self, validator: FlowValidator) -> None:
        """When all steps are reachable, no unreachable messages."""
        flow = FlowData(
            name="All Reachable",
            type="class",
            steps=[
                StepData(name="A", function_name="a", description=""),
                StepData(name="B", function_name="b", description=""),
                StepData(name="C", function_name="c", description=""),
            ],
            edges=[
                Edge(from_step="a", to_step="b"),
                Edge(from_step="b", to_step="c"),
            ],
            description="",
        )
        messages = validator.validate(flow)
        unreachable = [m for m in messages if "not reachable" in m.message]
        assert len(unreachable) == 0

    def test_branching_flow_all_reachable(self, validator: FlowValidator) -> None:
        """Branching flow where both branches are reachable."""
        flow = FlowData(
            name="Branching",
            type="class",
            steps=[
                StepData(name="Start", function_name="start", description=""),
                StepData(name="Left", function_name="left", description=""),
                StepData(name="Right", function_name="right", description=""),
            ],
            edges=[
                Edge(from_step="start", to_step="left", branch="if"),
                Edge(from_step="start", to_step="right", branch="else"),
            ],
            description="",
        )
        messages = validator.validate(flow)
        unreachable = [m for m in messages if "not reachable" in m.message]
        assert len(unreachable) == 0
