"""FlowDoc - Generate business flow diagrams from Python code decorators.

This package provides decorators to annotate business process steps in Python code,
and tools to automatically generate flow diagrams from those annotations.
"""

from flowdoc.decorators import flow, step
from flowdoc.discovery import discover_python_files
from flowdoc.generator import (
    DiagramGenerator,
    MermaidGenerator,
    create_generator,
)
from flowdoc.models import Edge, FlowData, StepData
from flowdoc.parser import FlowParser, StepRegistry
from flowdoc.validator import FlowValidator, ValidationMessage

try:
    from flowdoc.generator import GraphvizGenerator
except ImportError:
    pass

__version__ = "0.0.0-rc.2"

__all__ = [
    "flow",
    "step",
    "discover_python_files",
    "FlowParser",
    "StepRegistry",
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
