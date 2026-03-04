import asyncio
from pathlib import Path

from languages.translator import Translator
from buttons.async_pi_buttons import AsyncPiButtons
from display_controller import DisplayController
from utils.messages import messages_template
from utils.dummy_main_controller import DummyMainController


async def main():
    async with (
        AsyncPiButtons() as pi_buttons,
        Translator(files_path=Path("..")) as translator,
        DummyMainController(messages_template) as dummy_controller,
    ):
        display_controller = DisplayController()

        translator.translate(dummy_controller.send_message())
        dummy_controller.run(display_controller.push_direction)

        await display_controller.run(pi_buttons.listen_direction)


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    asyncio.run(main())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
