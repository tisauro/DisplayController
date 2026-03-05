import time
import logging
from typing import AsyncGenerator

from smbus2 import SMBus

from src.display.base_display import BaseDisplay

# Device I2C Arress
LCD_ADDRESS = 0x7C >> 1
RGB_ADDRESS = 0xC0 >> 1

# color define
REG_RED = 0x04
REG_GREEN = 0x03
REG_BLUE = 0x02
REG_MODE1 = 0x00
REG_MODE2 = 0x01
REG_OUTPUT = 0x08

LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

log = logging.getLogger(__name__)


class LCD1602Display(BaseDisplay):
    def __init__(self, i2c_address=0x27, bus=1):
        self._num_lines = None
        self._smbus = None
        self._backlight = LCD_NOBACKLIGHT
        self.i2c_address = LCD_ADDRESS
        self._row = 2
        self._col = 16
        self._show_function = LCD_4BITMODE | LCD_1LINE | LCD_5x8DOTS
        self._is_rgb = True

    def __setitem__(self, line, string):
        if not 0 <= line <= 1:
            raise IndexError("line number out of range")
        # Format string to exactly the width of LCD
        self.print_line(f"{string!s:<16.16}", line + 1)

    def _command(self, cmd):
        if self._smbus:
            try:
                self._smbus.write_byte_data(LCD_ADDRESS, 0x80, cmd)
            except Exception as e:
                log.exception(e)

    def _write(self, data):
        if self._smbus:
            try:
                self._smbus.write_byte_data(LCD_ADDRESS, 0x40, data)
            except Exception as e:
                log.exception(e)

    def _set_reg(self, reg, data):
        if self._smbus:
            self._smbus.write_byte_data(RGB_ADDRESS, reg, data)

    def _clear(self):
        self._command(LCD_CLEARDISPLAY)
        time.sleep(0.002)

    def set_rgb(self, r: int, g: int, b: int):
        try:
            self._set_reg(REG_RED, r)
            self._set_reg(REG_GREEN, g)
            self._set_reg(REG_BLUE, b)
        except Exception as e:
            self._is_rgb = False
            log.debug(f"No RGB found {e}")

    def set_cursor(self, col, row):
        if row == 0:
            col |= 0x80
        else:
            col |= 0xC0
        self._command(col)

    def _printout(self, arg):
        if isinstance(arg, int):
            arg = str(arg)

        for x in bytearray(arg, "utf-8"):
            self._write(x)

    def display_on(self):
        self._showcontrol |= LCD_DISPLAYON
        self._command(LCD_DISPLAYCONTROL | self._showcontrol)
        self.set_color_white()

    def _init_display(self, cols, lines):
        try:
            self._smbus = SMBus(1)
        except Exception as e:
            log.exception(e)
            self._smbus = None

        if lines > 1:
            self._show_function |= LCD_2LINE

        self._num_lines = lines
        self._currline = 0

        time.sleep(0.05)

        # Send function set command sequence
        self._command(LCD_FUNCTIONSET | self._show_function)
        # delayMicroseconds(4500);  # wait more than 4.1ms
        time.sleep(0.005)
        # second try
        self._command(LCD_FUNCTIONSET | self._show_function)
        # delayMicroseconds(150);
        time.sleep(0.005)
        # third go
        self._command(LCD_FUNCTIONSET | self._show_function)
        # finally, set # lines, font size, etc.
        self._command(LCD_FUNCTIONSET | self._show_function)
        # turn the display on with no cursor or blinking default
        self._showcontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF
        self.display_on()
        # clear it off
        self._clear()
        # Initialize to default text direction (for romance languages)
        self._showmode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT
        # set the entry mode
        self._command(LCD_ENTRYMODESET | self._showmode)

        try:
            # backlight init
            self._set_reg(REG_MODE1, 0)
            # set LEDs controllable by both PWM and GRPPWM registers
            self._set_reg(REG_OUTPUT, 0xFF)
            # set MODE2 values
            # 0010 0000 -> 0x20  (DMBLNK to 1, ie blinky mode)
            self._set_reg(REG_MODE2, 0x20)

            self.set_color_white()
        except Exception:
            self._is_rgb = False
            log.debug("No RGB found")
        # log.debug(f"Setting RGB display mode failed {e}")

    def set_color_white(self):
        self.set_rgb(255, 255, 255)

    def display_clear(self):
        self._clear()

    def display_off(self):
        self.set_rgb(0, 0, 0)
        if self._is_rgb:
            self._clear()

    def print_line(self, string, line):
        if line == 1:
            self.set_cursor(0, 0)
        elif line == 2:
            self.set_cursor(0, 1)

        self._printout(string)

    def print_lines(self, line_1, line_2):
        self.print_line(f"{line_1!s:<16.16}", 1)
        self.print_line(f"{line_2!s:<16.16}", 2)

    def has_timeout(self):
        return self._is_rgb

    async def __aenter__(self):
        self._init_display(self._row, self._col)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._smbus:
            self._smbus.close()

    async def receive_messages(self, messages: AsyncGenerator):
        async for message in messages:
            log.debug(f"LCD Display Received message: {message}")
            if "text" in message:
                line1, line2, *_ = (*message.get("text", ()), "", "")
                self.print_lines(line1, line2)
            elif "settings" in message:
                if "clear" in message["settings"]:
                    self.display_clear()
                elif "on" in message["settings"]:
                    self.display_on()
                elif "off" in message["settings"]:
                    self.display_off()
                else:
                    log.debug(f"No settings found for {message['settings']}")
            elif "background_colour" in message:
                r, g, b = message["background_colour"]
                self.set_rgb(r, g, b)
            else:
                log.debug(f"No message found for {message}")
