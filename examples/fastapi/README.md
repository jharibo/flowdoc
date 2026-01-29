# FastAPI Example — Product Inventory API

This example demonstrates `@step` decorators applied **directly to FastAPI
endpoint functions**.  FlowDoc discovers the business flow by analysing which
`@step`-decorated functions call other `@step`-decorated functions — no
separate service layer or `@flow` class required.

## Key Pattern

```python
@app.post("/products", status_code=201)
@step(name="Create Product", description="Validate, de-duplicate, and persist a new product")
async def create_product(request: CreateProductRequest) -> dict:
    result = validate_product_data(asdict(request))
    ...
```

Stack the FastAPI route decorator and `@step` on the same function.  Helper
functions like `validate_product_data` also carry `@step` so FlowDoc can trace
the full business flow from endpoint to leaf.

## Endpoints

| Method   | Path                | Description                     |
|----------|---------------------|---------------------------------|
| `POST`   | `/products`         | Create a new product            |
| `GET`    | `/products/{id}`    | Retrieve a single product       |
| `PUT`    | `/products/{id}`    | Update an existing product      |
| `DELETE` | `/products/{id}`    | Soft- or hard-delete a product  |

## Business Flow Diagram

Generated with `flowdoc generate examples/fastapi/app.py --format mermaid`

```mermaid
flowchart TD
    validate_product_data([Validate Product Data])
    check_duplicate_sku([Check Duplicate SKU])
    save_product[Save Product]
    notify_catalog_update([Notify Catalog Update])
    lookup_product([Lookup Product])
    apply_update[Apply Update]
    check_order_references([Check Order References])
    soft_delete[Soft Delete]
    hard_delete[Hard Delete]
    create_product{Create Product}
    get_product[Get Product]
    update_product{Update Product}
    delete_product{Delete Product}

    save_product --> notify_catalog_update
    apply_update --> notify_catalog_update
    soft_delete --> notify_catalog_update
    hard_delete --> notify_catalog_update
    create_product --> validate_product_data
    create_product --> check_duplicate_sku
    create_product --> save_product
    get_product --> lookup_product
    update_product --> lookup_product
    update_product --> validate_product_data
    update_product --> apply_update
    delete_product --> lookup_product
    delete_product --> check_order_references
    delete_product -->|yes| soft_delete
    delete_product -->|yes| hard_delete
    delete_product -->|no| soft_delete
```

## Generating Diagrams

```bash
# Mermaid (renders on GitHub)
flowdoc generate examples/fastapi/app.py --format mermaid

# Graphviz DOT source
flowdoc generate examples/fastapi/app.py --format dot

# PNG (requires graphviz system package)
flowdoc generate examples/fastapi/app.py --format png

# Validate flow
flowdoc validate examples/fastapi/app.py
```
