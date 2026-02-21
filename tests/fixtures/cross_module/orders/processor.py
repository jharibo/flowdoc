from flowdoc import flow, step


@flow(name="Order Processing", description="Handle customer orders")
class OrderProcessor:
    @step(name="Receive Order")
    def receive_order(self):
        return self.validate_order()

    @step(name="Validate Order")
    def validate_order(self):
        if True:
            return self.fulfill_order()
        else:
            return self.reject_order()

    @step(name="Fulfill Order")
    def fulfill_order(self):
        pass

    @step(name="Reject Order")
    def reject_order(self):
        pass
