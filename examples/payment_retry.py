"""Payment retry flow example.

Demonstrates try/except branching where business decisions are expressed
through exception handling: successful charges follow the happy path,
payment declines trigger failure notifications, and network errors
trigger a retry.
"""

from flowdoc import flow, step


class PaymentError(Exception):
    pass


class NetworkError(Exception):
    pass


@flow(name="Payment Retry", description="Charge a payment with retry on network failure")
class PaymentFlow:
    @step(name="Process Payment", description="Attempt to charge the customer")
    def process_payment(self, order: dict) -> dict:
        try:
            return self.charge_card(order)
        except PaymentError:
            return self.send_failure_email(order)
        except NetworkError:
            return self.retry_later(order)
        finally:
            self.log_attempt(order)

    @step(name="Charge Card", description="Submit charge to payment gateway")
    def charge_card(self, order: dict) -> dict:
        return {"status": "charged", "order_id": order["id"]}

    @step(name="Send Failure Email", description="Notify customer of payment decline")
    def send_failure_email(self, order: dict) -> dict:
        return {"status": "declined", "order_id": order["id"]}

    @step(name="Retry Later", description="Schedule retry after network error")
    def retry_later(self, order: dict) -> dict:
        return {"status": "retry_scheduled", "order_id": order["id"]}

    @step(name="Log Attempt", description="Record the payment attempt for audit")
    def log_attempt(self, order: dict) -> None:
        pass
