### Hardware:
- Raspberry Pi 4
- Display LCD1602 RGB Module
- No 2 push buttons

### Dev Tools

A very minimal set of dev tools have been configured, such as `pre-commit` hooks with `ruff` for linting. You can install the pre-commit hooks by running:

```bash
pip install -e ".[dev]"
pre-commit install
```

Then whenever you make a commit, `ruff` will automatically check your code for linting issues.


```ascii art:

┌─────────────────────┐
│                     │
│      Buttons        │
│                     │
└──────────┬──────────┘
           │
           │ button events
           │
           ▼
┌─────────────────────────────────────────┐          ┌─────────────────┐
│                                         │          │                 │
│       Display Controller                │─────────▶│  Real Display   │
│                                         │          │   (LCD1602)     │
│  ┌───────────────────────────────────┐  │          │                 │
│  │  Filter Button Events:            │  │          └─────────────────┘
│  │  • Scroll text                    │  │
│  │  • Wake up display                │  │
│  └───────────────────────────────────┘  │
│                                         │
└────────┬─────────────────────▲──────────┘
         │                     │
         │ filtered            │ translated text
         │ button events       │
         │                     │
         │                ┌────┴──────────────────┐
         │                │                       │
         │                │   Language Module     │
         │                │                       │
         │                │  ┌─────────────────┐  │
         │                │  │  Translate text │  │
         │                │  │  codes based on:│  │
         │                │  │  • Selected     │  │
         │                │  │    language     │  │
         │                │  └─────────────────┘  │
         │                │                       │
         │                └───────────▲───────────┘
         │                            │
         │                            │ text codes
         │                            │
         ▼                            │
┌─────────────────────────────────────┴───┐
│                                         │
│        Main Controller                  │
│                                         │
└─────────────────────────────────────────┘

```




### Project Scope:
This project implements control logic for an LCD1602 RGB display module using Python asyncio.

**Key Features:**
- **Automatic text scrolling**: Handles multi-line text display with button-controlled scrolling
- **Display timeout**: Automatically turns off the display after a period of inactivity
- **Multi-language support**: Translates text codes into any configured language
- **Event filtering**: Button events are intelligently filtered—handled locally for scrolling/wake operations or forwarded to the main controller when not needed for display control
- **Modular simulators**: Plug-and-play test modules that can be composed in various configurations to test the logic

**Architecture:**
The Display Controller acts as a mediator between buttons and the main controller. It receives button events from physical buttons and text events from the main controller. Button events are filtered to control text scrolling or wake the display; otherwise, they are forwarded to the main controller for application logic handling.


### TTL terminal for Raspberry Pi
In Ubuntu run the below command after connecting the USB to TTL connector:
```
sudo chmod ugo+rw /dev/ttyUSB0
```
then start the  Serial console with:

```
sudo screen /dev/ttyUSB0 115200
