from abc import ABC, abstractmethod


class BaseDisplay(ABC):
    @abstractmethod
    def set_rgb(self, r: int, g: int, b: int):
        raise NotImplementedError()

    def set_color_white(self):
        self.set_rgb(255, 255, 255)

    @abstractmethod
    def display_clear(self):
        raise NotImplementedError()

    @abstractmethod
    def display_on(self):
        raise NotImplementedError()

    @abstractmethod
    def display_off(self):
        raise NotImplementedError()

    @abstractmethod
    def print_lines(self, line_1, line_2):
        raise NotImplementedError()

    @abstractmethod
    def has_timeout(self):
        raise NotImplementedError()
