"""FastAPI Product Inventory API with FlowDoc decorators on endpoints.

Demonstrates how ``@step`` works directly alongside FastAPI's route
decorators.  FlowDoc discovers the business flow by analysing which
``@step``-decorated functions call other ``@step``-decorated functions.

Usage:
    uvicorn examples.fastapi.app:app --reload

Generate diagrams:
    flowdoc generate examples/fastapi/app.py --format png
    flowdoc generate examples/fastapi/app.py --format mermaid
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from flowdoc import step

try:
    from fastapi import FastAPI, HTTPException, Query
except ImportError as exc:
    raise SystemExit(
        "FastAPI is required to run this example: pip install fastapi uvicorn"
    ) from exc

app = FastAPI(
    title="Product Inventory API",
    description="CRUD API for product catalog management — powered by FlowDoc",
    version="1.0.0",
)


# ── Models ──────────────────────────────────────────────────────────


@dataclass
class CreateProductRequest:
    """Request payload for creating a product."""

    name: str
    sku: str
    price: float
    stock: int
    category: str


@dataclass
class UpdateProductRequest:
    """Request payload for updating a product."""

    name: str | None = None
    price: float | None = None
    stock: int | None = None
    category: str | None = None


# ── Helper steps ────────────────────────────────────────────────────


@step(name="Validate Product Data", description="Check required fields and value ranges")
def validate_product_data(data: dict) -> dict:
    errors: list[str] = []
    if not data.get("name"):
        errors.append("name is required")
    if not data.get("sku"):
        errors.append("sku is required")
    if data.get("price", 0) <= 0:
        errors.append("price must be positive")
    return {"valid": len(errors) == 0, "errors": errors, "data": data}


@step(name="Check Duplicate SKU", description="Ensure SKU is unique in catalog")
def check_duplicate_sku(sku: str) -> bool:
    # Placeholder — would query the database in production
    return False


@step(name="Save Product", description="Persist new product to the database")
def save_product(data: dict) -> dict:
    return notify_catalog_update({"id": "prod_123", **data})


@step(name="Notify Catalog Update", description="Publish event for downstream systems")
def notify_catalog_update(product: dict) -> dict:
    # Placeholder — would publish to an event bus in production
    return product


@step(name="Lookup Product", description="Query database for a product by ID")
def lookup_product(product_id: str) -> dict | None:
    # Placeholder — would query the database in production
    return None


@step(name="Apply Update", description="Merge changes and persist to database")
def apply_update(product_id: str, updates: dict) -> dict:
    return notify_catalog_update({"id": product_id, **updates})


@step(name="Check Order References", description="Look for active orders referencing this product")
def check_order_references(product_id: str) -> bool:
    # Placeholder — would query the orders table in production
    return False


@step(name="Soft Delete", description="Mark product as inactive")
def soft_delete(product_id: str) -> dict:
    return notify_catalog_update({"id": product_id, "action": "deactivated"})


@step(name="Hard Delete", description="Permanently remove product from database")
def hard_delete(product_id: str) -> dict:
    return notify_catalog_update({"id": product_id, "action": "deleted"})


# ── Endpoints ───────────────────────────────────────────────────────


@app.post("/products", status_code=201)
@step(name="Create Product", description="Validate, de-duplicate, and persist a new product")
async def create_product(request: CreateProductRequest) -> dict:
    result = validate_product_data(asdict(request))
    if not result["valid"]:
        raise HTTPException(status_code=422, detail=result["errors"])

    is_duplicate = check_duplicate_sku(request.sku)
    if is_duplicate:
        raise HTTPException(status_code=409, detail="SKU already exists")

    product = save_product(result["data"])
    return {"status": "created", "product": product}


@app.get("/products/{product_id}")
@step(name="Get Product", description="Retrieve a single product by ID")
async def get_product(product_id: str) -> dict:
    product = lookup_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "ok", "product": product}


@app.put("/products/{product_id}")
@step(name="Update Product", description="Validate and apply changes to an existing product")
async def update_product(product_id: str, request: UpdateProductRequest) -> dict:
    existing = lookup_product(product_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Product not found")

    updates = {k: v for k, v in asdict(request).items() if v is not None}
    result = validate_product_data({**existing, **updates})
    if not result["valid"]:
        raise HTTPException(status_code=422, detail=result["errors"])

    product = apply_update(product_id, updates)
    return {"status": "updated", "product": product}


@app.delete("/products/{product_id}", status_code=204)
@step(name="Delete Product", description="Soft- or hard-delete depending on order references")
async def delete_product(
    product_id: str,
    hard: bool = Query(default=False, description="Permanently remove instead of soft-delete"),
) -> None:
    existing = lookup_product(product_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Product not found")

    has_orders = check_order_references(product_id)
    if has_orders:
        soft_delete(product_id)
    else:
        if hard:
            hard_delete(product_id)
        else:
            soft_delete(product_id)
