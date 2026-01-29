# FlowDoc

Generate business flow diagrams from Python code decorators.

Unlike tools that trace technical execution paths, FlowDoc captures **business logic flow** -- the high-level process steps that describe what your application does from a business perspective. Annotate your code with lightweight decorators, and FlowDoc uses AST analysis to infer the flow graph and render it as a diagram.

## Features

- **Inference over declaration** -- annotate steps, and FlowDoc discovers connections by analyzing your code
- **Pure AST analysis** -- no code execution, safe to run on untrusted code
- **Multiple output formats** -- PNG, SVG, PDF, DOT (via Graphviz), and Mermaid markdown
- **Flexible patterns** -- class-based flows, standalone functions, async/await, and web frameworks (FastAPI, Flask)
- **Built-in validation** -- detect dead steps, missing entry points, and other flow issues
- **CLI included** -- generate diagrams and validate flows from the command line

## Installation

```bash
pip install flowdoc
```

FlowDoc requires Python 3.10+ and [Graphviz](https://graphviz.org/download/) installed on your system for PNG/SVG/PDF output.

## Quick Start

Decorate your business logic with `@flow` and `@step`:

```python
from flowdoc import flow, step

@flow(name="Order Processing", description="Handle customer orders")
class OrderProcessor:
    @step(name="Receive Order")
    def receive_order(self, order_data):
        return self.validate_payment(order_data)

    @step(name="Validate Payment")
    def validate_payment(self, order):
        if order.get("payment_valid"):
            return self.fulfill_order(order)
        else:
            return self.send_failure_email(order)

    @step(name="Fulfill Order")
    def fulfill_order(self, order):
        return self.send_confirmation(order)

    @step(name="Send Confirmation")
    def send_confirmation(self, order):
        return {"status": "confirmed", "order": order}

    @step(name="Send Failure Email")
    def send_failure_email(self, order):
        return {"status": "failed", "order": order}
```

Generate the diagram:

```bash
flowdoc generate order_processor.py
```

FlowDoc analyzes the code, detects that `validate_payment` branches into two paths, and produces a flowchart with decision diamonds, regular steps, and terminal nodes.

## Usage

### CLI

```bash
# Generate a PNG diagram (default)
flowdoc generate mymodule.py

# Choose output format
flowdoc generate mymodule.py --format svg
flowdoc generate mymodule.py --format mermaid
flowdoc generate mymodule.py --format dot

# Validate a flow for issues
flowdoc validate mymodule.py
```

### Programmatic API

```python
from flowdoc import FlowParser, create_generator, FlowValidator

# Parse a source file
parser = FlowParser()
flows = parser.parse_file("mymodule.py")

# Generate a diagram
generator = create_generator("png")
for flow_data in flows:
    generator.generate(flow_data, "output.png")

# Validate
validator = FlowValidator()
for flow_data in flows:
    messages = validator.validate(flow_data)
    for msg in messages:
        print(f"[{msg.level}] {msg.message}")
```

## Supported Patterns

### Class-based flows

Use `@flow` on a class and `@step` on its methods. FlowDoc detects `self.method()` calls to build the graph.

### Function-based flows

Use `@step` on standalone functions. FlowDoc detects direct function calls between decorated functions.

```python
from flowdoc import step

@step(name="Process Order")
def process_order(order_data):
    validated = validate_order(order_data)
    return charge_payment(validated)

@step(name="Validate Order")
def validate_order(order_data):
    return order_data

@step(name="Charge Payment")
def charge_payment(order):
    return {"status": "charged"}
```

### Async functions

```python
from flowdoc import step

@step(name="Create Order")
async def create_order(order):
    validated = await validate_order(order)
    return await save_order(validated)
```

### Web framework integration

Works alongside FastAPI, Flask, and other decorator-based frameworks:

```python
from fastapi import FastAPI
from flowdoc import step

app = FastAPI()

@app.post("/orders")
@step(name="Create Order Endpoint")
async def create_order(order: OrderData):
    validated = await validate_order(order)
    return await save_order(validated)
```

## How It Works

FlowDoc uses Python's `ast` module to statically analyze decorated functions. For each `@step`, it walks the function body looking for:

- **Method calls** (`self.other_method()`) and **function calls** (`other_function()`) to other `@step`-decorated code
- **Conditional branches** (`if`/`else`) to identify decision points
- **Call count** to determine node shapes: multiple outgoing calls produce a diamond (decision), zero calls produce an ellipse (terminal), and single calls produce a box (regular step)

No code is ever executed during analysis.

## Limitations

These are intentional design constraints -- FlowDoc focuses on explicit, readable business flows:

- **Dynamic decorator arguments**: Use literal strings (`@step(name="Process")`) rather than variables
- **Dynamic dispatch**: `getattr(self, name)()` is not traced -- use explicit method calls
- **External object calls**: `processor.handle()` is not followed unless that object's methods are also decorated
- **Indirect references**: Passing functions as arguments is not traced -- use explicit `if`/`else`

## Development

### Setup

```bash
# Install uv (if needed)
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

# Run with coverage
uv run pytest --cov=flowdoc --cov-report=term-missing

# Run a specific test
uv run pytest tests/test_parser.py::test_class_flow_parsing
```

### Code quality

```bash
# Format
uv run ruff format .

# Lint (with auto-fix)
uv run ruff check . --fix

# Type check
uv run ty check flowdoc/
```

## Project Structure

```
flowdoc/
├── flowdoc/
│   ├── __init__.py       # Public API exports
│   ├── decorators.py     # @flow and @step decorators
│   ├── parser.py         # AST analysis and flow extraction
│   ├── generator.py      # Graphviz and Mermaid diagram generators
│   ├── validator.py      # Flow validation logic
│   └── cli.py            # CLI (Click-based)
├── tests/                # pytest test suite
├── examples/             # Example flows
├── pyproject.toml
└── LICENSE               # MIT
```

## Contributing

Contributions are welcome. To get started:

1. Fork the repository and create a feature branch
2. Install development dependencies with `uv sync`
3. Make your changes, adding tests for new functionality
4. Ensure all checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ty check flowdoc/`
5. Submit a pull request

Please keep decorators minimal, avoid executing user code, and treat validation as advisory (warnings, not errors).

## License

MIT -- see [LICENSE](LICENSE) for details.
