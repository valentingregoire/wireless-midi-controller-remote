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

# WLAN(0).active(False)
# WLAN(1).active(False)

machine.freq(240000000)


TFT = display.TFT()
# 320 * 240, but in reality x goes from 40 to 279 and y goes from 53 to 187 -> 239 * 134 --> 1.78 ratio instead of 1.33
# --> 240 * 135
TFT.init(TFT.ST7789, rot=TFT.LANDSCAPE_FLIP, miso=17, backl_pin=4, backl_on=1, mosi=19, clk=18, cs=5, dc=16, splash=False)
TFT.tft_writecmd(0x21)
TFT.setwin(39, 52, 279, 187)  # 240 * 135
TFT.savewin()
WINDOW_SIZE = TFT.winsize()
WINDOW_SPLIT_X_1 = int(WINDOW_SIZE[0] / 3)
WINDOW_SPLIT_X_2 = int(WINDOW_SPLIT_X_1 * 2)
WINDOW_SPLIT_Y = int(WINDOW_SIZE[1] / 2)
WINDOW_SPLIT_Y_3_4 = int(WINDOW_SIZE[1] / 4 * 3)

MARGIN = const(6)
MARGIN_HALF = const(3)

COLOR_OFF = const(0x551100)
COLOR_ON = const(0xDDAA00)
COLOR_BG = TFT.BLACK

SWITCH_SPACE_WIDTH = int(WINDOW_SIZE[0] / 4)
SWITCH_HALF_SPACE_WIDTH = int(SWITCH_SPACE_WIDTH / 2)
SWITCH_Y = WINDOW_SPLIT_Y_3_4
SWITCH_R = SWITCH_HALF_SPACE_WIDTH - MARGIN

RIG_WIDTH = WINDOW_SPLIT_X_1
RIG_HEIGHT = WINDOW_SPLIT_Y
RIG_X_START = WINDOW_SIZE[0] - RIG_WIDTH
RIG_Y_START = 0


TEXT_X = int(WINDOW_SIZE[0] / 2)
TEXT_Y = int(WINDOW_SPLIT_Y / 2)


def set_normal_font():
    TFT.font(TFT.FONT_Ubuntu)


def print_text(text: str) -> None:
    set_normal_font()
    # text_width = TFT.textWidth(text)
    TFT.rect(0, 22, RIG_X_START, WINDOW_SPLIT_Y - 22, COLOR_BG, COLOR_BG)
    TFT.text(10, TEXT_Y, text)


print_text("Loading ...")


SERVANT_IP = "192.168.169.1"
SERVANT_PORT = 18788
REMOTE_IP = "192.168.169.2"
REMOTE_PORT = 11686
_WIFI_STRENGTH = 0


def _print_wifi_status(status: int) -> None:
    """
    Shows the wifi status in the upper left corner.

    Usable window is (0, 0) -> (15, 21)
    :param status: status of the wifi:
        0. not connected
        1. connecting
        2. connected
        3. sending message
    :param _WIFI_STRENGTH: the WIFI signal strength:
        1: unusable
        2: not that good
        3: ok
        4: very good
        5: superior
    :return: None
    """

    TFT.rect(0, 0, 15, 21, COLOR_BG, COLOR_BG)
    if status == 0:
        color = 0xAA0000
    elif status == 1:
        color = 0xCCCC00
    elif status == 2:
        color = 0x00AA00
    else:
        color = TFT.WHITE

    color_green_greyed = 0x003300

    for i in range(3):
        color_arc = color if _WIFI_STRENGTH == 0 or (i + 3) <= _WIFI_STRENGTH else color_green_greyed
        # print("i: {} - {} - {}".format(i, _WIFI_STRENGTH, color_arc))
        TFT.arc(15, 20, 8 + i * 6, 3, -45, 45, color_arc, color_arc)
    color_dot = color_green_greyed if status == 2 and _WIFI_STRENGTH == 1 else color
    TFT.circle(15, 21, 2, color_dot, color_dot)


def _create_pin_in(pin_id: int) -> Pin:
    return Pin(pin_id, Pin.IN, Pin.PULL_UP)


_BUTTON_SCENE1 = b"button_scene1"
_BUTTON_SCENE2 = b"button_scene2"
_BUTTON_SCENE3 = b"button_scene3"
_BUTTON_SCENE4 = b"button_scene4"
_BUTTON_RIG_UP = b"button_rig_up"
_BUTTON_RIG_DOWN = b"button_rig_down"


_BUTTON_PIN_MAP = OrderedDict()
_BUTTON_PIN_MAP[_BUTTON_SCENE1] = _create_pin_in(2)
_BUTTON_PIN_MAP[_BUTTON_SCENE2] = _create_pin_in(25)
_BUTTON_PIN_MAP[_BUTTON_SCENE3] = _create_pin_in(13)
_BUTTON_PIN_MAP[_BUTTON_SCENE4] = _create_pin_in(12)
_BUTTON_PIN_MAP[_BUTTON_RIG_UP] = _create_pin_in(32)
_BUTTON_PIN_MAP[_BUTTON_RIG_DOWN] = _create_pin_in(33)

_BUTTON_REPL = Pin(35, Pin.IN)
# _BUTTON_WIFI_STATUS = Pin(0, Pin.IN)

# _BUTTON_POT = _create_pin_in(13)
# _POT = ADC(Pin(35))
# _POT.atten(ADC.ATTN_11DB)


SWITCH_STATUS = OrderedDict()


def set_switch_status(switch_active):
    counter = 0
    if switch_active in [_BUTTON_RIG_UP, _BUTTON_RIG_DOWN]:
        switch_active = _BUTTON_SCENE1
    for key in _BUTTON_PIN_MAP.keys():
        SWITCH_STATUS[key] = {"pos": counter, "value": switch_active == key}
        counter += 1


# SWITCH_STATUS[b"POT"] = (6, 0)
WIFI = network.WLAN(network.STA_IF)
WIFI.ifconfig((REMOTE_IP, '255.255.255.0', '192.168.178.1', '8.8.8.8'))
WIFI.active(True)
WIFI.connect("Headrush Servant", "dunnolol")


def _get_wifi_signal_strength() -> None:
    if WIFI.isconnected():
        # rssi = WIFI.status("stations")
        networks = WIFI.scan(True)
        rssi = None
        for net in networks:
            # print("\t{}".format(net))
            if net[1] == b'\x8c\xaa\xb5\xb5\x9fe':
                rssi = net[3]
        # print("rssi: {}".format(rssi))
        global _WIFI_STRENGTH
        if rssi >= -30:
            _WIFI_STRENGTH = 5
        elif rssi >= -67:
            _WIFI_STRENGTH = 4
        elif rssi >= -70:
            _WIFI_STRENGTH = 3
        elif rssi >= -80:
            _WIFI_STRENGTH = 2
        else:
            _WIFI_STRENGTH = 1
    else:
        _WIFI_STRENGTH = 0


def _update_wifi_status() -> None:
    if _WIFI_STRENGTH == 0:
        _get_wifi_signal_strength()
    _print_wifi_status(2)


def wifi_callback(data) -> None:
    if data[0] == 4:
        # connected
        print_text("Connected")
        _update_wifi_status()
    elif data[0] == 5:
        # disconnected
        print_text("Disconnected")
        _print_wifi_status(0)


network.WLANcallback(wifi_callback)


def map_switch_status_to_color(value: float) -> hex:
    # map values between 0 and 1 to gradually go from COLOR_OFF to COLOR_ON
    if value == 1:
        return COLOR_ON
    else:
        return COLOR_OFF


def clear_background():
    # print("rendering background")
    # set black background
    # TFT.rect(0, 0, SCREEN_SIZE[0], SCREEN_SIZE[1], fillcolor=TFT.WHITE)
    TFT.clear(TFT.BLACK)


def set_segment_font(color=COLOR_ON):
    TFT.font(TFT.FONT_7seg)
    TFT.attrib7seg(12, 12, color, color)


def init_tft() -> None:
    # print("init tft")
    set_segment_font()
    clear_background()

    # set front and back colors so segment font is printed properly
    TFT.set_bg(COLOR_BG)
    TFT.set_fg(COLOR_ON)


def draw_switch(switch: bytes) -> None:
    pos_value = SWITCH_STATUS[switch]
    pos = pos_value["pos"]
    value = pos_value["value"]
    # lower row
    color = COLOR_ON if value else COLOR_OFF
    if pos <= 3:
        switch_space_multiplier = SWITCH_SPACE_WIDTH * pos
        TFT.rect(switch_space_multiplier, WINDOW_SPLIT_Y, switch_space_multiplier + SWITCH_SPACE_WIDTH, WINDOW_SIZE[1], COLOR_BG)
        TFT.circle(pos * SWITCH_SPACE_WIDTH + SWITCH_HALF_SPACE_WIDTH, SWITCH_Y, SWITCH_R, color, color)
    # elif pos == 6:
    #     TFT.circle(SWITCH_HALF_SPACE_WIDTH, int(WINDOW_SPLIT_Y / 2), SWITCH_R, color, color)


def reset_switches(switch: bytes) -> None:
    set_switch_status(switch)
    for sw in SWITCH_STATUS:
        # new_value = not sw == switch
        # if not SWITCH_STATUS[sw]["value"] == new_value:
        draw_switch(sw)
        # SWITCH_STATUS[sw]["value"] = new_value


def print_rig_number(rig: int, color=COLOR_ON) -> None:
    set_segment_font(color)
    TFT.rect(RIG_X_START, RIG_Y_START, RIG_WIDTH, RIG_HEIGHT, color=COLOR_BG, fillcolor=COLOR_BG)
    text = str(rig)
    # print("rig {}".format(rig))
    segment_width = int(RIG_WIDTH / 2)
    x = RIG_X_START + ((2 - len(text)) * segment_width)
    y = RIG_Y_START
    TFT.text(x, y, text)


def configure_socket():
    counter = 0
    while not WIFI.isconnected():
        print("Waiting for connection with servant.")
        print_text("Connecting {}".format("." * (counter % 3 + 1)))
        counter += 1
        sleep_ms(250)

    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.bind(("192.168.169.1", 10086))
    sock.sendto(b"Remote connected!", (SERVANT_IP, SERVANT_PORT))

    _update_wifi_status()

    return sock


# ARROW_SIDE = WINDOW_SPLIT_X_1 - MARGIN * 2
# ARROW_X1 = WINDOW_SPLIT_X_1 + MARGIN
# ARROW_X3 = WINDOW_SPLIT_X_2 - MARGIN
# ARROW_X2 = int((ARROW_X3 - ARROW_X1) / 2 + ARROW_X1)
# ARROW_HEIGHT = int(ARROW_SIDE * math.sqrt(3) / 2)
# ARROW_HEIGHT_2 = int(ARROW_HEIGHT / 2)
# ARROW_Y1 = int((WINDOW_SPLIT_Y - ARROW_HEIGHT) / 2)
# ARROW_Y2 = WINDOW_SPLIT_Y - ARROW_Y1


# def _draw_arrow(up=True) -> None:
#     if up:
#         print(ARROW_X1, ARROW_Y2, ARROW_X2, ARROW_Y1, ARROW_X3, ARROW_Y2, COLOR_ON, COLOR_ON)
#         TFT.triangle(ARROW_X1, ARROW_Y2, ARROW_X2, ARROW_Y1, ARROW_X3, ARROW_Y2, COLOR_ON, COLOR_ON)
#     else:
#         print(ARROW_X1, ARROW_Y1, ARROW_X2, ARROW_Y2, ARROW_X3, ARROW_Y1, COLOR_ON, COLOR_ON)
#         TFT.triangle(ARROW_X1, ARROW_Y1, ARROW_X2, ARROW_Y2, ARROW_X3, ARROW_Y1, COLOR_ON, COLOR_ON)


# def draw_arrow(up = True) -> None:
#     _thread.start_new_thread(__blink_led, (times, interval))


RIG_MIN = const(1)
RIG_MAX = const(99)

# _BUTTON_WIFI_NAME = b"WIFI_STATUS"


def main() -> None:
    sock = configure_socket()
    print_text("")
    # initiate_switch_status()
    reset_switches(_BUTTON_SCENE1)

    rig = RIG_MIN
    print_rig_number(rig)
    print_text("Scene 1 OK")
    button_down = None
    while True:
        send = True
        rig_change = False
        # foot switches
        if _BUTTON_REPL.value() == 0:
            print_text("system exit")
            sys.exit()
        # elif _BUTTON_WIFI_STATUS.value() == 1:
        #     if not button_down == _BUTTON_WIFI_NAME:
        #         print("WIFI button pressed")
        #         button_down = _BUTTON_WIFI_NAME
        #         global _WIFI_STRENGTH
        #         _WIFI_STRENGTH = 0
        #         _update_wifi_status()
        #     elif button_down == _BUTTON_WIFI_NAME and _BUTTON_WIFI_STATUS.value() == 0:
        #         button_down = None
        else:
            for command, button in _BUTTON_PIN_MAP.items():
                if not button_down == command and button.value() == 0:
                    # print("{} pressed".format(command))
                    button_down = command
                    # print("sending '{command}'.".format(command=command))
                    if command in [_BUTTON_RIG_UP, _BUTTON_RIG_DOWN]:
                        if command == _BUTTON_RIG_UP:
                            if rig < RIG_MAX:
                                rig += 1
                                rig_change = True
                            else:
                                send = False
                        elif command == _BUTTON_RIG_DOWN:
                            if rig > RIG_MIN:
                                rig -= 1
                                rig_change = True
                            else:
                                send = False

                    if send:
                        print_rig_number(rig)
                        message = "Rig {}".format(rig) if rig_change else command.replace(b"button_scene", b"Scene ").decode()
                        print_text("{} ...".format(message))
                        sock.sendto(command, (SERVANT_IP, SERVANT_PORT))
                        reset_switches(command)
                        print_text("{} OK".format(message))

                    break
                elif button_down == command and button.value() == 1:
                    button_down = None


if __name__ == "__main__":
    init_tft()
    _print_wifi_status(0)
    main()
