from flowdoc import step


@step(name="Process Payment")
def process_payment(order: dict):
    """Process the payment for an order."""
    if order.get("total", 0) > 1000:
        return flag_for_review(order)
    return confirm_payment(order)


@step(name="Flag for Review")
def flag_for_review(order: dict):
    """Flag high-value orders for manual review."""
    pass


@step(name="Confirm Payment")
def confirm_payment(order: dict):
    """Confirm the payment was successful."""
    pass
