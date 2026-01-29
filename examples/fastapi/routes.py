"""FastAPI routes for the Product Inventory API.

Thin routing layer that delegates business logic to ProductService.
This file shows how FlowDoc decorators coexist with framework decorators.

The business flow diagram is generated from service.py, where the
decision logic lives. This file wires HTTP concerns (status codes,
response models) to the service layer.

Usage:
    uvicorn examples.fastapi.routes:app --reload
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from examples.fastapi.models import CreateProductRequest, UpdateProductRequest
from examples.fastapi.service import ProductService

# FastAPI app setup (import guarded so the file parses without fastapi installed)
try:
    from fastapi import FastAPI, HTTPException, Query
except ImportError:
    raise SystemExit(
        "FastAPI is required to run this example: pip install fastapi uvicorn"
    )

app = FastAPI(
    title="Product Inventory API",
    description="CRUD API for product catalog management — powered by FlowDoc",
    version="1.0.0",
)

service = ProductService()


# ── CREATE ───────────────────────────────────────────────────────────


@app.post("/products", status_code=201)
async def create_product(request: CreateProductRequest) -> dict[str, Any]:
    """Create a new product in the catalog.

    Validates data, checks for duplicate SKU, persists, and publishes
    a catalog-update event.
    """
    result = service.create_product(asdict(request))

    if result["status"] == "invalid":
        raise HTTPException(status_code=422, detail=result["errors"])
    if result["status"] == "conflict":
        raise HTTPException(status_code=409, detail=result["error"])

    return result


# ── READ ─────────────────────────────────────────────────────────────


@app.get("/products/{product_id}")
async def get_product(product_id: str) -> dict[str, Any]:
    """Retrieve a single product by its ID.

    Returns 404 if the product does not exist or is inactive.
    """
    result = service.get_product(product_id)

    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    return result


@app.get("/products")
async def list_products(
    category: str | None = Query(default=None, description="Filter by category"),
    active_only: bool = Query(default=True, description="Exclude inactive products"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Page size"),
) -> dict[str, Any]:
    """List products with optional filtering and pagination.

    This endpoint does not use FlowDoc steps because the logic is a
    straightforward database query with no branching business rules.
    """
    # Placeholder — in production this would query the database
    return {
        "status": "ok",
        "filters": {"category": category, "active_only": active_only},
        "pagination": {"offset": offset, "limit": limit},
        "products": [],
    }


# ── UPDATE ───────────────────────────────────────────────────────────


@app.put("/products/{product_id}")
async def update_product(
    product_id: str,
    request: UpdateProductRequest,
) -> dict[str, Any]:
    """Update an existing product.

    Checks authorization, validates the update payload, applies changes,
    and publishes a catalog-update event.
    """
    updates = {k: v for k, v in asdict(request).items() if v is not None}
    # In a real app the authorization flag comes from an auth middleware
    updates["authorized"] = True

    result = service.update_product(product_id, updates)

    if result["status"] == "forbidden":
        raise HTTPException(status_code=403, detail="Not authorized to update this product")
    if result["status"] == "invalid":
        raise HTTPException(status_code=422, detail=result["errors"])

    return result


# ── DELETE ───────────────────────────────────────────────────────────


@app.delete("/products/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    hard: bool = Query(default=False, description="Permanently remove instead of soft-delete"),
) -> None:
    """Delete a product from the catalog.

    Checks for active order references. If orders exist the product is
    soft-deleted (deactivated) regardless of the ``hard`` flag. Otherwise
    the caller controls whether the removal is soft or hard.
    """
    result = service.delete_product(product_id, hard=hard)

    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
