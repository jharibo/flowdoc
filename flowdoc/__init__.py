"""FlowDoc - Generate business flow diagrams from Python code decorators.

This package provides decorators to annotate business process steps in Python code,
and tools to automatically generate flow diagrams from those annotations.
"""

from flowdoc.decorators import flow, step
from flowdoc.generator import (
    DiagramGenerator,
    GraphvizGenerator,
    MermaidGenerator,
    create_generator,
)
from flowdoc.models import Edge, FlowData, StepData
from flowdoc.parser import FlowParser
from flowdoc.validator import FlowValidator, ValidationMessage

__version__ = "0.0.0-rc.1"
__all__ = [
    "flow",
    "step",
    "FlowParser",
    "FlowData",
    "StepData",
    "Edge",
    "DiagramGenerator",
    "GraphvizGenerator",
    "MermaidGenerator",
    "create_generator",
    "FlowValidator",
    "ValidationMessage",
]
