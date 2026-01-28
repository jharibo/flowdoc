"""Tests for diagram generators (Graphviz and Mermaid)."""

import shutil
from pathlib import Path

import pytest

from flowdoc.generator import (
    DiagramGenerator,
    GraphvizGenerator,
    MermaidGenerator,
    create_generator,
)
from flowdoc.models import Edge, FlowData, StepData


class TestGraphvizGeneratorDOT:
    """Tests for Graphviz DOT output (no system binary required)."""

    def test_generates_dot_output(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that DOT format output is generated correctly."""
        gen = GraphvizGenerator(output_format="dot")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        assert output.suffix == ".dot"
        assert output.exists()

        content = output.read_text()
        assert "Test Flow" in content
        assert "start" in content
        assert "validate" in content
        assert "process" in content
        assert "reject" in content

    def test_decision_node_is_diamond(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that decision nodes (2+ outgoing edges) get diamond shape."""
        gen = GraphvizGenerator(output_format="dot")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        # validate has 2 outgoing edges -> diamond
        assert "validate" in content
        assert "shape=diamond" in content

    def test_terminal_node_is_ellipse(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that terminal nodes (0 outgoing edges) get ellipse shape."""
        gen = GraphvizGenerator(output_format="dot")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        # process and reject have 0 outgoing edges -> ellipse
        assert "shape=ellipse" in content

    def test_regular_node_is_box(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that regular nodes (1 outgoing edge) get box shape."""
        gen = GraphvizGenerator(output_format="dot")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        # start has 1 outgoing edge -> box
        assert "shape=box" in content

    def test_edge_labels_for_branches(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that branched edges have yes/no labels."""
        gen = GraphvizGenerator(output_format="dot")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        assert "label=yes" in content
        assert "label=no" in content

    def test_direction_lr(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that LR direction is applied."""
        gen = GraphvizGenerator(output_format="dot", direction="LR")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        assert "rankdir=LR" in content

    def test_direction_tb_default(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that TB is the default direction."""
        gen = GraphvizGenerator(output_format="dot")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        assert "rankdir=TB" in content

    def test_linear_flow_all_regular_except_terminal(
        self, tmp_path: Path, linear_flow_data: FlowData
    ) -> None:
        """Test classification in a linear flow."""
        gen = GraphvizGenerator(output_format="dot")
        output = gen.generate(linear_flow_data, tmp_path / "test")

        content = output.read_text()
        # step_c has 0 outgoing -> terminal (ellipse)
        # step_a and step_b have 1 outgoing each -> regular (box)
        assert "shape=box" in content
        assert "shape=ellipse" in content
        # No decisions in a linear flow
        assert "shape=diamond" not in content


@pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz binary not installed")
class TestGraphvizGeneratorRendered:
    """Tests for rendered Graphviz output (PNG, SVG). Requires Graphviz system binary."""

    def test_generates_png(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that PNG output is generated."""
        gen = GraphvizGenerator(output_format="png")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        assert output.suffix == ".png"
        assert output.exists()
        assert output.stat().st_size > 0

    def test_generates_svg(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that SVG output is generated."""
        gen = GraphvizGenerator(output_format="svg")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        assert output.suffix == ".svg"
        assert output.exists()

        content = output.read_text()
        assert "<svg" in content


class TestMermaidGenerator:
    """Tests for Mermaid output."""

    def test_generates_valid_output(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that Mermaid output has correct structure."""
        gen = MermaidGenerator()
        output = gen.generate(sample_flow_data, tmp_path / "test")

        assert output.suffix == ".mmd"
        assert output.exists()

        content = output.read_text()
        assert content.startswith("flowchart TD\n")
        assert "start" in content
        assert "validate" in content
        assert "process" in content
        assert "reject" in content

    def test_decision_node_shape(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that decision nodes use diamond/rhombus syntax."""
        gen = MermaidGenerator()
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        # validate has 2 outgoing edges -> {label}
        assert "validate{Validate}" in content

    def test_terminal_node_shape(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that terminal nodes use stadium/pill syntax."""
        gen = MermaidGenerator()
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        # process and reject have 0 outgoing edges -> ([label])
        assert "process([Process])" in content
        assert "reject([Reject])" in content

    def test_regular_node_shape(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that regular nodes use rectangle syntax."""
        gen = MermaidGenerator()
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        # start has 1 outgoing edge -> [label]
        assert "start[Start]" in content

    def test_edge_labels(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that branched edges have yes/no labels."""
        gen = MermaidGenerator()
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        assert "-->|yes|" in content
        assert "-->|no|" in content

    def test_edge_without_branch(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that edges without branches have no labels."""
        gen = MermaidGenerator()
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        # start -> validate has no branch
        assert "start --> validate" in content

    def test_direction_lr(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that LR direction is applied."""
        gen = MermaidGenerator(direction="LR")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        assert content.startswith("flowchart LR\n")

    def test_tb_maps_to_td(self, tmp_path: Path, sample_flow_data: FlowData) -> None:
        """Test that TB direction maps to TD for Mermaid compatibility."""
        gen = MermaidGenerator(direction="TB")
        output = gen.generate(sample_flow_data, tmp_path / "test")

        content = output.read_text()
        assert content.startswith("flowchart TD\n")

    def test_reserved_word_node_id(self, tmp_path: Path) -> None:
        """Test that Mermaid reserved words are prefixed."""
        flow_data = FlowData(
            name="Test",
            type="function",
            steps=[
                StepData(name="End Step", function_name="end", description=""),
            ],
            edges=[],
            description="",
        )

        gen = MermaidGenerator()
        output = gen.generate(flow_data, tmp_path / "test")

        content = output.read_text()
        assert "step_end" in content

    def test_special_characters_in_label(self, tmp_path: Path) -> None:
        """Test that special characters in step names are escaped."""
        flow_data = FlowData(
            name="Test",
            type="function",
            steps=[
                StepData(name="Check [Valid]", function_name="check_valid", description=""),
            ],
            edges=[],
            description="",
        )

        gen = MermaidGenerator()
        output = gen.generate(flow_data, tmp_path / "test")

        content = output.read_text()
        # Should be quoted due to brackets
        assert '"Check [Valid]"' in content


class TestCreateGeneratorFactory:
    """Tests for the create_generator factory function."""

    def test_creates_graphviz_for_png(self) -> None:
        gen = create_generator("png")
        assert isinstance(gen, GraphvizGenerator)

    def test_creates_graphviz_for_svg(self) -> None:
        gen = create_generator("svg")
        assert isinstance(gen, GraphvizGenerator)

    def test_creates_graphviz_for_dot(self) -> None:
        gen = create_generator("dot")
        assert isinstance(gen, GraphvizGenerator)

    def test_creates_graphviz_for_pdf(self) -> None:
        gen = create_generator("pdf")
        assert isinstance(gen, GraphvizGenerator)

    def test_creates_mermaid(self) -> None:
        gen = create_generator("mermaid")
        assert isinstance(gen, MermaidGenerator)

    def test_passes_kwargs(self) -> None:
        gen = create_generator("dot", direction="LR")
        assert isinstance(gen, GraphvizGenerator)
        assert gen.direction == "LR"

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported format"):
            create_generator("bmp")


class TestStepClassification:
    """Tests for step classification logic."""

    def test_terminal_has_no_outgoing(self) -> None:
        step = StepData(name="End", function_name="end_step", description="")
        edges = [Edge(from_step="other", to_step="end_step")]
        assert DiagramGenerator._classify_step(step, edges) == "terminal"

    def test_decision_has_multiple_outgoing(self) -> None:
        step = StepData(name="Check", function_name="check", description="")
        edges = [
            Edge(from_step="check", to_step="a"),
            Edge(from_step="check", to_step="b"),
        ]
        assert DiagramGenerator._classify_step(step, edges) == "decision"

    def test_regular_has_one_outgoing(self) -> None:
        step = StepData(name="Process", function_name="process", description="")
        edges = [Edge(from_step="process", to_step="next")]
        assert DiagramGenerator._classify_step(step, edges) == "regular"
