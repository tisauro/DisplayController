import asyncio
from pathlib import Path

from src.language.translator import Translator
from src.buttons.async_pi_buttons import AsyncPiButtons
from src.display_controller import DisplayController
from src.utils.messages import dispatch_messages


async def main():
    async with AsyncPiButtons() as pi_buttons:
        print(pi_buttons)
        # screen_buttons = DisplayController()

        languages = Translator()
        languages.load_languages(path=Path(".."))
        languages.verify_templates()
        languages.set_current_language("english")

        display = DisplayController()
        await display.run(languages.translate(dispatch_messages()), pi_buttons)


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    asyncio.run(main())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
