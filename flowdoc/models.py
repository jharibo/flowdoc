from dataclasses import dataclass, field


@dataclass
class Edge:
    from_step: str
    to_step: str
    branch: str | None = None
    line_number: int | None = None


@dataclass
class StepData:
    name: str
    function_name: str
    description: str = ""
    calls: list[Edge] = field(default_factory=list)


@dataclass
class FlowData:
    name: str
    type: str
    steps: list[StepData]
    edges: list[Edge]
    description: str = ""
