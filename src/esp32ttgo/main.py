import display
from micropython import const
from utime import sleep_ms

COLOR_OFF = const(0xAAAAAA)
COLOR_ON = const(0xFFC117)

tft = display.TFT()
# 240 * 320
tft.init(tft.ST7789, bgr=True, rot=tft.LANDSCAPE_FLIP, miso=17, backl_pin=4, backl_on=1, mosi=19, clk=18, cs=5, dc=16, splash=False)
# tft.font(tft.FONT_Ubuntu)
tft.font(tft.FONT_7seg)
tft.attrib7seg(12, 12, COLOR_ON, COLOR_ON)
print(tft.fontSize())
tft.rect(0, 0, 320, 240, fillcolor=tft.WHITE)
tft.set_bg(tft.WHITE)
tft.set_fg(COLOR_ON)


# tft.setwin(40, 52, 320, 240)

# for i in range(0, 241):
#     color = 0xFFFFFF - tft.hsb2rgb(i / 241 * 360, 1, 1)
#     tft.line(i, 0, i, 135, color)

# tft.set_fg(0x000000)

# tft.ellipse(120, 67, 120, 67)

# tft.line(0, 0, 240, 135)

# (width, height)
WIN_SIZE = tft.winsize()

# for i in range(0, 321):
#     tft.pixel(i, int(WIN_SIZE[1] / 2), tft.BLACK)

for i in range(21):
    tft.rect(0, 0, 320, 240, fillcolor=tft.WHITE)
    x = 240 if i < 10 else 200
    y = 58
    tft.text(x, y, str(i))
    sleep_ms(50)
text = "12"
# tft.text(120 - int(tft.textWidth(text) / 2), 67 - int(tft.fontSize()[1] / 2), text, 0xFFFFFF)
# tft.text(tft.RIGHT -


# tft.attrib7seg(10, 120, tft.RED, COLOR_ON)

tft.circle(50, 100, 20, tft.BLACK, tft.WHITE)
tft.circle(150, 200, 20, tft.WHITE, tft.BLACK)