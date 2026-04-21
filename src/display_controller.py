import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, AsyncGenerator, Any, Optional, AsyncIterator

from languages.message_types import AllMessageTypes, BackgroundColourMessage, SettingsMessage, TextMessage

log = logging.getLogger(__name__)

TIMEOUT_MINUTES = 2
IDLE_TIME = 3


@dataclass
class ButtonEvent:
    type: str
    button_id: Optional[int] = None


class DisplayController:
    """
    Manages the interaction with the display hardware, including managing display
    timeouts, text display, and background color settings.

    The `DisplayController` class provides functionality to control a display
    screen, handle text message updates, and manage user interactions through
    physical buttons. It aims to provide robust control mechanisms, including
    handling screen timeouts and ensuring efficient display updates.

    :ivar lines: List of text lines currently displayed on the screen.
    :type lines: list
    :ivar cursor_position: Index representing the current display position
        when scrolling through text.
    :type cursor_position: int
    """

    def __init__(self):
        self._lines = []
        self._cursor_position = 0

        # Display timeout
        self._start_timer_tick = datetime.now(UTC).timestamp()
        self._display_off = False
        self._disable_screen_timeout = False
        self._timeout_minutes = TIMEOUT_MINUTES
        self._last_payload = {"text": ["Display", "Initialized"]}
        self._last_background_colour = None
        self._task_display_timeout: asyncio.Task[None] | None = None
        self._display_queue = asyncio.Queue[dict[str, Any]]()
        self._direction_queue = asyncio.Queue[ButtonEvent]()

    async def __aenter__(self):
        self._task_display_timeout = asyncio.create_task(self._switch_display())
        self._show_text(self._last_payload, force_update=True)
        return self

    async def __aexit__(self, _exc_type, _exc_value, _traceback):
        if self._task_display_timeout and not self._task_display_timeout.done():
            self._task_display_timeout.cancel()
            try:
                await self._task_display_timeout
            except asyncio.CancelledError:
                pass

    async def send_message_to_display(self) -> AsyncGenerator:
        while True:
            message = await self._display_queue.get()
            await asyncio.sleep(0.1)
            yield message

    async def send_direction_to_controller(self) -> AsyncGenerator:
        while True:
            direction = await self._direction_queue.get()
            await asyncio.sleep(0.1)
            yield direction

    async def _switch_display(self):
        while True:
            if (
                    self._start_timer_tick
                    + timedelta(minutes=self._timeout_minutes).total_seconds()
                    < datetime.now(UTC).timestamp()
                    and not self._display_off
                    and not self._disable_screen_timeout
            ):
                log.debug("Display Off")
                message = SettingsMessage(settings= "display_off")
                self._process_event(message)
                self._display_off = True
            await asyncio.sleep(IDLE_TIME)

    def _set_settings(self, message: SettingsMessage):
        self._disable_screen_timeout = message.settings == "display_off"

        log.debug(f"Setting disable_screen_timeout to {self._disable_screen_timeout}")

    def _set_background_colour(self, message: BackgroundColourMessage):
        """
        Sets the background color based on the provided message. The background color will not change if the display
        is turned off or if the background color remains the same as the last applied color.

        :param message: A dictionary containing the background color information. It can include a key
            "background_colour" with either a list representing RGB values, or a string value such as "white".
        :type message: dict
        :return: None
        """
        bg_colour = message.colour

        # don't change background if display is off or
        # Avoid flickering if the background color is the same
        if self._display_off or self._last_background_colour == bg_colour:
            return

        msg = {"background_colour": tuple()}
        if isinstance(bg_colour, (list, tuple)):
            log.debug(f"Setting background colour to {message.colour}")
            msg = {"background_colour": tuple(bg_colour)}
        elif isinstance(bg_colour, str):
            log.debug("Setting background colour white")
            if bg_colour == "white":
                msg = {"background_colour": (255, 255, 255)}
            elif bg_colour == "red":
                msg = {"background_colour": (255, 0, 0)}
            elif bg_colour == "green":
                msg = {"background_colour": (0, 255, 0)}
            elif bg_colour == "blue":
                msg = {"background_colour": (0, 0, 255)}
            else:
                log.error(f"Invalid background colour: {bg_colour}")
                return
        self._last_background_colour = bg_colour
        self._display_queue.put_nowait(msg)

    def _show_text(self, payload, force_update: bool = False) -> None:
        if force_update or payload != self._last_payload:
            self._last_payload = payload
            text_lines = payload["text"]
            if isinstance(text_lines, list):
                self._cursor_position = 0
                send_lines = tuple(
                    text_lines[self._cursor_position: self._cursor_position + 2]
                )
                self._display_queue.put_nowait({"text": send_lines})
                self._lines = text_lines

    def _process_event(self, message: AllMessageTypes):
        try:
            if isinstance(message, BackgroundColourMessage):
                self._set_background_colour(message)
            elif isinstance(message, SettingsMessage):
                self._set_settings(message)
            elif isinstance(message, TextMessage):
                self._show_text(message.text)
            else:
                log.error(f"Unknown message: {message}")
        except Exception as e:
            log.error(f"Error processing event: {e}")

    async def listen_messages(self, messages: AsyncGenerator[AllMessageTypes, None]):
        try:
            async for message in messages:
                self._process_event(message)
        except Exception as e:
            log.info(f"Error processing event: {e}")

    async def listen_direction(self, buttons: AsyncIterator[str]):
        try:
            async for direction in buttons:
                # Ensure direction matches the Literal type expected by push_direction
                if direction in ["button_01", "button_02", "double_button"]:
                    msg = self.push_direction(direction)  # type: ignore
                    if msg != {}:
                        log.debug(f"Sending message: {msg}")
                        event = str(msg.get("button", "unknown"))
                        _id_str = event.split("_")[1] if "_" in event else None
                        _id = int(_id_str) if _id_str and _id_str.isdigit() else None
                        if msg.get("held"):
                            event += "_held"
                        self._direction_queue.put_nowait(
                            ButtonEvent(type=event, button_id=_id)
                        )
                elif direction in ["button_01_held", "button_02_held"]:
                    # Handle held events directly if they come from the iterator
                    btn_name = direction.replace("_held", "")
                    if btn_name in ["button_01", "button_02"]:
                        msg = self.push_direction(btn_name, held=True)  # type: ignore
                        if msg != {}:
                            log.debug(f"Sending message (held): {msg}")
                            event = str(msg.get("button", "unknown"))
                            _id_str = event.split("_")[1] if "_" in event else None
                            _id = (
                                int(_id_str) if _id_str and _id_str.isdigit() else None
                            )
                            if msg.get("held"):
                                event += "_held"
                            self._direction_queue.put_nowait(
                                ButtonEvent(type=event, button_id=_id)
                            )
                else:
                    log.warning(f"Unexpected direction value: {direction}")
        except Exception as e:
            log.info(f"Error processing event: {e}")

    def _update_display_text(self) -> None:
        """Updates the display with current lines at cursor position."""
        msg = {
            "text": (
                self._lines[self._cursor_position],
                self._lines[self._cursor_position + 1],
            )
        }
        self._display_queue.put_nowait(msg)

    def _handle_forward_direction(self) -> bool:
        """Handle forward direction. Returns True if display was updated."""
        if self._cursor_position + 3 == len(self._lines):
            self._cursor_position += 1
            self._update_display_text()
            return True
        elif self._cursor_position + 3 < len(self._lines):
            self._cursor_position += 2
            self._update_display_text()
            return True
        return False

    def _handle_backward_direction(self) -> bool:
        """Handle previous button press. Returns True if display was updated."""
        if self._cursor_position - 1 == 0:
            self._cursor_position = 0
            self._update_display_text()
            return True
        elif self._cursor_position - 2 >= 0:
            self._cursor_position -= 2
            self._update_display_text()
            return True
        return False

    def push_direction(
            self,
            button: Literal["button_01", "button_02", "double_button"],
            held: bool = False,
    ) -> dict[str, Any]:
        """
        Process button press and scroll display or wake it up if off.

        Returns message to send to topic, or empty dict if handled internally.
        """
        # Reset the timer on any button press
        self._start_timer_tick = datetime.now(UTC).timestamp()

        # Wake up display if off
        if self._display_off:
            msg = {"settings": "display_on"}
            self._display_queue.put_nowait(msg)
            self._display_off = False
            return {}

        # Scroll display on button press (if not held)
        if not held:
            try:
                if button == "button_01" and self._handle_forward_direction():
                    return {}
                elif button == "button_02" and self._handle_backward_direction():
                    return {}
            except Exception as e:
                log.error(f"Error processing button event: {e}")

        # Send message to topic if not handled above
        return {"button": button, "held": held}
