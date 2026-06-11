class CollectorRegistry:
    def __init__(self):
        self.topic = None
        self.service = None
        self.lifecycle = None
        self.graph = None

registry = CollectorRegistry()