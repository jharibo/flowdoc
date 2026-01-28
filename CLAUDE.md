# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FlowDoc** is a Python library for generating business flow diagrams from decorator annotations in application code. Unlike existing tools that focus on technical code execution flow, FlowDoc captures and visualizes **business logic flow** - the high-level process steps that represent what the application does from a business perspective.

### Core Concept

FlowDoc uses Python decorators (`@flow` and `@step`) to mark business process steps. The library then:
1. Uses AST (Abstract Syntax Tree) analysis to detect which steps call which other steps
2. Infers the flow graph automatically from actual code calls
3. Generates diagrams in multiple formats (PNG, SVG, Mermaid, DOT)

**Key principle**: Inference over declaration. Developers only annotate "this is a business step" - FlowDoc determines connections by analyzing the code.

### Supported Patterns

FlowDoc works with multiple patterns:
- **Class-based flows**: `@flow` decorator on class, `@step` on methods
- **Function-based flows**: `@step` on standalone functions (no `@flow` needed)
- **Mixed flows**: Classes and functions working together
- **Web frameworks**: FastAPI, Flask endpoints with `@step` decorators
- **Async/await**: Full support for async functions

## Development Commands

### Setup
```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_decorators.py

# Run with coverage
uv run pytest --cov=flowdoc --cov-report=term-missing

# Run single test
uv run pytest tests/test_decorators.py::test_step_decorator
```

### Code Quality
```bash
# Format code (automatic fixes)
uv run ruff format .

# Lint and check (with automatic fixes)
uv run ruff check . --fix

# Lint without fixes
uv run ruff check .

# Type checking
uv run mypy flowdoc/
```

### CLI Usage (during development)
```bash
# Generate diagram from example
uv run flowdoc generate examples/ecommerce_order.py

# Generate with specific format
uv run flowdoc generate examples/ecommerce_order.py --format svg

# Validate flow
uv run flowdoc validate examples/ecommerce_order.py

# Get help
uv run flowdoc --help
```

## Architecture

### Core Components

1. **Decorators** (`flowdoc/decorators.py`)
   - `@flow(name, description)`: Marks a class as a business flow
   - `@step(name, description)`: Marks a method as a business process step
   - Stores metadata without altering function behavior
   - Maintains a global registry of flows

2. **Parser** (`flowdoc/parser.py`)
   - Uses AST to analyze decorated methods
   - Detects `self.method()` calls to infer flow connections
   - Tracks branching (if/else) to identify decision points
   - Builds edge graph: `{from: step_name, to: step_name, branch: 'if'/'else'/None}`

3. **Generators** (`flowdoc/generator.py`)
   - **GraphvizGenerator**: Creates PNG, SVG, PDF, DOT formats
   - **MermaidGenerator**: Creates Mermaid markdown diagrams
   - Factory pattern: `create_generator(format, **kwargs)`
   - Node types: regular (box), decision (diamond), terminal (ellipse)

4. **Validator** (`flowdoc/validator.py`)
   - Checks for dead steps (decorated but never called)
   - Detects missing entry points or multiple entry points
   - Warns about undecorated methods with business-like names
   - Advisory only - warnings don't block execution

5. **CLI** (`flowdoc/cli.py`)
   - `flowdoc generate`: Generate diagrams from source files
   - `flowdoc validate`: Validate flow consistency
   - Built with Click framework

### AST Analysis Approach

**Security-First Design**: FlowDoc uses **pure AST analysis** - no code execution.
This means it's completely safe to run on untrusted code.

FlowDoc walks the AST of each `@step` decorated function/method looking for:
- **Method calls**: `self.other_method()` → creates edge if `other_method` has `@step`
- **Function calls**: `other_function()` → creates edge if `other_function` has `@step`
- **Async calls**: `await other_function()` → handles async/await patterns
- **Conditional branches**: Tracks if we're in `if` vs `else` block
- **Multiple calls**: If a step calls 2+ other steps → it's a decision point (diamond shape)
- **No calls**: Terminal step (ellipse shape)

**What works** (99% of use cases):
- Literal string arguments: `@step(name="Process Order")`
- All standard decorator patterns
- Multiple decorators (e.g., FastAPI + @step)
- Async/await functions

**Limitations** (by design):
- Dynamic decorator arguments: `@step(name=variable)` - use literal strings instead
- Dynamic method selection: `getattr(self, method_name)()` - use explicit calls
- External object calls: `processor.handle()` - unless also decorated
- Functions as parameters: `next_step(order)` - use explicit if/else

These are documented limitations. Users should refactor to use explicit patterns for business flows.

## Development Phases

The project follows this implementation sequence:

**Phase 1**: Core Decorators & Metadata (MVP)
**Phase 2**: Parsing & AST Analysis
**Phase 3**: Diagram Generation - Graphviz (PNG, SVG, DOT)
**Phase 4**: CLI (`flowdoc generate`, `flowdoc validate`)
**Phase 5**: Validation (dead steps, entry points, warnings)
**Phase 6**: Mermaid Support
**Phase 7**: Polish & Release (config files, documentation, PyPI)

See `flowdoc-development-guide.md` for detailed checklist.

## Key Design Principles

1. **Inference Over Declaration**: Flow structure is discovered from actual code, not manually specified
2. **Lightweight Decorators**: Minimal metadata required - just name and optional description
3. **Code is Truth**: Actual Python execution determines flow; decorators are just labels
4. **Fail Gracefully**: Best-effort parsing; warn but don't crash on complex code
5. **Business Language**: Step names should describe business actions, not technical details
6. **Documentation Lives in Code**: No separate config files; decorators are the source of truth
7. **Validation is Advisory**: Warnings help catch drift but don't enforce correctness

## Code Style

- **Python Version**: 3.10 minimum (for modern type hints)
- **Formatting**: Ruff (replaces Black, isort, flake8)
- **Type Hints**: Required for all public APIs (Python 3.10+ syntax)
- **Line Length**: 100 characters
- **Docstrings**: Sphinx format for all public functions/classes (see example below)
- **Testing**: pytest, aim for high coverage of core logic

### Sphinx Docstring Format

```python
def example_function(param1: str, param2: int = 0) -> bool:
    """Brief description of function (one line).

    Longer description with more details about what the function does,
    if needed. This can span multiple lines.

    :param param1: Description of param1
    :param param2: Description of param2 (default: 0)
    :return: Description of return value
    :raises ValueError: Description of when this exception is raised
    """
```

## Example Usage Patterns

### Class-based Flow
```python
from flowdoc import flow, step

@flow(name="Order Processing", description="Handle customer orders")
class OrderProcessor:
    @step(name="Receive Order")
    def receive_order(self, order_data):
        return self.validate_payment(order_data)

    @step(name="Validate Payment")
    def validate_payment(self, order):
        if payment_valid:
            return self.fulfill_order(order)
        else:
            return self.send_failure_email(order)
```

### Function-based Flow
```python
from flowdoc import step

@step(name="Process Order")
def process_order(order_data):
    validated = validate_order(order_data)
    return charge_payment(validated)

@step(name="Validate Order")
def validate_order(order_data):
    # ... validation logic
    return order_data

@step(name="Charge Payment")
def charge_payment(order):
    if order["total"] > 0:
        return process_credit_card(order)
    else:
        return mark_as_free(order)
```

### FastAPI Integration
```python
from fastapi import FastAPI
from flowdoc import step

app = FastAPI()

@app.post("/orders")
@step(name="Create Order Endpoint")
async def create_order(order: OrderData):
    validated = await validate_order(order)
    return await save_order(validated)

@step(name="Validate Order")
async def validate_order(order: OrderData):
    # Async validation
    return order
```

**CLI Commands**:
```bash
flowdoc generate order_processor.py  # Creates order_processing.png
flowdoc generate api/orders.py --format mermaid  # For FastAPI flows
flowdoc validate order_processor.py  # Check for issues
```

## Important Implementation Notes

### When Adding New Features

1. **Always add tests first** - TDD approach preferred
2. **Update validation** if adding new decorator capabilities
3. **Document limitations** if AST analysis can't handle a pattern
4. **Add example** in `examples/` directory
5. **Keep decorators minimal** - resist adding more parameters

### When Working with AST

- Use `ast.NodeVisitor` subclasses for traversal
- Track context (current branch: if/else/None) while visiting
- Look for `ast.Call` nodes with `ast.Attribute` func (e.g., `self.method`)
- Handle nested functions carefully - only analyze top-level method body

### When Adding Output Formats

1. Create new `DiagramGenerator` subclass
2. Implement `generate(flow_data, output_path)` method
3. Add format to `create_generator()` factory
4. Add CLI option in `--format` choices
5. Add tests for the new format

### Common Pitfalls to Avoid

- Don't try to execute code - AST analysis only
- Don't enforce flow correctness - validation is advisory
- Don't add runtime behavior to decorators - they're for metadata only
- Don't require external config files - decorators should be self-contained
- Don't create dependencies between steps - let code structure define it

## File Organization (Planned)

```
flowdoc/
├── flowdoc/
│   ├── __init__.py          # Public API exports
│   ├── decorators.py        # @flow and @step decorators
│   ├── parser.py            # AST analysis and flow extraction
│   ├── generator.py         # Base class + Graphviz/Mermaid generators
│   ├── validator.py         # Flow validation logic
│   └── cli.py               # Click-based CLI commands
├── tests/
│   ├── test_decorators.py   # Decorator behavior tests
│   ├── test_parser.py       # AST parsing tests
│   ├── test_generator.py    # Diagram generation tests
│   ├── test_validator.py    # Validation logic tests
│   └── test_cli.py          # CLI integration tests
├── examples/
│   ├── ecommerce_order.py   # E-commerce flow example
│   ├── user_authentication.py  # Auth flow example
│   └── data_import.py       # Simple linear flow example
├── pyproject.toml           # Dependencies and tool config
├── README.md                # User-facing documentation
├── flowdoc-development-guide.md  # Comprehensive design doc
└── CLAUDE.md                # This file
```

## Dependencies

**Core**:
- `graphviz>=0.20` - Diagram rendering
- `click>=8.0` - CLI framework

**Development**:
- `pytest>=7.0` - Testing framework
- `ruff>=0.1.0` - Linting and formatting
- `mypy>=1.0` - Type checking

**Standard library** (no install needed):
- `ast` - Code parsing
- `inspect` - Metadata extraction
- `pathlib` - File handling

## Testing Strategy

- **Unit tests**: Each component isolated (decorators, parser, generators, validator)
- **Integration tests**: CLI commands end-to-end
- **Fixture-based**: Use pytest fixtures for sample flows
- **AST test cases**: Cover edge cases (nested if, try/except, loops, early returns)
- **Golden files**: Compare generated diagrams against known-good outputs

## Current Task

**Objective**: Build out the FlowDoc library from scratch according to the development guide.

**Approach**:
1. Follow the 7-phase implementation plan in order
2. Write tests alongside each component (TDD where practical)
3. Maintain todo list tracking progress through all phases
4. Ensure code quality standards (ruff, mypy) at each step
5. Create example files to validate functionality

**Status**: Active development - implementing phases sequentially starting with Phase 1 (Core Decorators & Metadata).

## Reference Documentation

- Full design rationale: `flowdoc-development-guide.md`
- AST module: https://docs.python.org/3/library/ast.html
- Graphviz Python: https://graphviz.readthedocs.io/
- Mermaid syntax: https://mermaid.js.org/syntax/flowchart.html
- Click documentation: https://click.palletsprojects.com/
