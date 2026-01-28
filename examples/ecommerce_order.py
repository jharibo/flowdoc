"""E-commerce order processing flow example.

Demonstrates class-based flows with branching (payment valid/invalid)
and terminal steps (confirmation/failure email).
"""

from flowdoc import flow, step


@flow(name="Order Processing", description="Handle customer orders end-to-end")
class OrderProcessor:
    @step(name="Receive Order", description="Accept incoming order from customer")
    def receive_order(self, order_data: dict) -> dict:
        return self.validate_payment(order_data)

    @step(name="Validate Payment", description="Check payment method and funds")
    def validate_payment(self, order: dict) -> dict:
        if order.get("payment_valid"):
            return self.fulfill_order(order)
        else:
            return self.send_failure_email(order)

    @step(name="Fulfill Order", description="Package and ship the order")
    def fulfill_order(self, order: dict) -> dict:
        return self.send_confirmation(order)

    @step(name="Send Confirmation", description="Email order confirmation to customer")
    def send_confirmation(self, order: dict) -> dict:
        return {"status": "confirmed", "order": order}

    @step(name="Send Failure Email", description="Notify customer of payment failure")
    def send_failure_email(self, order: dict) -> dict:
        return {"status": "failed", "order": order}
