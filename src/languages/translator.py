import asyncio
import json
import logging
from pathlib import Path
from string import Template
from typing import AsyncGenerator, Tuple

from languages.message_types import TextMessage, AllMessageTypes, CodeLanguageMessage

log = logging.getLogger(__name__)


class Translator:
    """
    Handles language translation using dynamic templates. Provides functionality to load, reload,
    and translate text and messages in multiple languages. Uses JSON files to store language data.

    This class is designed to support asynchronous context management and dynamic language
    template substitution. It ensures that language templates are valid before usage.

    :ivar _current_language: The currently set language for translation operations.
    :type _current_language: str
    :ivar _language_path: The file path where language JSON files are located.
    :type _language_path: Path
    """

    def __init__(self, files_path: Path | None = None):
        self._languages = {}
        self.verify_templates()
        self._current_language: str = "english"
        if files_path is None:
            self._language_path: Path = Path(__file__)
        else:
            self._language_path = files_path

    async def __aenter__(self):
        self.load_languages(self._language_path)
        self.verify_templates()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def reload(self):
        self.load_languages(self._language_path)

    def load_languages(self, files_path: Path | None = None) -> None:
        self._languages = {}
        if files_path:
            self._language_path = files_path
        else:
            files_path = self._language_path
        for file_path in files_path.glob("**/language_*.json"):
            language_name = file_path.stem.split("_")[-1:][0]

            with open(file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            self._languages[language_name] = json_data

        self.verify_templates()

    def get_current_language(self):
        return self._current_language

    def set_current_language(self, language: str):
        self._current_language = language

    def verify_templates(self):
        for lang in list(self._languages.keys()):
            for key in list(self._languages[lang].keys()):
                line = self._languages[lang][key]
                if isinstance(line, str):
                    line = [line]
                for ln in line:
                    string_template = Template(ln)
                    if not string_template.is_valid():
                        # Todo: create custom exceptions for this class
                        raise Exception(ln)

    @staticmethod
    def _convert_parameters(parameters: Tuple[str, ...]) -> dict[str, str]:
        # Todo: what happens when parameters is None empty tuple?
        return {
            par.split(sep="=")[0]: par.split(sep="=")[1]
            for par in parameters
            if "=" in par
        }

    def get_text(self, code_message: CodeLanguageMessage) -> tuple[str, ...]:
        raw_text = self._languages[self.get_current_language()].get(
            code_message.code_language, code_message.code_language
        )
        if isinstance(raw_text, str):
            raw_text = [raw_text]

        final_text = []
        dict_par = self._convert_parameters(code_message.parameters)
        for line in raw_text:
            string_template = Template(line)
            temp = string_template.safe_substitute(dict_par)
            # create multiple lines from a single parameter if it contains '\n'
            temp = temp.split(sep="\n")
            final_text.extend(temp)
        return tuple(final_text)

    async def translate(self, messages: AsyncGenerator[AllMessageTypes, None]) -> AsyncGenerator[AllMessageTypes, None]:
        try:
            async for message in messages:
                try:
                    if isinstance(message, CodeLanguageMessage):
                        yield TextMessage(
                            text=self.get_text(message)
                        )
                    else:
                        yield message
                except Exception as e:
                    # Log per-message errors but continue processing
                    log.error(f"Error translating message {message}: {e}")

        except asyncio.CancelledError:
            # Allow clean cancellation
            log.info("Translation cancelled")
            raise
        except Exception as e:
            # Fatal error - log and re-raise
            log.exception(f"Fatal translator error: {e}")
            raise
