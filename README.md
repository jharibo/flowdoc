# FlowDoc

[![CI](https://github.com/jharibo/flowdoc/actions/workflows/ci.yml/badge.svg)](https://github.com/jharibo/flowdoc/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jharibo/flowdoc/graph/badge.svg)](https://codecov.io/gh/jharibo/flowdoc)
[![PyPI version](https://img.shields.io/pypi/v/flowdoc)](https://pypi.org/project/flowdoc/)
[![Python versions](https://img.shields.io/pypi/pyversions/flowdoc)](https://pypi.org/project/flowdoc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Generate business flow diagrams from Python code decorators.

Unlike tools that trace technical execution paths, FlowDoc captures **business logic flow** -- the high-level process steps that describe what your application does from a business perspective. Annotate your code with lightweight decorators, and FlowDoc uses AST analysis to infer the flow graph and render it as a diagram.

## ✨ Features

- **Inference over declaration** -- annotate steps, and FlowDoc discovers connections by analyzing your code
- **Pure AST analysis** -- no code execution, safe to run on untrusted code
- **Cross-module discovery** -- analyze flows spanning multiple files with automatic file discovery
- **Multiple output formats** -- Mermaid markdown (default), PNG, SVG, PDF, DOT (Graphviz formats require optional `graphviz` extra)
- **Docstring tooltips** -- include `@step` docstrings as tooltips in SVG/DOT/Mermaid output
- **Flexible patterns** -- class-based flows, standalone functions, async/await, and web frameworks (FastAPI, Flask)
- **Built-in validation** -- detect dead steps, missing entry points, and other flow issues
- **CLI included** -- generate diagrams and validate flows from the command line

## 📦 Installation

```bash
pip install flowdoc
```

FlowDoc requires Python 3.10+. The base install supports Mermaid and DOT output with no extra dependencies.

For PNG, SVG, and PDF output, install the Graphviz extra and the [Graphviz system package](https://graphviz.org/download/):

```bash
pip install flowdoc[graphviz]
```

## 🚀 Quick Start

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

## 💻 Usage

### CLI

```bash
# Generate a Mermaid diagram (default)
flowdoc generate mymodule.py

# Choose output format
flowdoc generate mymodule.py --format svg
flowdoc generate mymodule.py --format png
flowdoc generate mymodule.py --format dot

# Generate from a directory (cross-module discovery)
flowdoc generate src/

# Include docstrings as tooltips (SVG, DOT, Mermaid only)
flowdoc generate mymodule.py --format svg --docstrings

# Exclude directories during discovery
flowdoc generate src/ --exclude migrations --exclude scripts

# Validate a flow for issues
flowdoc validate mymodule.py
```

### Programmatic API

```python
from flowdoc import FlowParser, create_generator, FlowValidator

# Parse a single file
parser = FlowParser()
flows = parser.parse_file("mymodule.py")

# Or parse a directory (cross-module discovery)
flows = parser.parse_directory("src/")

# Generate a diagram
generator = create_generator("mermaid")
for flow_data in flows:
    generator.generate(flow_data, "output")

# Generate with docstring tooltips
generator = create_generator("svg", include_docstrings=True)
for flow_data in flows:
    generator.generate(flow_data, "output")

# Validate
validator = FlowValidator()
for flow_data in flows:
    messages = validator.validate(flow_data)
    for msg in messages:
        print(f"[{msg.level}] {msg.message}")
```

## 🔧 Supported Patterns

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

See [examples/fastapi/app.py](examples/fastapi/app.py) for a complete CRUD API example with `@step` decorators on endpoints.

### App-factory functions

For FastAPI/Flask app-factory patterns, decorate the factory function itself with `@flow`. FlowDoc treats it as a flow boundary and discovers nested `@step` inner functions:

```python
from fastapi import FastAPI
from flowdoc import flow, step

@flow(name="Order API")
def create_app() -> FastAPI:
    app = FastAPI()

    @app.post("/orders")
    @step(name="Create Order Endpoint")
    async def create_order(payload: dict):
        return await validate_order(payload)

    @step(name="Validate Order")
    async def validate_order(payload: dict):
        return payload

    return app
```

See [examples/fastapi_factory.py](examples/fastapi_factory.py) for a runnable example.

### Exception-handling branches

`try`/`except`/`finally` blocks are detected and labeled on edges, so business error paths (payment declines, retries, failure notifications) appear in the diagram:

```python
@step(name="Process Payment")
def process_payment(self, order):
    try:
        return self.charge_card(order)
    except PaymentError:
        return self.send_failure_email(order)
    except NetworkError:
        return self.retry_later(order)
    finally:
        self.log_attempt(order)
```

Edges are labeled `try`, `except PaymentError`, `except NetworkError`, and `finally`. See [examples/payment_retry.py](examples/payment_retry.py).

## ⚙️ How It Works

FlowDoc uses Python's `ast` module to statically analyze decorated functions. For each `@step`, it walks the function body looking for:

- **Method calls** (`self.other_method()`) and **function calls** (`other_function()`) to other `@step`-decorated code
- **Conditional branches** (`if`/`else`) to identify decision points
- **Exception handling** (`try`/`except`/`finally`) -- except handlers label edges with the exception type (e.g. `except PaymentError`), enabling business error-handling flows
- **Call count** to determine node shapes: multiple outgoing calls produce a diamond (decision), zero calls produce an ellipse (terminal), and single calls produce a box (regular step)

No code is ever executed during analysis.

## Limitations

These are intentional design constraints -- FlowDoc focuses on explicit, readable business flows:

- **Dynamic decorator arguments**: Use literal strings (`@step(name="Process")`) rather than variables
- **Dynamic dispatch**: `getattr(self, name)()` is not traced -- use explicit method calls
- **External object calls**: `processor.handle()` is not followed unless that object's methods are also decorated
- **Indirect references**: Passing functions as arguments is not traced -- use explicit `if`/`else`

## ❓ Troubleshooting

### Graphviz not found

PNG, SVG, and PDF output requires both the Python `graphviz` package and the Graphviz system package.

Install the Python extra:

```bash
pip install flowdoc[graphviz]
```

Install the system package:

- **macOS**: `brew install graphviz`
- **Ubuntu/Debian**: `sudo apt-get install graphviz`
- **Windows**: Download from [graphviz.org](https://graphviz.org/download/)

Mermaid and DOT formats do not require Graphviz.

### No flows found

Ensure your source file contains functions or methods decorated with `@step`. If using class-based flows, the class must also have the `@flow` decorator. FlowDoc only analyzes `@step` and `@flow` decorators -- it does not detect undecorated functions.

### Dynamic decorator arguments

FlowDoc only supports literal string arguments in decorators. This works:

```python
@step(name="Process Order")  # literal string
```

This does not:

```python
step_name = "Process Order"
@step(name=step_name)  # variable -- not supported
```

Use literal strings in all decorator arguments for FlowDoc to detect them.

### ImportError when running CLI

If you see `ModuleNotFoundError: No module named 'flowdoc'` after installation:

```bash
# Ensure you're using the correct Python environment
python -m flowdoc --version

# Or reinstall in your active environment
pip install --force-reinstall flowdoc
```

## 🛠️ Development

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
│   ├── discovery.py      # Cross-module file discovery
│   ├── parser.py         # AST analysis and flow extraction
│   ├── generator.py      # Graphviz and Mermaid diagram generators
│   ├── validator.py      # Flow validation logic
│   └── cli.py            # CLI (Click-based)
├── tests/                # pytest test suite
├── examples/             # Example flows
├── pyproject.toml
└── LICENSE               # MIT
```

## 🤝 Contributing

Contributions are welcome. To get started:

1. Fork the repository and create a feature branch
2. Install development dependencies with `uv sync`
3. Make your changes, adding tests for new functionality
4. Ensure all checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ty check flowdoc/`
5. Submit a pull request

Please keep decorators minimal, avoid executing user code, and treat validation as advisory (warnings, not errors).

## 📄 License

MIT -- see [LICENSE](LICENSE) for details.
