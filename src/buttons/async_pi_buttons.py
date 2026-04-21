import logging
import asyncio
import threading
from typing import AsyncIterator, Optional

from gpiozero import Button

logger = logging.getLogger(__name__)


class AsyncPiButtons:
    def __init__(
        self,
        button_01_pin: int = 23,
        button_02_pin: int = 22,
        hold_time: float = 0.5,
        bounce_time: float = 0.05,
    ):
        self._button_states: dict[Button, bool] = {}
        self._double_button_triggered = False
        self.hold_time = hold_time
        self.bounce_time = bounce_time
        self._button_01_pin = button_01_pin
        self._button_02_pin = button_02_pin
        self._button_01: Optional[Button] = None
        self._button_02: Optional[Button] = None
        self._queue: Optional[asyncio.Queue[str]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.Lock()

    async def __aenter__(self) -> "AsyncPiButtons":
        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue()
        try:
            # Cast to Any because gpiozero stubs might incorrectly expect int for hold_time
            self._button_01 = Button(
                self._button_01_pin,
                pull_up=True,
                hold_time=self.hold_time,  # type: ignore
                bounce_time=self.bounce_time,
            )
            self._button_01.when_held = self._button_01_held
            self._button_01.when_released = self._button_01_released
        except Exception:
            logger.exception("Failed to attach button_01 interrupt")
            raise
        try:
            # Cast to Any because gpiozero stubs might incorrectly expect int for hold_time
            self._button_02 = Button(
                self._button_02_pin,
                pull_up=True,
                hold_time=self.hold_time,  # type: ignore
                bounce_time=self.bounce_time,
            )
            self._button_02.when_held = self._button_02_held
            self._button_02.when_released = self._button_02_released
        except Exception:
            logger.exception("Failed to attach button_02 interrupt")
            if self._button_01:
                self._button_01.close()
            raise
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._button_01:
            self._button_01.close()
        if self._button_02:
            self._button_02.close()

    def _button_01_released(self, btn: Button) -> None:
        if self._loop is None or self._queue is None or self._button_02 is None:
            return
        if not self._button_states.get(btn, False):
            logger.debug("Button 01 pressed")
            self._loop.call_soon_threadsafe(self._queue.put_nowait, "button_01")
        self._button_states[btn] = False
        if not getattr(self._button_02, "is_pressed", False):
            self._double_button_triggered = False

    def _button_02_released(self, btn: Button) -> None:
        if self._loop is None or self._queue is None or self._button_01 is None:
            return
        if not self._button_states.get(btn, False):
            logger.debug("Button 02 pressed")
            self._loop.call_soon_threadsafe(self._queue.put_nowait, "button_02")
        self._button_states[btn] = False
        if not getattr(self._button_01, "is_pressed", False):
            self._double_button_triggered = False

    def _button_01_held(self, btn: Button) -> None:
        if self._loop is None or self._queue is None or self._button_02 is None:
            return
        self._button_states[btn] = True
        ret = self._button_02.wait_for_active(timeout=0.3)
        if ret:
            with self._lock:
                if not self._double_button_triggered:
                    self._double_button_triggered = True
                    self._button_states[self._button_02] = True
                    self._loop.call_soon_threadsafe(
                        self._queue.put_nowait, "double_button"
                    )
        else:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, "button_01_held")

    def _button_02_held(self, btn: Button) -> None:
        if self._loop is None or self._queue is None or self._button_01 is None:
            return
        self._button_states[btn] = True
        ret = self._button_01.wait_for_active(timeout=0.3)
        if ret:
            with self._lock:
                if not self._double_button_triggered:
                    self._double_button_triggered = True
                    self._button_states[self._button_01] = True
                    self._loop.call_soon_threadsafe(
                        self._queue.put_nowait, "double_button"
                    )
        else:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, "button_02_held")

    def __aiter__(self) -> AsyncIterator[str]:
        return self

    async def __anext__(self) -> str:
        if self._queue is None:
            raise StopAsyncIteration
        direction = await self._queue.get()
        return direction


if __name__ == "__main__":
    import time

    async def main():
        async with AsyncPiButtons() as buttons:
            async for direction in buttons:
                print(f"{time.time():0.2f} - Direction: {direction}")

    asyncio.run(main())
