from flowdoc import step


@step(name="Check Inventory")
def check_inventory(order: dict):
    """Check if all items are in stock."""
    return verify_address(order)


@step(name="Verify Address")
def verify_address(order: dict):
    """Verify the shipping address is valid."""
    pass
