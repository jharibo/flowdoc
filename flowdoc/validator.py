"""Flow validation logic for detecting consistency issues.

All validation is advisory -- warnings help catch drift but do not block execution.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from flowdoc.models import FlowData


@dataclass
class ValidationMessage:
    """A single validation finding.

    :param severity: One of 'error', 'warning', 'info'
    :param message: Human-readable description of the issue
    :param step_name: Name of the step involved, or empty for flow-level issues
    """

    severity: str
    message: str
    step_name: str = ""


class FlowValidator:
    """Validates flow data for consistency issues.

    Checks for common problems like dead steps, missing entry points,
    and unreachable steps. All validation is advisory.
    """

    def validate(self, flow_data: FlowData) -> list[ValidationMessage]:
        """Run all validation checks on a flow.

        :param flow_data: The flow data to validate
        :return: List of validation messages (empty if no issues found)
        """
        messages: list[ValidationMessage] = []
        messages.extend(self._check_entry_points(flow_data))
        messages.extend(self._check_dead_steps(flow_data))
        messages.extend(self._check_unreachable_steps(flow_data))
        return messages

    def _check_entry_points(self, flow_data: FlowData) -> list[ValidationMessage]:
        """Check for missing or multiple entry points.

        Entry points are steps that are never the target of any edge.

        :param flow_data: The flow data to check
        :return: List of validation messages
        """
        if not flow_data.steps:
            return []

        targeted = {e.to_step for e in flow_data.edges}
        entry_points = [s for s in flow_data.steps if s.function_name not in targeted]

        if len(entry_points) == 0:
            return [
                ValidationMessage(
                    severity="error",
                    message="No entry point found; all steps are targets of other steps "
                    "(possible circular flow)",
                )
            ]

        if len(entry_points) > 1:
            names = ", ".join(s.name for s in entry_points)
            return [
                ValidationMessage(
                    severity="warning",
                    message=f"Multiple entry points found: {names}",
                )
            ]

        return []

    def _check_dead_steps(self, flow_data: FlowData) -> list[ValidationMessage]:
        """Check for dead steps (decorated but completely disconnected).

        A dead step has no incoming edges and no outgoing edges, meaning it
        participates in nothing. Single-step flows are exempt.

        :param flow_data: The flow data to check
        :return: List of validation messages
        """
        if len(flow_data.steps) <= 1:
            return []

        messages: list[ValidationMessage] = []
        targeted = {e.to_step for e in flow_data.edges}
        sources = {e.from_step for e in flow_data.edges}

        for step in flow_data.steps:
            fn = step.function_name
            has_incoming = fn in targeted
            has_outgoing = fn in sources

            if not has_incoming and not has_outgoing:
                messages.append(
                    ValidationMessage(
                        severity="warning",
                        message=f"Step '{step.name}' is disconnected (no incoming or outgoing edges)",
                        step_name=step.name,
                    )
                )

        return messages

    def _check_unreachable_steps(self, flow_data: FlowData) -> list[ValidationMessage]:
        """Check for steps not reachable from any entry point.

        Uses BFS from all entry points to find reachable steps.

        :param flow_data: The flow data to check
        :return: List of validation messages
        """
        if not flow_data.steps or not flow_data.edges:
            return []

        targeted = {e.to_step for e in flow_data.edges}
        entry_points = {s.function_name for s in flow_data.steps if s.function_name not in targeted}

        if not entry_points:
            return []  # Circular flow, handled by _check_entry_points

        # Build adjacency list for O(V + E) BFS
        adjacency: dict[str, list[str]] = defaultdict(list)
        for edge in flow_data.edges:
            adjacency[edge.from_step].append(edge.to_step)

        reachable: set[str] = set(entry_points)
        queue: deque[str] = deque(entry_points)

        while queue:
            current = queue.popleft()
            for neighbor in adjacency.get(current, []):
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    queue.append(neighbor)

        # Find unreachable steps
        messages: list[ValidationMessage] = []
        for step in flow_data.steps:
            if step.function_name not in reachable:
                messages.append(
                    ValidationMessage(
                        severity="warning",
                        message=f"Step '{step.name}' is not reachable from any entry point",
                        step_name=step.name,
                    )
                )

        return messages
