# Write your code here :-)
import time
import board
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal

# --- Display setup ---
matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

# Create a new label with the color and text selected
matrixportal.add_text(
    text_font=terminalio.FONT,
    text_position=(0, (matrixportal.graphics.display.height // 2) - 1),
    scrolling=True,
)

SCROLL_DELAY = 0.03

contents = [
    { 'text': 'THIS IS RED',  'color': '#cf2727'},
    { 'text': 'THIS IS BLUE', 'color': '#0846e4'},
]

while True:
    for content in contents:
        matrixportal.set_text(content['text'])

        # Set the text color
        matrixportal.set_text_color(content['color'])

        # Scroll it
        matrixportal.scroll_text(SCROLL_DELAY)# Write your code here :-)
