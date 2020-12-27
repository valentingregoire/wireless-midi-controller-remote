import _thread
import math
import sys
from collections import OrderedDict
from time import sleep

import display
import machine
import network
from machine import ADC
from machine import Pin
from micropython import const
from utime import sleep_ms

# print("deactivating wlan")
# WLAN(0).active(False)
# WLAN(1).active(False)

machine.freq(240000000)


TFT = display.TFT()
# 320 * 240, but in reality x goes from 40 to 279 and y goes from 53 to 187 -> 239 * 134 --> 1.78 ratio instead of 1.33
# --> 240 * 135
TFT.init(TFT.ST7789, rot=TFT.LANDSCAPE_FLIP, miso=17, backl_pin=4, backl_on=1, mosi=19, clk=18, cs=5, dc=16, splash=False)

SERVANT_IP = "192.168.169.1"
SERVANT_PORT = 18788
REMOTE_IP = "192.168.169.2"
REMOTE_PORT = 11686

# configure wifi connectivity
print("Connecting to servant...")


def _print_wifi_status(status: int, strength_status: int = 0) -> None:
    """
    Shows the wifi status in the upper left corner.

    Usable window is (0, 0) -> (15, 21)
    :param status: status of the wifi:
        0. not connected
        1. connecting
        2. connected
        3. sending message
    :param strength_status: the status of the WIFI signal strength:
        1: superior
        2: very good
        3: ok
        4: not that good
        5: unusable
    :return: None
    """

    TFT.rect(0, 0, 15, 21, COLOR_BG, COLOR_BG)
    # color_disabled = 0xA1FFA1
    if status == 0:
        # color = 0xDC7684
        color = TFT.RED
    elif status == 1:
        color = TFT.YELLOW
    elif status == 2:
        color = TFT.GREEN
    else:
        color = TFT.WHITE

    # for i in range(3):
    #     if status == 2:
    #         color = TFT.GREEN if i + strength_status >= 6 else color_disabled
    #     TFT.arc(15, 20, 20 - i * 6, 3, -45, 45, color, color)
    # TFT.circle(15, 21, 2, color, color)

    TFT.arc(15, 20, 20, 3, -45, 45, color, color)
    TFT.arc(15, 20, 14, 3, -45, 45, color, color)
    TFT.arc(15, 20, 8, 3, -45, 45, color, color)
    TFT.circle(15, 21, 2, color, color)


def wifi_callback(data) -> None:
    if data[0] == 4:
        # connected
        _print_wifi_status(2)
    elif data[0] == 5:
        # disconnected
        _print_wifi_status(0)

    print("Wifi callback data {}".format(data))


network.WLANcallback(wifi_callback)
WIFI = network.WLAN(network.STA_IF)
WIFI.ifconfig((REMOTE_IP, '255.255.255.0', '192.168.178.1', '8.8.8.8'))
WIFI.active(True)
WIFI.connect("Headrush Servant", "dunnolol")


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
    b"button_scene4": _create_pin_in(15),
}

_BUTTON_POT = _create_pin_in(13)
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


TFT.tft_writecmd(0x21)
TFT.setwin(39, 52, 279, 187)  # 240 * 135
TFT.savewin()
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


def _get_wifi_signal_strength() -> int:
    if WIFI.isconnected():
        # rssi = WIFI.status("stations")
        networks = WIFI.scan(True)
        rssi = None
        for network in networks:
            if network[1] == b'\x8c\xaa\xb5\xb5\x9fe':
                rssi = network[3]
        print("rssi: {}".format(rssi))
        if rssi >= -30:
            return 1
        elif rssi >= -67:
            return 2
        elif rssi >= -70:
            return 3
        elif rssi >= -80:
            return 4
        else:
            return 5
    else:
        return 0


def _update_wifi_status() -> None:
    while True:
        rssi_status = _get_wifi_signal_strength()
        if rssi_status >= 0:
            _print_wifi_status(2, rssi_status)
            sleep(5)


def poll_wifi_status() -> None:
    _thread.start_new_thread("Update Wi-Fi status", _update_wifi_status, ())


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


def configure_socket():
    while not WIFI.isconnected():
        print("Waiting for connection with servant.")
        sleep_ms(100)

    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.bind(("192.168.169.1", 10086))
    sock.sendto(b"Remote connected!", (SERVANT_IP, SERVANT_PORT))

    _print_wifi_status(2, 1)

    return sock

ARROW_SIDE = WINDOW_SPLIT_X_1 - MARGIN * 2
ARROW_X1 = WINDOW_SPLIT_X_1 + MARGIN
ARROW_X3 = WINDOW_SPLIT_X_2 - MARGIN
ARROW_X2 = int((ARROW_X3 - ARROW_X1) / 2 + ARROW_X1)
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
    sock = configure_socket()
    reset_switches()

    # print("in main")
    rig = 1
    print_rig_number(rig)
    button_down = None
    while True:
        # foot switches
        if _BUTTON_POT.value() == 0:
            print("POT pressed")
        else:
            for command, button in _BUTTON_PIN_MAP.items():
                if not button_down == command and button.value() == 0:
                    print("{} pressed".format(command))
                    button_down = command
                    # print("sending '{command}'.".format(command=command))
                    if command in [b"button_rig_up", b"button_rig_down"]:
                        if command == b"button_rig_up":
                            rig += 1
                        elif command == b"button_rig_down":
                            rig -= 1
                            sys.exit()

                        print_rig_number(rig)
                    # remote.send(struct.pack("I", command))
                    # remote.send(command)

                    sock.sendto(command, (SERVANT_IP, SERVANT_PORT))

                    break
                elif button_down == command and button.value() == 1:
                    button_down = None

        # print("({}, {}, {}, {}, {})".format(button.value(), button2.value(), button3.value(), button4.value(), button5.value()))


if __name__ == "__main__":
    init_tft()
    # poll_wifi_status()
    main()
