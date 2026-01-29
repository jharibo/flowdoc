"""Product inventory service with business flow logic.

Demonstrates FlowDoc with a realistic CRUD service layer where business
decisions (validation, authorization, conflict detection) are captured
as flow steps. The routes layer (routes.py) delegates to this service.

Run:
    flowdoc generate examples/fastapi/service.py --format png
    flowdoc generate examples/fastapi/service.py --format mermaid
"""

from flowdoc import flow, step


@flow(
    name="Product Inventory API",
    description="CRUD operations for product catalog management",
)
class ProductService:
    """Service encapsulating all product business logic.

    Each public method corresponds to a CRUD endpoint. Internal steps
    handle validation, authorization, conflict detection, and persistence.
    """

    # ── CREATE ───────────────────────────────────────────────────────

    @step(name="Create Product", description="Entry point for product creation")
    def create_product(self, data: dict) -> dict:
        return self.validate_product_data(data)

    @step(name="Validate Product Data", description="Check required fields and value ranges")
    def validate_product_data(self, data: dict) -> dict:
        if data.get("name") and data.get("sku") and data.get("price", 0) > 0:
            return self.check_duplicate_sku(data)
        else:
            return self.reject_invalid(data)

    @step(name="Check Duplicate SKU", description="Ensure SKU is unique in catalog")
    def check_duplicate_sku(self, data: dict) -> dict:
        existing = None  # db lookup placeholder
        if existing:
            return self.reject_duplicate(data)
        else:
            return self.persist_product(data)

    @step(name="Persist Product", description="Save new product to the database")
    def persist_product(self, data: dict) -> dict:
        return self.notify_catalog_update(data)

    @step(name="Notify Catalog Update", description="Publish event for downstream systems")
    def notify_catalog_update(self, data: dict) -> dict:
        return {"status": "created", "product": data}

    @step(name="Reject Invalid", description="Return validation errors to caller")
    def reject_invalid(self, data: dict) -> dict:
        return {"status": "invalid", "errors": ["Missing required fields"]}

    @step(name="Reject Duplicate", description="Return conflict error for existing SKU")
    def reject_duplicate(self, data: dict) -> dict:
        return {"status": "conflict", "error": "SKU already exists"}

    # ── READ ─────────────────────────────────────────────────────────

    @step(name="Get Product", description="Retrieve a single product by ID")
    def get_product(self, product_id: str) -> dict:
        return self.lookup_product(product_id)

    @step(name="Lookup Product", description="Query database for the product")
    def lookup_product(self, product_id: str) -> dict:
        product = None  # db lookup placeholder
        if product:
            return self.check_product_visibility(product)
        else:
            return self.handle_not_found(product_id)

    @step(name="Check Product Visibility", description="Filter out inactive products for non-admin users")
    def check_product_visibility(self, product: dict) -> dict:
        if product.get("is_active"):
            return self.format_product_response(product)
        else:
            return self.handle_not_found(product.get("id", ""))

    @step(name="Format Product Response", description="Shape product data for API response")
    def format_product_response(self, product: dict) -> dict:
        return {"status": "ok", "product": product}

    @step(name="Handle Not Found", description="Return 404 response")
    def handle_not_found(self, product_id: str) -> dict:
        return {"status": "not_found", "id": product_id}

    # ── UPDATE ───────────────────────────────────────────────────────

    @step(name="Update Product", description="Entry point for product updates")
    def update_product(self, product_id: str, updates: dict) -> dict:
        return self.authorize_update(product_id, updates)

    @step(name="Authorize Update", description="Verify caller has permission to modify product")
    def authorize_update(self, product_id: str, updates: dict) -> dict:
        has_permission = updates.get("authorized", False)
        if has_permission:
            return self.validate_update_fields(product_id, updates)
        else:
            return self.reject_unauthorized(product_id)

    @step(name="Validate Update Fields", description="Check update payload for valid values")
    def validate_update_fields(self, product_id: str, updates: dict) -> dict:
        if updates.get("price", 1) > 0:
            return self.apply_update(product_id, updates)
        else:
            return self.reject_invalid_update(updates)

    @step(name="Apply Update", description="Merge changes and persist to database")
    def apply_update(self, product_id: str, updates: dict) -> dict:
        return self.notify_catalog_update({"id": product_id, **updates})

    @step(name="Reject Unauthorized", description="Return 403 forbidden response")
    def reject_unauthorized(self, product_id: str) -> dict:
        return {"status": "forbidden", "id": product_id}

    @step(name="Reject Invalid Update", description="Return validation errors for update")
    def reject_invalid_update(self, updates: dict) -> dict:
        return {"status": "invalid", "errors": ["Invalid update values"]}

    # ── DELETE ────────────────────────────────────────────────────────

    @step(name="Delete Product", description="Entry point for product removal")
    def delete_product(self, product_id: str, hard: bool = False) -> dict:
        return self.check_order_references(product_id, hard)

    @step(name="Check Order References", description="Look for active orders referencing this product")
    def check_order_references(self, product_id: str, hard: bool) -> dict:
        has_active_orders = False  # db lookup placeholder
        if has_active_orders:
            return self.soft_delete_product(product_id)
        else:
            if hard:
                return self.hard_delete_product(product_id)
            else:
                return self.soft_delete_product(product_id)

    @step(name="Soft Delete Product", description="Mark product as inactive, keep data")
    def soft_delete_product(self, product_id: str) -> dict:
        return self.notify_catalog_update({"id": product_id, "action": "deactivated"})

    @step(name="Hard Delete Product", description="Permanently remove product from database")
    def hard_delete_product(self, product_id: str) -> dict:
        return self.notify_catalog_update({"id": product_id, "action": "deleted"})
