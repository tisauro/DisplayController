import asyncio

import pytest
from display_controller import DisplayController
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_aenter_aexit():
    async with DisplayController() as controller:
        assert controller is not None
        assert controller._task_display_timeout is not None
        assert not controller._task_display_timeout.done()
        assert not controller._task_display_timeout.cancelled()
        assert controller._display_queue is not None
        assert controller._display_queue.qsize() == 1
        assert controller._last_payload == {"text": ["Display", "Initialized"]}


@pytest.mark.parametrize(
    "display_off,disable_screen_timeout,should_call",
    [
        (False, False, True),
        (True, False, False),
        (False, True, False),
        (True, True, False),
    ],
    ids=[
        "normal_case",
        "display_off",
        "disable_screen_timeout",
        "display_off_and_disable",
    ],
)
@patch("display_controller.datetime")
@pytest.mark.asyncio
async def test_display_timeout_task(
    mock_datetime, display_off, disable_screen_timeout, should_call
):
    # Mock datetime to return initial time, then time after a timeout period
    mock_now = MagicMock()
    mock_now.timestamp.side_effect = [
        1000.0,
        1000.0 + (60 * 2) + 5,
    ]  # 2 min timeout + 5 sec
    mock_datetime.now.return_value = mock_now

    async with DisplayController() as controller:
        with patch.object(controller, "_process_event") as mock_process:
            assert controller._task_display_timeout is not None
            controller._display_off = display_off
            controller._disable_screen_timeout = disable_screen_timeout

            # Wait for the timeout task to run (it checks every 3 seconds)
            await asyncio.sleep(4)
            if should_call:
                message = {"settings": "display_off"}
                mock_process.assert_called_once_with(message)
            else:
                mock_process.assert_not_called()


@pytest.mark.parametrize(
    "background_colour,expected",
    [("white", (255, 255, 255)), ([200, 200, 200], (200, 200, 200))],
)
@pytest.mark.asyncio
async def test_background_colour(background_colour, expected):
    async with DisplayController() as controller:
        with patch.object(controller._display_queue, "put_nowait") as mock_put:
            controller._set_background_colour({"background_colour": background_colour})
            mock_put.assert_called_once_with({"background_colour": expected})


@pytest.mark.asyncio
async def test_push_direction_wake_screen():
    async with DisplayController() as controller:
        controller._display_off = True
        with patch.object(controller._display_queue, "put_nowait") as mock_put:
            ret = controller.push_direction(button="button_01", held=False)
            assert ret == {}
            msg = {"settings": "display_on"}
            mock_put.assert_called_once_with(msg)


@pytest.mark.parametrize(
    "button,held",
    [
        ("button_01", True),
        ("button_02", True),
        ("button_01", False),
        ("button_02", False),
    ],
)
@pytest.mark.asyncio
async def test_push_direction_scroll_display_1_line(button, held):
    async with DisplayController() as controller:
        controller._display_off = False
        with patch.object(controller._display_queue, "put_nowait") as mock_put:
            controller._lines = ["line_1"]
            ret = controller.push_direction(button=button, held=held)
            assert ret == {"button": button, "held": held}
            mock_put.assert_not_called()


@pytest.mark.parametrize(
    "button,held",
    [
        ("button_01", True),
        ("button_02", True),
        ("button_01", False),
        ("button_02", False),
    ],
)
@pytest.mark.asyncio
async def test_push_direction_scroll_display_2_lines(button, held):
    async with DisplayController() as controller:
        controller._display_off = False
        with patch.object(controller._display_queue, "put_nowait") as mock_put:
            controller._lines = ["line_1", "line_2"]
            ret = controller.push_direction(button=button, held=held)
            assert ret == {"button": button, "held": held}
            mock_put.assert_not_called()


@pytest.mark.parametrize(
    "button,lines,expected_calls",
    [
        pytest.param(
            "button_01", ["l1", "l2"], 0, id="2_lines_no_scroll"
        ),  # 2 lines - no scroll
        pytest.param(
            "button_01", ["l1", "l2", "l3"], 1, id="3_lines_1_scroll"
        ),  # 3 lines - scroll once
        pytest.param(
            "button_01", ["l1", "l2", "l3", "l4"], 1, id="4_lines_1_scroll"
        ),  # 4 lines - scroll twice
        pytest.param(
            "button_01", ["l1", "l2", "l3", "l4", "l5"], 2, id="5_lines_2_scrolls"
        ),  # 5 lines - scroll twice
        pytest.param(
            "button_01", ["l1", "l2", "l3", "l4", "l5", "l6"], 2, id="6_lines_2_scrolls"
        ),
        # 6 lines - scroll twice
        pytest.param(
            "button_01",
            ["l1", "l2", "l3", "l4", "l5", "l6", "l7"],
            3,
            id="7_lines_3_scrolls",
        ),
        # 7 lines - scroll 3 times
    ],
)
@pytest.mark.asyncio
async def test_push_direction_scroll_forward(button, lines, expected_calls):
    async with DisplayController() as controller:
        controller._display_off = False
        controller._lines = lines

        with patch.object(controller._display_queue, "put_nowait") as mock_put:
            # Scroll until we can't scroll anymore
            for i in range(expected_calls):
                ret = controller.push_direction(button=button, held=False)
                assert ret == {}

            # The next scroll should return a button message (can't scroll further)
            ret = controller.push_direction(button=button, held=False)
            assert ret == {"button": button, "held": False}

            # Verify final call showed the last two lines
            final_msg = {"text": (lines[-2], lines[-1])}
            assert mock_put.call_count == expected_calls
            if expected_calls > 0:
                assert mock_put.call_args[0][0] == final_msg


@pytest.mark.parametrize(
    "button,lines,expected_calls",
    [
        pytest.param(
            "button_02", ["l1", "l2"], 0, id="2_lines_no_scroll"
        ),  # 2 lines - no scroll
        pytest.param(
            "button_02", ["l1", "l2", "l3"], 1, id="3_lines_1_scroll"
        ),  # 3 lines - scroll once
        pytest.param(
            "button_02", ["l1", "l2", "l3", "l4"], 1, id="4_lines_1_scroll"
        ),  # 4 lines - scroll twice
        pytest.param(
            "button_02", ["l1", "l2", "l3", "l4", "l5"], 2, id="5_lines_2_scrolls"
        ),  # 5 lines - scroll twice
        pytest.param(
            "button_02", ["l1", "l2", "l3", "l4", "l5", "l6"], 2, id="6_lines_2_scrolls"
        ),
        # 6 lines - scroll twice
        pytest.param(
            "button_02",
            ["l1", "l2", "l3", "l4", "l5", "l6", "l7"],
            3,
            id="7_lines_3_scrolls",
        ),
        # 7 lines - scroll 3 times
    ],
)
@pytest.mark.asyncio
async def test_push_direction_scroll_backwards(button, lines, expected_calls):
    async with DisplayController() as controller:
        controller._display_off = False
        controller._lines = lines
        controller._cursor_position = len(lines) - 2

        with patch.object(controller._display_queue, "put_nowait") as mock_put:
            # Scroll until we can't scroll anymore
            for i in range(expected_calls):
                ret = controller.push_direction(button=button, held=False)
                assert ret == {}

            # The next scroll should return a button message (can't scroll further)
            ret = controller.push_direction(button=button, held=False)
            assert ret == {"button": button, "held": False}

            # Verify final call showed the first two lines
            final_msg = {"text": (lines[0], lines[1])}
            assert mock_put.call_count == expected_calls
            if expected_calls > 0:
                assert mock_put.call_args[0][0] == final_msg
