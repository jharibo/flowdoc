"""FastAPI app-factory pattern with FlowDoc decorators.

Demonstrates the ``@flow`` decorator on a factory function as a flow
boundary. FlowDoc discovers nested ``@step`` inner functions and treats
them as the flow's steps, which enables FastAPI's ``create_app()``
idiom where endpoints are registered inside a factory.

Usage:
    flowdoc generate examples/fastapi_factory.py --format png
"""

from __future__ import annotations

from flowdoc import flow, step

try:
    from fastapi import FastAPI
except ImportError as exc:
    raise SystemExit(
        "FastAPI is required to run this example: pip install fastapi uvicorn"
    ) from exc


@flow(name="Order API", description="Factory-constructed order endpoints")
def create_app() -> FastAPI:
    app = FastAPI(title="Order API")

    @app.post("/orders")
    @step(name="Create Order Endpoint", description="HTTP entry point for new orders")
    async def create_order(payload: dict) -> dict:
        validated = await validate_order(payload)
        return await save_order(validated)

    @step(name="Validate Order", description="Check required fields and pricing rules")
    async def validate_order(payload: dict) -> dict:
        if payload.get("total", 0) <= 0:
            return await reject_order(payload)
        return payload

    @step(name="Save Order", description="Persist the validated order")
    async def save_order(order: dict) -> dict:
        return {"status": "saved", "order": order}

    @step(name="Reject Order", description="Return validation failure to the client")
    async def reject_order(order: dict) -> dict:
        return {"status": "rejected", "order": order}

    return app
