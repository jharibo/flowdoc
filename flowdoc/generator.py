"""Diagram generators for rendering flow data as visual diagrams.

Supports Graphviz (PNG, SVG, PDF, DOT) and Mermaid output formats.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path

from graphviz import Digraph

from flowdoc.models import Edge, FlowData, StepData


class DiagramGenerator(ABC):
    """Base class for all diagram generators.

    Subclasses must implement :meth:`generate` to produce output files.
    """

    @abstractmethod
    def generate(self, flow_data: FlowData, output_path: Path) -> Path:
        """Generate a diagram from flow data.

        :param flow_data: The flow data to render
        :param output_path: Path for the output file
        :return: Path to the generated file
        """
        ...

    @staticmethod
    def _classify_step(step: StepData, edges: list[Edge]) -> str:
        """Classify a step by its outgoing edge count.

        :param step: The step to classify
        :param edges: All edges in the flow
        :return: One of 'decision', 'terminal', or 'regular'
        """
        outgoing = [e for e in edges if e.from_step == step.function_name]
        if len(outgoing) == 0:
            return "terminal"
        if len(outgoing) >= 2:
            return "decision"
        return "regular"

    @staticmethod
    def _get_branch_label(branch: str | None) -> str | None:
        """Convert branch type to a human-readable label.

        :param branch: Branch type ('if', 'else', or None)
        :return: Label string or None
        """
        if branch == "if":
            return "yes"
        if branch == "else":
            return "no"
        return None


class GraphvizGenerator(DiagramGenerator):
    """Generates diagrams using Graphviz.

    Supports PNG, SVG, PDF, and DOT output formats.

    :param output_format: One of 'png', 'svg', 'pdf', 'dot'
    :param direction: Graph direction - 'TB' (top-bottom) or 'LR' (left-right)
    """

    # Node styling by classification
    NODE_STYLES: dict[str, dict[str, str]] = {
        "regular": {"shape": "box", "style": "filled", "fillcolor": "lightblue"},
        "decision": {"shape": "diamond", "style": "filled", "fillcolor": "lightyellow"},
        "terminal": {"shape": "ellipse", "style": "filled", "fillcolor": "lightgreen"},
    }

    def __init__(
        self,
        output_format: str = "png",
        direction: str = "TB",
        **kwargs: str,
    ) -> None:
        """Initialize Graphviz generator.

        :param output_format: Output format ('png', 'svg', 'pdf', 'dot')
        :param direction: Layout direction ('TB' or 'LR')
        :param kwargs: Additional keyword arguments (ignored)
        """
        self.output_format = output_format
        self.direction = direction

    def generate(self, flow_data: FlowData, output_path: Path) -> Path:
        """Generate a Graphviz diagram.

        :param flow_data: The flow data to render
        :param output_path: Path for the output file (without extension for rendered formats)
        :return: Path to the generated file
        """
        dot = self._create_graph(flow_data)

        if self.output_format == "dot":
            # Write DOT source directly
            dot_path = output_path.with_suffix(".dot")
            dot_path.write_text(dot.source, encoding="utf-8")
            return dot_path

        # Render to image format
        # graphviz.render() appends the format extension automatically
        stem = str(output_path.with_suffix(""))
        dot.render(filename=stem, format=self.output_format, cleanup=True)
        return Path(f"{stem}.{self.output_format}")

    def _create_graph(self, flow_data: FlowData) -> Digraph:
        """Create a Graphviz Digraph from flow data.

        :param flow_data: The flow data to render
        :return: Configured Digraph object
        """
        dot = Digraph(
            name=flow_data.name,
            comment=flow_data.description or flow_data.name,
        )
        dot.attr(rankdir=self.direction)
        dot.attr("graph", label=flow_data.name, labelloc="t", fontsize="16")

        self._add_nodes(dot, flow_data)
        self._add_edges(dot, flow_data.edges)

        return dot

    def _add_nodes(self, dot: Digraph, flow_data: FlowData) -> None:
        """Add styled nodes to the graph.

        :param dot: Graphviz Digraph to add nodes to
        :param flow_data: Flow data containing steps and edges
        """
        for step in flow_data.steps:
            classification = self._classify_step(step, flow_data.edges)
            style = self.NODE_STYLES[classification]
            dot.node(step.function_name, label=step.name, **style)

    def _add_edges(self, dot: Digraph, edges: list[Edge]) -> None:
        """Add edges to the graph.

        :param dot: Graphviz Digraph to add edges to
        :param edges: List of edges to add
        """
        for edge in edges:
            attrs: dict[str, str] = {}
            label = self._get_branch_label(edge.branch)
            if label:
                attrs["label"] = label
            dot.edge(edge.from_step, edge.to_step, **attrs)


class MermaidGenerator(DiagramGenerator):
    """Generates Mermaid flowchart diagrams.

    Produces Mermaid markdown syntax suitable for GitHub/GitLab READMEs.

    :param direction: Flowchart direction - 'TD' (top-down) or 'LR' (left-right)
    """

    # Mermaid keywords that conflict with node IDs
    RESERVED_WORDS = frozenset({"end", "graph", "subgraph", "direction", "click", "style", "class"})

    def __init__(self, direction: str = "TD", **kwargs: str) -> None:
        """Initialize Mermaid generator.

        :param direction: Flowchart direction ('TD' or 'LR')
        :param kwargs: Additional keyword arguments (ignored)
        """
        # Map TB to TD for Mermaid compatibility
        self.direction = "TD" if direction == "TB" else direction

    def generate(self, flow_data: FlowData, output_path: Path) -> Path:
        """Generate a Mermaid diagram file.

        :param flow_data: The flow data to render
        :param output_path: Path for the output file
        :return: Path to the generated .mmd file
        """
        mermaid_text = self._render(flow_data)
        mmd_path = output_path.with_suffix(".mmd")
        mmd_path.write_text(mermaid_text, encoding="utf-8")
        return mmd_path

    def _render(self, flow_data: FlowData) -> str:
        """Render flow data as Mermaid syntax.

        :param flow_data: The flow data to render
        :return: Mermaid flowchart string
        """
        lines: list[str] = [f"flowchart {self.direction}"]

        # Add nodes
        for step in flow_data.steps:
            node_id = self._sanitize_id(step.function_name)
            classification = self._classify_step(step, flow_data.edges)
            label = self._escape_label(step.name)
            node_def = self._node_shape(node_id, label, classification)
            lines.append(f"    {node_def}")

        # Blank line between nodes and edges
        if flow_data.edges:
            lines.append("")

        # Add edges
        for edge in flow_data.edges:
            from_id = self._sanitize_id(edge.from_step)
            to_id = self._sanitize_id(edge.to_step)
            label = self._get_branch_label(edge.branch)
            if label:
                lines.append(f"    {from_id} -->|{label}| {to_id}")
            else:
                lines.append(f"    {from_id} --> {to_id}")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _node_shape(node_id: str, label: str, classification: str) -> str:
        """Format a node definition with the appropriate Mermaid shape.

        :param node_id: Sanitized node identifier
        :param label: Display label for the node
        :param classification: One of 'decision', 'terminal', 'regular'
        :return: Mermaid node definition string
        """
        if classification == "decision":
            return f"{node_id}{{{label}}}"
        if classification == "terminal":
            return f"{node_id}([{label}])"
        return f"{node_id}[{label}]"

    def _sanitize_id(self, name: str) -> str:
        """Sanitize a function name for use as a Mermaid node ID.

        :param name: Raw function name
        :return: Safe Mermaid node ID
        """
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if sanitized.lower() in self.RESERVED_WORDS:
            sanitized = f"step_{sanitized}"
        return sanitized

    @staticmethod
    def _escape_label(label: str) -> str:
        """Escape special characters in a Mermaid label.

        :param label: Raw label text
        :return: Escaped label text safe for Mermaid
        """
        # Mermaid uses quotes for labels with special chars
        if any(c in label for c in '[]{}()|"'):
            escaped = label.replace('"', "#quot;")
            return f'"{escaped}"'
        return label


def create_generator(output_format: str, **kwargs: str) -> DiagramGenerator:
    """Factory function to create a diagram generator.

    :param output_format: One of 'png', 'svg', 'pdf', 'dot', 'mermaid'
    :param kwargs: Additional arguments passed to the generator constructor
    :return: Appropriate DiagramGenerator instance
    :raises ValueError: If format is not supported
    """
    if output_format in ("png", "svg", "pdf", "dot"):
        return GraphvizGenerator(output_format=output_format, **kwargs)
    if output_format == "mermaid":
        return MermaidGenerator(**kwargs)
    raise ValueError(f"Unsupported format: {output_format}. Supported: png, svg, pdf, dot, mermaid")
