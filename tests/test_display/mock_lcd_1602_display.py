from display.base_display import BaseDisplay


class MockLCD1602Display(BaseDisplay):
    def __init__(self):
        self.initialized = False
        self.cleanup = False

    async def __aenter__(self):
        self.initialized = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.cleanup = True
