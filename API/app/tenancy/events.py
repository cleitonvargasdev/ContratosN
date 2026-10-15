from app.tenancy.context import tenant_key


class TenantEventBroker:
    """One in-memory broker per tenant, including overlapping user IDs."""

    def __init__(self, factory):
        self.factory = factory
        self.brokers = {}

    def __getattr__(self, name):
        key = tenant_key()
        if key not in self.brokers:
            self.brokers[key] = self.factory()
        return getattr(self.brokers[key], name)
