import display
import machine
from machine import Pin
from micropython import const
import network
from utime import sleep_ms
from microWebSrv import MicroWebSrv

# print("deactivating wlan")
# WLAN(0).active(False)
# WLAN(1).active(False)

machine.freq(240000000)

# configure wifi connectivity
print("Connecting to servant...")
WIFI = network.WLAN(network.STA_IF)
WIFI.active(True)
WIFI.connect("Headrush Servant")


def _create_pin_in(pin_id: int) -> Pin:
    return Pin(pin_id, Pin.IN, Pin.PULL_UP)

COLOR_OFF = const(0xCCCCCC)
COLOR_ON = const(0xFFC117)

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


TFT = display.TFT()
# 240 * 320
TFT.init(TFT.ST7789, bgr=True, rot=TFT.LANDSCAPE_FLIP, miso=17, backl_pin=4, backl_on=1, mosi=19, clk=18, cs=5, dc=16, splash=False)
# # rig window
# TFT.setwin(180, 0, 140, 70)
# TFT.savewin()
# TFT.resetwin()
SCREEN_SIZE = TFT.screensize()
print(SCREEN_SIZE)

RIG_WIDTH = 120
RIG_HEIGHT = 100
RIG_X_START = SCREEN_SIZE[0] - RIG_WIDTH
RIG_Y_START = 0


def render_background():
    print("rendering background")
    # set black background
    TFT.rect(0, 0, 320, 240, fillcolor=TFT.WHITE)


def init_tft() -> None:
    print("init tft")

    # 240 * 320
    TFT.font(TFT.FONT_7seg)
    TFT.attrib7seg(12, 12, COLOR_ON, COLOR_ON)

    # set black background
    TFT.rect(0, 0, SCREEN_SIZE[0], SCREEN_SIZE[1], fillcolor=TFT.WHITE)

    # set front and back colors so segment font is printed properly
    TFT.set_bg(TFT.WHITE)
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


def draw_switches() -> None:
    TFT.circle(20, 20, 20, fillcolor=COLOR_OFF)
    # print("drawing switches")
    # switches = 5
    # space_width = int(SCREEN_SIZE[0] / (switches + 1))
    # print(space_width)
    # half_space_width = int(space_width / 2)
    # print(half_space_width)
    # y = int(SCREEN_SIZE[1] / 4 * 3)
    # for i in range(switches):
    #     x = i * space_width + half_space_width
    #     print("circle : {}, {}".format(x, y))
    #     TFT.circle(x, y, half_space_width - 6, color=COLOR_OFF, fillcolor=COLOR_OFF)



def print_rig_number(rig: int) -> None:
    # print("printing rig number")
    TFT.rect(RIG_X_START, RIG_Y_START, RIG_WIDTH, 120, color=TFT.WHITE, fillcolor=TFT.WHITE)
    text = str(rig)
    print("rig {}".format(rig))
    segment_width = 40
    # x = 280 - len(text) * 40
    x = SCREEN_SIZE[0] - segment_width * (len(text) + 1)
    # y = 50
    y = int(RIG_HEIGHT / 2)
    TFT.text(x, y, text)


def configure_socket():
    while not WIFI.isconnected():
        print("Waiting for connection with servant.")
        sleep_ms(150)

    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.bind(("192.168.4.1", 10086))
    sock.sendto(b"this is just a simple string...", ("192.168.4.1", 10086))

    return sock


def main() -> None:
    sock = configure_socket()
    draw_switches()
    print("in main")
    rig = 1
    button_down = None
    counter = 0
    while counter < 100:
        if True:
        # if remote.is_connected():
            # foot switches
            for command, button in _BUTTON_PIN_MAP.items():
                if not button_down == command and button.value() == 0:
                    print("{} pressed".format(command))
                    button_down = command
                    print("sending '{command}'.".format(command=command))
                    if command in [b"button_rig_up", b"button_rig_down"]:
                        if command == b"button_rig_up":
                            rig += 1
                        elif command == b"button_rig_down":
                            rig -= 1

                        print_rig_number(rig)
                    # remote.send(struct.pack("I", command))
                    # remote.send(command)
                    sock.sendto(command, ("192.168.4.1", 10086))
                    # blink_led(2)

                    break
                elif button_down == command and button.value() == 1:
                    button_down = None

            counter += 1
            print(counter)
            sleep_ms(100)


        # print("({}, {}, {}, {}, {})".format(button.value(), button2.value(), button3.value(), button4.value(), button5.value()))


if __name__ == "__main__":
    init_tft()
    main()
