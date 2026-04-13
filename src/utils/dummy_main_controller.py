import asyncio
from typing import AsyncGenerator, Any, Sequence
import logging

logger = logging.getLogger(__name__)


class DummyMainController:
    def __init__(self, messages: Sequence[dict[str, Any]]):
        # Store the provided messages and basic state
        self._messages: Sequence[dict[str, Any]] = messages
        self._count: int = len(self._messages)
        self._current_index: int = 0
        self._colours = ["white", "red", "green", "blue"]
        self._current_colour: int = 0
        self._message_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def send_message(self) -> AsyncGenerator[dict[str, Any], None]:
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
                await self._message_queue.put(msg)
            elif event.type == "button_02":
                logger.debug(f"Button 02: {event.button_id}")
                self._current_index -= 1
                if self._current_index < 0:
                    self._current_index = self._count - 1
                msg = self._messages[self._current_index]
                logger.debug(f"Controller Sending message: {msg}")
                await self._message_queue.put(msg)
            elif event.type == "button_01_held":
                logger.debug(f"Button 01 held: {event.button_id}")
                self._current_colour += 1
                if self._current_colour >= len(self._colours):
                    self._current_colour = 0
                await self._message_queue.put(
                    {"background_colour": self._colours[self._current_colour]}
                )
            elif event.type == "button_02_held":
                logger.debug(f"Button 02 held: {event.button_id}")
                self._current_colour -= 1
                if self._current_colour < 0:
                    self._current_colour = len(self._colours) - 1
                await self._message_queue.put(
                    {"background_colour": self._colours[self._current_colour]}
                )
            elif event.type == "double_button":
                logger.debug("Double button clicked")
                self._current_index = 0
                await self._message_queue.put(self._messages[self._current_index])
            else:
                logger.warning(f"Unknown event type: {event.type}")
