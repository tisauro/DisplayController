import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Literal, AsyncGenerator, Any

log = logging.getLogger(__name__)


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
        self._timeout_minutes = 2
        self._last_payload = {"text": ["Display", "Initialized"]}
        self._last_background_colour = None
        self._task_display_timeout: asyncio.Task | None = None
        self._display_queue: asyncio.Queue | None = None

    async def __aenter__(self):
        self.init_display_controller()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._task_display_timeout.cancel()

    def init_display_controller(self):
        self._display_queue = asyncio.Queue()
        self._task_display_timeout = asyncio.create_task(self._switch_display())
        self._show_text(self._last_payload, force_update=True)

    async def send_message_to_display(self) -> AsyncGenerator:
        while True:
            message = await self._display_queue.get()
            await asyncio.sleep(0.1)
            yield message

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
                message = {"settings": "display_off"}
                self._process_event(message)
                self._display_off = True
            await asyncio.sleep(3)

    def _set_settings(self, message):
        self._disable_screen_timeout = message["settings"].get(
            "disable_screen_timeout", False
        )
        log.debug(f"Setting disable_screen_timeout to {self._disable_screen_timeout}")

    def _set_background_colour(self, message):
        """
        Sets the background color based on the provided message. The background color will not change if the display
        is turned off or if the background color remains the same as the last applied color.

        :param message: A dictionary containing the background color information. It can include a key
            "background_colour" with either a list representing RGB values, or a string value such as "white".
        :type message: dict
        :return: None
        """
        bg_colour = message.get("background_colour", [])

        # don't change background if display is off or
        # Avoid flickering if the background color is the same
        if self._display_off or self._last_background_colour == bg_colour:
            return

        msg = {"background_colour": tuple()}
        if isinstance(bg_colour, list):
            log.debug(f"Setting background colour to {message['background_colour']}")
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
                    text_lines[self._cursor_position : self._cursor_position + 2]
                )
                self._display_queue.put_nowait({"text": send_lines})
                self._lines = text_lines

    def _process_event(self, message: dict[str, Any]):
        try:
            if "background_color" in message:
                self._set_background_colour(message)
            elif "settings" in message:
                self._set_settings(message)
            elif "text" in message:
                self._show_text(message)
            else:
                log.error(f"Unknown message: {message}")
        except Exception as e:
            log.error(f"Error processing event: {e}")

    async def run(self, messages: AsyncGenerator, pi_buttons: AsyncGenerator):
        await asyncio.gather(
            self.listen_messages(messages), self.listen_direction(pi_buttons)
        )

    async def listen_messages(self, messages: AsyncGenerator):
        try:
            async for message in messages:
                self._process_event(message)
        except Exception as e:
            log.info(f"Error processing event: {e}")

    async def listen_direction(self, buttons: AsyncGenerator):
        try:
            async for direction in buttons:
                msg = self.push_direction(direction)
                if msg:
                    yield msg
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

    def _handle_next_button(self) -> bool:
        """Handle next button press. Returns True if display was updated."""
        if self._cursor_position + 3 == len(self._lines):
            self._cursor_position += 1
            self._update_display_text()
            return True
        elif self._cursor_position + 3 < len(self._lines):
            self._cursor_position += 2
            self._update_display_text()
            return True
        return False

    def _handle_prev_button(self) -> bool:
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
    ) -> dict[str, Any] | None:
        """
        Process button press and scroll display or wake it up if off.

        Returns message to send to topic, or None if handled internally.
        """
        # Reset timer on any button press
        self._start_timer_tick = datetime.now(UTC).timestamp()

        # Wake up display if off
        if self._display_off:
            msg = {"settings": "display_on"}
            self._display_queue.put_nowait(msg)
            self._display_off = False
            return None

        # Scroll display on button press (if not held)
        if not held:
            try:
                if button == "button_01" and self._handle_next_button():
                    return None
                elif button == "button_02" and self._handle_prev_button():
                    return None
            except Exception as e:
                log.error(f"Error processing button event: {e}")

        # Send message to topic if not handled above
        return {"button": button, "held": held}
