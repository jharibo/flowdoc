"""Pydantic models for the Product Inventory API.

These are shared between routes and service layers.
"""

from dataclasses import dataclass


@dataclass
class Product:
    """Product entity."""

    id: str
    name: str
    sku: str
    price: float
    stock: int
    category: str
    is_active: bool = True


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
    is_active: bool | None = None
