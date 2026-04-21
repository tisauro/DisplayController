from abc import ABC, abstractmethod


class BaseDisplay(ABC):
    @abstractmethod
    def set_rgb(self, r: int, g: int, b: int) -> None:
        ...

    def set_color_white(self):
        self.set_rgb(255, 255, 255)

    @abstractmethod
    def display_clear(self) -> None:
        ...

    @abstractmethod
    def display_on(self) -> None:
        ...

    @abstractmethod
    def display_off(self) -> None:
        ...

    @abstractmethod
    def print_lines(self, line_1: str, line_2: str) -> None:
        ...

    @abstractmethod
    def has_timeout(self) -> bool:
        ...
