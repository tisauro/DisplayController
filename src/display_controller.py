import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Literal, AsyncGenerator

log = logging.getLogger(__name__)


class DisplayController:
    """ """

    def __init__(self, languages: str = ""):
        self.lines = []
        self.cursor_position = 0

        self._display_queue = asyncio.Queue()

        # Display timeout
        self.start_timer_tick = datetime.now(UTC).timestamp()
        self.display_off = False
        self._disable_screen_timeout = False
        self._timeout_minutes = 2
        self._last_payload = {"text": "Initialized"}

        # self._timer = Thread(target=self._switch_display)
        # if self._screen.has_timeout():
        #     self._timer.start()
        self._task_display = asyncio.create_task(self._switch_display())

        # self._init_display()

    def _init_display(self):
        self._show_text(self._last_payload, force_update=True)

    async def _switch_display(self):
        while True:
            if (
                self.start_timer_tick
                + timedelta(minutes=self._timeout_minutes).total_seconds()
                < datetime.now(UTC).timestamp()
                and not self.display_off
                and not self._disable_screen_timeout
            ):
                log.debug("Display Off")
                message = {"settings": "display_off"}
                self._display_queue.put_nowait(message)
                self.display_off = True
            await asyncio.sleep(3)

    def _set_settings(self, message):
        if "disable_screen_timeout" in message:
            self._disable_screen_timeout = message["settings"]["disable_screen_timeout"]
            log.debug(
                f"Setting disable_screen_timeout to {self._disable_screen_timeout}"
            )

    def _set_background_colour(self, message):
        # don't change background if display is off
        if self.display_off:
            return

        # Avoid flickering if the background color is the same
        if self._last_payload.get("background_colour", []) == message.get(
            "background_colour", []
        ):
            return

        if "background_color" in message:
            log.debug(f'Setting background colour to {message["background_color"]}')
            self._display_queue.put_nowait(message)
        if "background_colour_white" in message:
            log.debug("Setting background colour white")
            message["background_color"] = [255, 255, 255]
            self._display_queue.put_nowait(message)

    def _show_text(self, payload, force_update: bool = False) -> None:
        new_message = False

        if not force_update and (
            ("text" in self._last_payload and "text" in payload)
            and (self._last_payload["text"] == payload.get("text", []))
        ):
            return

        if not force_update and (
            ("code_language" in self._last_payload and "code_language" in payload)
            and (self._last_payload["code_language"] == payload["code_language"])
            and ("parameters" in self._last_payload and "parameters" in payload)
            and self._last_payload["parameters"] == payload["parameters"]
        ):
            return

        if "code_language" in payload:
            self._last_payload = payload
            self.lines = self._languages.get_text(
                payload["code_language"], payload.get("parameters", [])
            )
            new_message = True

        if "text" in payload:
            self._last_payload = payload
            new_message = True
            text = payload["text"]
            if isinstance(text, str):
                text = [text]
            self.lines = text

        if not self.display_off:
            # don't write on display if it is off
            if new_message and len(self.lines) == 1:
                log.debug(
                    f"Received message: {self._last_payload}, no lines: {len(self.lines)}"
                )
                with self._lock:
                    self._screen.display_clear()
                    self._screen.print_lines(self.lines[0], "")
            elif new_message and len(self.lines) > 1:
                log.debug(
                    f"Received message: {self._last_payload}, no lines: {len(self.lines)}"
                )
                with self._lock:
                    self.cursor_position = 0
                    self._screen.display_clear()
                    self._screen.print_lines(self.lines[0], self.lines[1])

    def _process_event(self, message: dict):
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
                self.push_direction(direction)
        except Exception as e:
            log.info(f"Error processing event: {e}")

    def push_direction(
        self, button: Literal["Next", "Prev", "Double"], held: bool = False
    ) -> AsyncGenerator:
        # avoid moving the state if the display is off
        # use the first press of the button to wake up the display
        # if self.display_off:
        #     self.start_timer_tick = datetime.now(UTC).timestamp()
        #     with self._lock:
        #         self._screen.display_on()
        #     self.display_off = False
        #     self._init_display()
        #
        # else:
        #     self.start_timer_tick = datetime.now(UTC).timestamp()
        print(button, held)
        pass
        # Todo: improve code in here: perhaps spit this in several functions
        # We use push of the buttons to move the text up and down the screen
        try:
            # scroll test in display before sending message to the topic
            if button == "Next" and not held:
                # we want this to work with odd and even number of lines
                if self.cursor_position + 3 == len(self.lines):
                    self.cursor_position += 1
                    with self._lock:
                        self._screen.display_clear()
                        self._screen.print_lines(
                            self.lines[self.cursor_position],
                            self.lines[self.cursor_position + 1],
                        )
                elif self.cursor_position + 3 < len(self.lines):
                    self.cursor_position += 2
                    with self._lock:
                        self._screen.display_clear()
                        self._screen.print_lines(
                            self.lines[self.cursor_position],
                            self.lines[self.cursor_position + 1],
                        )

            elif button == "Prev" and not held:
                # we want this to work with odd and even number of lines
                if self.cursor_position - 1 == 0:
                    self.cursor_position = 0
                    with self._lock:
                        self._screen.display_clear()
                        self._screen.print_lines(
                            self.lines[self.cursor_position],
                            self.lines[self.cursor_position + 1],
                        )
                elif self.cursor_position - 2 >= 0:
                    self.cursor_position -= 2
                    with self._lock:
                        self._screen.display_clear()
                        self._screen.print_lines(
                            self.lines[self.cursor_position],
                            self.lines[self.cursor_position + 1],
                        )
        except Exception as e:
            log.error(f"Error processing event: {e}")

        # if none of the above send message to topic
        msg = {"button": button, "held": held}
        yield msg
