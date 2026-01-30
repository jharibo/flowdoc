# FlowDoc Examples

This directory contains examples demonstrating different FlowDoc patterns and use cases.

## Available Examples

| Example | Pattern | Description | File |
|---------|---------|-------------|------|
| **E-commerce Order** | Class-based flow | Order processing with payment validation and branching | [ecommerce_order.py](ecommerce_order.py) |
| **User Authentication** | Class-based flow | User login flow with validation and session management | [user_authentication.py](user_authentication.py) |
| **Data Import** | Function-based flow | Simple linear CSV import process | [data_import.py](data_import.py) |
| **FastAPI CRUD** | Function-based flow + Web framework | Product inventory API with `@step` on endpoints | [fastapi/app.py](fastapi/app.py) |

## Generating Diagrams

### PNG (default)

```bash
flowdoc generate examples/ecommerce_order.py
```

### Mermaid Markdown

```bash
flowdoc generate examples/ecommerce_order.py --format mermaid
```

### SVG

```bash
flowdoc generate examples/ecommerce_order.py --format svg
```

### DOT (Graphviz source)

```bash
flowdoc generate examples/ecommerce_order.py --format dot
```

## Validating Flows

Check for dead steps, missing entry points, and other issues:

```bash
flowdoc validate examples/ecommerce_order.py
```

## Pattern Overview

### Class-Based Flows

Use `@flow` decorator on a class and `@step` on methods:

```python
from flowdoc import flow, step

@flow(name="Order Processing")
class OrderProcessor:
    @step(name="Receive Order")
    def receive_order(self, order_data):
        return self.validate_payment(order_data)
```

**Best for**: Object-oriented codebases, state management, complex business logic

**Examples**: [ecommerce_order.py](ecommerce_order.py), [user_authentication.py](user_authentication.py)

### Function-Based Flows

Use `@step` decorator on standalone functions (no `@flow` needed):

```python
from flowdoc import step

@step(name="Process Order")
def process_order(order_data):
    validated = validate_order(order_data)
    return charge_payment(validated)
```

**Best for**: Functional programming, simple pipelines, web framework integration

**Examples**: [data_import.py](data_import.py), [fastapi/app.py](fastapi/app.py)

### Web Framework Integration

Stack `@step` with framework decorators:

```python
from fastapi import FastAPI
from flowdoc import step

app = FastAPI()

@app.post("/orders")
@step(name="Create Order")
async def create_order(order: OrderData):
    # business logic
```

**Best for**: API endpoints, web applications, microservices

**Examples**: [fastapi/app.py](fastapi/app.py)

## Adding Your Own Example

1. Create a `.py` file with realistic business logic
2. Add decorators (`@flow` and/or `@step`)
3. Generate diagrams to verify the flow
4. Update this README with your example

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.
