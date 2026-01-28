# FlowDoc

Generate business flow diagrams from Python code decorators.

## Installation

```bash
pip install flowdoc
```

## Quick Start

```python
from flowdoc import flow, step

@flow(name="Order Processing", description="Handle customer orders")
class OrderProcessor:
    @step(name="Receive Order")
    def receive_order(self, order_data):
        return self.validate_payment(order)

    @step(name="Validate Payment")
    def validate_payment(self, order):
        if payment_valid:
            return self.fulfill_order(order)
        else:
            return self.send_failure_email(order)
```

Generate diagram:

```bash
flowdoc generate order_processor.py
```

## Status

This project is in active development.
