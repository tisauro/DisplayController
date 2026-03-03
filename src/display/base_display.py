class BaseDisplay:
    def set_rgb(self, r: int, g: int, b: int):
        raise NotImplementedError()

    def set_color_white(self):
        self.set_rgb(255, 255, 255)

    def display_clear(self):
        raise NotImplementedError()

    def display_on(self):
        raise NotImplementedError()

    def display_off(self):
        raise NotImplementedError()

    def print_lines(self, line_1, line_2):
        raise NotImplementedError()

    def has_timeout(self):
        raise NotImplementedError()
