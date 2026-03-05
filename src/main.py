import asyncio
from pathlib import Path

from languages.translator import Translator
from buttons.async_pi_buttons import AsyncPiButtons
from display_controller import DisplayController
from utils.messages import messages_template
from utils.dummy_main_controller import DummyMainController
from display.lcd_1602_display import LCD1602Display


async def main():
    async with (
        AsyncPiButtons() as pi_buttons,
        Translator(files_path=Path("languages")) as translator,
        DummyMainController(messages_template) as dummy_controller,
        LCD1602Display() as lcd_1602_display,
        DisplayController() as display_controller,
    ):
        # Wire up the data flow:
        # 1. Buttons -> DisplayController -> DummyController
        # 2. DummyController -> Translator -> DisplayController -> LCD Display

        await asyncio.gather(
            # display_controller listens to button events and process them
            display_controller.listen_direction(pi_buttons),
            # Listen to app messages, translate them, and send to display
            display_controller.listen_messages(
                translator.translate(dummy_controller.send_message())
            ),
            # display_controller sends display messages to LCD hardware
            lcd_1602_display.receive_messages(
                display_controller.send_message_to_display()
            ),
            # Process button events in the dummy controller
            dummy_controller.listen_direction(
                display_controller.send_direction_to_controller()
            ),
        )


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    asyncio.run(main())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
