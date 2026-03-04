import asyncio
from typing import AsyncGenerator


class DummyMainController:
    def __init__(self, messages=None):
        self._messages = messages
        self._count = len(self._messages)
        self._current_index = 0
        self._message_queue = asyncio.Queue()

    #     self._task_send_message = None
    #
    async def __aenter__(self):
        # self._task_send_message = asyncio.create_task(self.send_message())
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        # self._task_send_message.cancel()
        # await self._task_send_message
        pass

    async def send_message(self):
        while True:
            message = await self._message_queue.get()
            yield message

    async def run(self, buttons_events: AsyncGenerator):
        async for event in buttons_events:
            if event.type == "button_01":
                print(f"Button 01 clicked: {event.button_id}")
                self._current_index += 1
                if self._current_index >= self._count:
                    self._current_index = 0
                await self._message_queue.put(self._messages[self._current_index])
            elif event.type == "button_02":
                print(f"Button 02: {event.button_id}")
                self._current_index -= 1
                if self._current_index < 0:
                    self._current_index = self._count - 1
                await self._message_queue.put(self._messages[self._current_index])
            elif event.type == "double_button":
                print("Double button clicked")
                self._current_index = 0
                await self._message_queue.put(self._messages[self._current_index])
            else:
                print(f"Unknown event type: {event.type}")
