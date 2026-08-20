class EntityNotFoundException(Exception):
    def __init__(self, message: str = "Entity not found"):
        self.message = message
        super().__init__(self.message)

class RateLimitException(Exception):
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)

class IngestionException(Exception):
    def __init__(self, message: str = "Failed to process and ingest document"):
        self.message = message
        super().__init__(self.message)
