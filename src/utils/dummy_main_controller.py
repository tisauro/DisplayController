import asyncio
from typing import AsyncGenerator, Any, Sequence, Tuple
import logging

from languages.message_types import AllMessageTypes, TextMessage, BackgroundColourMessage, CodeLanguageMessage, SettingsMessage

logger = logging.getLogger(__name__)


class MessageFactory:
    @staticmethod
    def create_message_class(json_message: dict[str, Any]) -> AllMessageTypes:
        if "text" in json_message:
            text_data = json_message["text"]
            if isinstance(text_data, (list, tuple)):
                return TextMessage(text=tuple(str(item) for item in text_data))
            return TextMessage(text=(str(text_data),))

        if "background_colour" in json_message:
            bg_data = json_message["background_colour"]
            if isinstance(bg_data, (list, tuple)) and len(bg_data) == 3:
                return BackgroundColourMessage(colour=(int(bg_data[0]), int(bg_data[1]), int(bg_data[2])))
            # Fallback or handling for string colors like "white" if needed, 
            # though the dataclass expects a tuple. 
            # Given dummy_main_controller uses strings, we might need to map them.
            color_map = {
                "white": (255, 255, 255),
                "red": (255, 0, 0),
                "green": (0, 255, 0),
                "blue": (0, 0, 255),
            }
            if isinstance(bg_data, str) and bg_data in color_map:
                return BackgroundColourMessage(colour=color_map[bg_data])
            return BackgroundColourMessage(colour=(0, 0, 0))

        if "code_language" in json_message:
            code = str(json_message["code_language"])
            params = json_message.get("parameters", [])
            if isinstance(params, (list, tuple)):
                return CodeLanguageMessage(
                    code_language=code,
                    parameters=tuple(str(p) for p in params)
                )
            return CodeLanguageMessage(code_language=code)

        if "settings" in json_message:
            return SettingsMessage(settings=str(json_message["settings"]))

        return TextMessage(text=("Command Not Found",))


class DummyMainController:
    def __init__(self, messages: Sequence[dict[str, Any]]):
        # Store the provided messages and basic state
        self._messages: Sequence[dict[str, Any]] = messages
        self._count: int = len(self._messages)
        self._current_index: int = 0
        self._colours = ["white", "red", "green", "blue"]
        self._current_colour: int = 0
        self._message_queue: asyncio.Queue[AllMessageTypes] = asyncio.Queue()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def send_message(self) -> AsyncGenerator[AllMessageTypes, None]:
        while True:
            message = await self._message_queue.get()
            yield message

    async def listen_direction(self, buttons_events: AsyncGenerator) -> None:
        # If there are no messages, nothing to send – just consume events safely
        if self._count == 0:
            async for _ in buttons_events:
                pass
            return

        async for event in buttons_events:
            if event.type == "button_01":
                logger.debug(f"Button 01 clicked: {event.button_id}")
                self._current_index += 1
                if self._current_index >= self._count:
                    self._current_index = 0
                msg = self._messages[self._current_index]
                logger.debug(f"Controller Sending message: {msg}")
                cmd = MessageFactory().create_message_class(msg)
                await self._message_queue.put(cmd)
            elif event.type == "button_02":
                logger.debug(f"Button 02: {event.button_id}")
                self._current_index -= 1
                if self._current_index < 0:
                    self._current_index = self._count - 1
                msg = self._messages[self._current_index]
                logger.debug(f"Controller Sending message: {msg}")
                cmd = MessageFactory().create_message_class(msg)
                await self._message_queue.put(cmd)
            elif event.type == "button_01_held":
                logger.debug(f"Button 01 held: {event.button_id}")
                self._current_colour += 1
                if self._current_colour >= len(self._colours):
                    self._current_colour = 0
                msg = {"background_colour": self._colours[self._current_colour]}
                cmd = MessageFactory().create_message_class(msg)
                await self._message_queue.put(cmd)
            elif event.type == "button_02_held":
                logger.debug(f"Button 02 held: {event.button_id}")
                self._current_colour -= 1
                if self._current_colour < 0:
                    self._current_colour = len(self._colours) - 1
                msg = {"background_colour": self._colours[self._current_colour]}
                cmd = MessageFactory().create_message_class(msg)
                await self._message_queue.put(cmd)
            elif event.type == "double_button":
                logger.debug("Double button clicked")
                self._current_index = 0
                msg = self._messages[self._current_index]
                cmd = MessageFactory().create_message_class(msg)
                await self._message_queue.put(cmd)
            else:
                logger.warning(f"Unknown event type: {event.type}")
