import pytest
from display.lcd_1602_display import LCD1602Display
from unittest.mock import patch, Mock, call


@patch("display.lcd_1602_display.SMBus")
@pytest.mark.asyncio
async def test_contex_manager(smbus_mock):
    async with LCD1602Display() as display:
        assert display is not None
        assert display._smbus is not None


@patch("display.lcd_1602_display.SMBus")
@pytest.mark.asyncio
async def test_print_lines(smbus_mock):
    async def mock_messages():
        yield {"text": ("line_1", "line_2")}
        yield {"text": ("line_3", "line_4")}

    async with LCD1602Display() as display:
        display.print_lines = Mock()
        await display.receive_messages(mock_messages())
        display.print_lines.call_count = 2
        display.print_lines.assert_any_call("line_1", "line_2")
        display.print_lines.assert_has_calls(
            [call("line_1", "line_2"), call("line_3", "line_4")]
        )


@patch("display.lcd_1602_display.SMBus")
@pytest.mark.asyncio
async def test_receive_settiings(smbus_mock):
    async def mock_settings():
        yield {"settings": "clear"}
        yield {"settings": "on"}
        yield {"settings": "off"}

    async with LCD1602Display() as display:
        display.display_clear = Mock()
        display.display_on = Mock()
        display._display_off = Mock()
        await display.receive_messages(mock_settings())
        display.display_clear.assert_called_once()
        display.display_on.assert_called_once()
        display._display_off.assert_called_once()


@patch("display.lcd_1602_display.SMBus")
@pytest.mark.asyncio
async def test_receive_background_colour(smbus_mock):
    async def mock_colour():
        yield {"background_colour": (245, 245, 245)}

    async with LCD1602Display() as display:
        display.set_rgb = Mock()
        await display.receive_messages(mock_colour())
        display.set_rgb.assert_called_once_with(245, 245, 245)
