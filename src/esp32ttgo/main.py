import math
import sys

import display
import machine
from machine import ADC
from machine import Pin
from micropython import const
from collections import OrderedDict
import network
from utime import sleep_ms
from microWebSrv import MicroWebSrv

# print("deactivating wlan")
# WLAN(0).active(False)
# WLAN(1).active(False)

machine.freq(240000000)

# configure wifi connectivity
print("Connecting to servant...")
# WIFI = network.WLAN(network.STA_IF)
# WIFI.active(True)
# WIFI.connect("Headrush Servant")


def _create_pin_in(pin_id: int) -> Pin:
    return Pin(pin_id, Pin.IN, Pin.PULL_UP)

# button = _create_pin_in(32)
# button2 = _create_pin_in(33)
# button3 = _create_pin_in(13)
# button4 = _create_pin_in(2)
# button5 = _create_pin_in(15)

_BUTTON_PIN_MAP = {
    b"button_rig_up": _create_pin_in(32),
    b"button_rig_down": _create_pin_in(33),
    b"button_scene1": _create_pin_in(25),
    b"button_scene2": _create_pin_in(26),
    b"button_scene3": _create_pin_in(27),
    b"button_scene4": _create_pin_in(14),
}

_BUTTON_POT = _create_pin_in(12)
_POT = ADC(Pin(35))
_POT.atten(ADC.ATTN_11DB)


SWITCH_STATUS = OrderedDict()
SWITCH_STATUS[b"button_scene1"] = (0, 1)
SWITCH_STATUS[b"button_scene2"] = (1, 0)
SWITCH_STATUS[b"button_scene3"] = (2, 0)
SWITCH_STATUS[b"button_scene4"] = (3, 0)
SWITCH_STATUS[b"button_rig_up"] = (4, 0)
SWITCH_STATUS[b"button_rig_down"] = (5, 0)
SWITCH_STATUS[b"POT"] = (6, 0)


TFT = display.TFT()
# 320 * 240, but in reality x goes from 40 to 279 and y goes from 53 to 187 -> 239 * 134 --> 1.78 ratio instead of 1.33
# --> 240 * 135
TFT.init(TFT.ST7789, rot=TFT.LANDSCAPE_FLIP, miso=17, backl_pin=4, backl_on=1, mosi=19, clk=18, cs=5, dc=16, splash=False)
TFT.tft_writecmd(0x21)
TFT.setwin(39, 52, 279, 187)  # 240 * 135
# # rig window
# TFT.setwin(180, 0, 140, 70)
# TFT.savewin()
# TFT.resetwin()
# SCREEN_SIZE = TFT.screensize()
# print(SCREEN_SIZE)
WINDOW_SIZE = TFT.winsize()
WINDOW_SPLIT_X_1 = int(WINDOW_SIZE[0] / 3)
print(WINDOW_SPLIT_X_1)
WINDOW_SPLIT_X_2 = int(WINDOW_SPLIT_X_1 * 2)
WINDOW_SPLIT_Y = int(WINDOW_SIZE[1] / 2)
WINDOW_SPLIT_Y_3_4 = int(WINDOW_SIZE[1] / 4 * 3)
print(WINDOW_SIZE)

MARGIN = const(6)
MARGIN_HALF = const(3)

COLOR_OFF = const(0x551100)
COLOR_ON = const(0xDDAA00)
COLOR_BG = TFT.BLACK

RIG_WIDTH = WINDOW_SPLIT_X_1
RIG_HEIGHT = WINDOW_SPLIT_Y
RIG_X_START = WINDOW_SIZE[0] - RIG_WIDTH
RIG_Y_START = 0

SWITCH_SPACE_WIDTH = int(WINDOW_SIZE[0] / 4)
SWITCH_HALF_SPACE_WIDTH = int(SWITCH_SPACE_WIDTH / 2)
SWITCH_Y = WINDOW_SPLIT_Y_3_4
SWITCH_R = SWITCH_HALF_SPACE_WIDTH - MARGIN


def map_switch_status_to_color(value: float) -> hex:
    # map values between 0 and 1 to gradually go from COLOR_OFF to COLOR_ON
    if value == 1:
        return COLOR_ON
    else:
        return COLOR_OFF


def clear_background():
    print("rendering background")
    # set black background
    # TFT.rect(0, 0, SCREEN_SIZE[0], SCREEN_SIZE[1], fillcolor=TFT.WHITE)
    TFT.clear(TFT.BLACK)


def init_tft() -> None:
    print("init tft")

    TFT.font(TFT.FONT_7seg)
    TFT.attrib7seg(12, 12, COLOR_ON, COLOR_ON)

    clear_background()

    # set front and back colors so segment font is printed properly
    TFT.set_bg(COLOR_BG)
    TFT.set_fg(COLOR_ON)


# tft.setwin(40, 52, 320, 240)

# for i in range(0, 241):
#     color = 0xFFFFFF - tft.hsb2rgb(i / 241 * 360, 1, 1)
#     tft.line(i, 0, i, 135, color)

# tft.set_fg(0x000000)

# tft.ellipse(120, 67, 120, 67)

# tft.line(0, 0, 240, 135)

# (width, height)

# for i in range(0, 321):
#     tft.pixel(i, int(WIN_SIZE[1] / 2), tft.BLACK)



# for i in range(21):
#     tft.rect(0, 0, 320, 240, fillcolor=tft.WHITE)
#     x = 240 if i < 10 else 200
#     y = 58
#     tft.text(x, y, str(i))
#     sleep_ms(50)
# text = "12"



# tft.text(120 - int(tft.textWidth(text) / 2), 67 - int(tft.fontSize()[1] / 2), text, 0xFFFFFF)
# tft.text(tft.RIGHT -


# tft.attrib7seg(10, 120, tft.RED, COLOR_ON)

# tft.circle(50, 100, 20, tft.BLACK, tft.WHITE)
# tft.circle(150, 200, 20, tft.WHITE, tft.BLACK)


def draw_switch(switch: bytes) -> None:
    pos, status = SWITCH_STATUS[switch]
    # lower row
    color = COLOR_ON if status == 1 else COLOR_OFF
    if pos <= 3:
        switch_space_multiplier = SWITCH_SPACE_WIDTH * pos
        TFT.rect(switch_space_multiplier, WINDOW_SPLIT_Y, switch_space_multiplier + SWITCH_SPACE_WIDTH, WINDOW_SIZE[1], COLOR_BG)
        TFT.circle(pos * SWITCH_SPACE_WIDTH + SWITCH_HALF_SPACE_WIDTH, SWITCH_Y, SWITCH_R, color, color)
    # elif pos == 6:
    #     TFT.circle(SWITCH_HALF_SPACE_WIDTH, int(WINDOW_SPLIT_Y / 2), SWITCH_R, color, color)


def reset_switches() -> None:
    for switch in SWITCH_STATUS:
        draw_switch(switch)


def print_rig_number(rig: int) -> None:
    TFT.rect(RIG_X_START, RIG_Y_START, RIG_WIDTH, RIG_HEIGHT, color=COLOR_BG, fillcolor=COLOR_BG)
    text = str(rig)
    print("rig {}".format(rig))
    segment_width = int(RIG_WIDTH / 2)
    x = RIG_X_START + ((2 - len(text)) * segment_width)
    y = RIG_Y_START
    TFT.text(x, y, text)


# def configure_socket():
#     while not WIFI.isconnected():
#         print("Waiting for connection with servant.")
#         sleep_ms(150)
#
#     import socket
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     # sock.bind(("192.168.4.1", 10086))
#     sock.sendto(b"Remote connected!", ("192.168.4.1", 10086))
#
#     return sock

ARROW_SIDE = WINDOW_SPLIT_X_1 - MARGIN
ARROW_X1 = WINDOW_SPLIT_X_1 + MARGIN_HALF
ARROW_X3 = WINDOW_SPLIT_X_2 - MARGIN_HALF
ARROW_X2 = int((ARROW_X3 - ARROW_X1) / 2)
ARROW_HEIGHT = int(ARROW_SIDE * math.sqrt(3) / 2)
ARROW_HEIGHT_2 = int(ARROW_HEIGHT / 2)
ARROW_Y1 = int((WINDOW_SPLIT_Y - ARROW_HEIGHT) / 2)
ARROW_Y2 = WINDOW_SPLIT_Y - ARROW_Y1


def _draw_arrow(up=True) -> None:
    if up:
        print(ARROW_X1, ARROW_Y2, ARROW_X2, ARROW_Y1, ARROW_X3, ARROW_Y2, COLOR_ON, COLOR_ON)
        TFT.triangle(ARROW_X1, ARROW_Y2, ARROW_X2, ARROW_Y1, ARROW_X3, ARROW_Y2, COLOR_ON, COLOR_ON)
    else:
        print(ARROW_X1, ARROW_Y1, ARROW_X2, ARROW_Y2, ARROW_X3, ARROW_Y1, COLOR_ON, COLOR_ON)
        TFT.triangle(ARROW_X1, ARROW_Y1, ARROW_X2, ARROW_Y2, ARROW_X3, ARROW_Y1, COLOR_ON, COLOR_ON)


# def draw_arrow(up = True) -> None:
#     _thread.start_new_thread(__blink_led, (times, interval))


def main() -> None:
    # sock = configure_socket()
    reset_switches()

    # print("in main")
    rig = 1
    print_rig_number(rig)
    # button_down = None
    # while True:
    #     # if remote.is_connected():
    #     # foot switches
    #     for command, button in _BUTTON_PIN_MAP.items():
    #         if not button_down == command and button.value() == 0:
    #             # print("{} pressed".format(command))
    #             button_down = command
    #             # print("sending '{command}'.".format(command=command))
    #             if command in [b"button_rig_up", b"button_rig_down"]:
    #                 if command == b"button_rig_up":
    #                     rig += 1
    #                 elif command == b"button_rig_down":
    #                     rig -= 1
    #                     sys.exit()
    #
    #                 print_rig_number(rig)
    #             # remote.send(struct.pack("I", command))
    #             # remote.send(command)
    #
    #             # sock.sendto(command, ("192.168.4.1", 10086))
    #
    #             break
    #         elif button_down == command and button.value() == 1:
    #             button_down = None
    #
    #     # print("({}, {}, {}, {}, {})".format(button.value(), button2.value(), button3.value(), button4.value(), button5.value()))


if __name__ == "__main__":
    init_tft()
    main()
