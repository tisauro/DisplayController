### Hardware:
- Raspberry Pi 4
- Display LCD1602 RGB Module
- No 2 push buttons

### Project scope:
This project implments the logic to display text on LCD1602 RGB Module.
the buttons are used to implement automatic scrolling of the text which can be split in two or more lines.
The functinality also includes a display timeout to simulate the display going off aftera certain time.
A translator module to translate the text to any laguage is also implemented.
Button events are forwarded to the main controll logic if the is no need to scroll the text. 
The logic is enterely implemented using Python Asycio.
Different simulators are also implemented to test the logic.
they are plug and play modules that can be compsed in different ways to test the logic.


### TTL terminal for Raspberry Pi
In Ubuntu run the below command after connecting the USB to TTL connector:
```
sudo chmod ugo+rw /dev/ttyUSB0
```
then start the  Serial console with:

```
sudo screen /dev/ttyUSB0 115200
