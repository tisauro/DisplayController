from pathlib import Path
from string import Template
from typing import AsyncGenerator


class Translator:
    def __init__(self):
        self._languages = {}
        self.verify_templates()
        self._current_language: str = "english"
        self._language_path: Path = Path(__file__)

    def reload(self):
        self.load_languages(self._language_path)

    def load_languages(self, path: Path) -> None:
        self._languages = {}
        self._language_path = path
        for file_path in path.glob("**/language_*.py"):
            language_name = file_path.stem.split("_")[1]
            attr = f"_{language_name}_str"
            file_vars = {}
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read(), {}, file_vars)

            if attr in file_vars:
                self._languages[language_name] = file_vars[attr]

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
    def _convert_parameters(parameters: list) -> dict[str, str]:
        return {
            par.split(sep="=")[0]: par.split(sep="=")[1]
            for par in parameters
            if "=" in par
        }

    def get_text(self, code_language: str, parameters: list = ()) -> list:
        self.reload()
        raw_text = self._languages[self.get_current_language()].get(
            code_language, code_language
        )
        if isinstance(raw_text, str):
            raw_text = [raw_text]

        final_text = []
        dict_par = self._convert_parameters(parameters)
        for line in raw_text:
            string_template = Template(line)
            temp = string_template.safe_substitute(dict_par)
            # create multiple lines from a single parameter if it contains '\n'
            temp = temp.split(sep="\n")
            final_text.extend(temp)
        return final_text

    async def translate(self, messages: AsyncGenerator):
        async for message in messages:
            if "code_language" in message:
                yield {
                    "text": self.get_text(
                        message["code_language"], message.get("parameters", "")
                    )
                }
            else:
                yield message


if __name__ == "__main__":
    from src.utils.messages import dispatch_messages

    languages = Translator()
    languages.load_languages(path=Path("../.."))
    languages.verify_templates()
    languages.set_current_language("english")

    async def main():
        async for message in languages.translate(dispatch_messages()):
            print(message)

    from asyncio import run

    run(main())
