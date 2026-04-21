from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TextMessage:
    text: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BackgroundColourMessage:
    colour: tuple[int, int, int]

@dataclass(frozen=True, slots=True)
class SettingsMessage:
    settings: str


@dataclass(frozen=True, slots=True)
class CodeLanguageMessage:
    code_language: str
    parameters: tuple[str, ...] = field(default_factory=tuple)


type AllMessageTypes = TextMessage | BackgroundColourMessage | CodeLanguageMessage | SettingsMessage

