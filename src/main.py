import _thread

import bluetooth
from machine import ADC
from machine import Pin
import machine
from micropython import const
from network import WLAN
from utime import sleep_ms
import esp32

from ble_advertising import advertising_payload

WLAN(0).active(False)
WLAN(1).active(False)

machine.freq(240000000)


def _create_pin_in(pin_id: int) -> Pin:
    return Pin(pin_id, Pin.IN, Pin.PULL_UP)


# in seconds
_LED_BLING_TIME = 1
_LED_ON = False
_CURRENT_PATCH = 1


_BUTTON_PIN_MAP = {
    "button_rig_up": _create_pin_in(32),
    "button_rig_down": _create_pin_in(33),
    "button_scene1": _create_pin_in(25),
    "button_scene2": _create_pin_in(26),
    "button_scene3": _create_pin_in(27),
    "button_scene4": _create_pin_in(14),
    # "button_tap_tempo": create_pin(12)
}

_BUTTON_POT = _create_pin_in(12)
_POT = ADC(Pin(35))
_POT.atten(ADC.ATTN_11DB)
_LED_POT_STATUS = Pin(19, Pin.OUT, Pin.PULL_UP)
_LED_POT_STATUS.value(1)

_BUTTON_HALL_SENSOR = _create_pin_in(22)
# _BUTTON_HALL_SENSOR.value(1)
_LED_HALL_SENSOR = Pin(23, Pin.OUT, Pin.PULL_UP)
_LED_HALL_SENSOR.value(1)

_STATUS_LED = Pin(13, Pin.OUT, Pin.PULL_UP)
_STATUS_LED.value(0)


def __blink_led(status=1, times=1, interval=150) -> None:
    """
    Blinks the status led.
    :param status:
        1: blue
        2: green
        3: orange
        4: red
    :return:
    """

    for _ in range(times):
        _STATUS_LED.value(1)
        sleep_ms(interval)
        _STATUS_LED.value(0)
        sleep_ms(75)


def blink_led(status=1, times=1, interval=100) -> None:
    _thread.start_new_thread(__blink_led, (status, times, interval))
    # __blink_led(status)


_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_INDICATE_DONE = const(20)

_FLAG_READ = const(0x0002)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)

_REMOTE_UUID = bluetooth.UUID("7a47b14d-04c5-440c-b701-c5ed67789dff")
_REMOTE_CHAR = (
    bluetooth.UUID("588f33e0-4039-4373-a2f5-776a1ff38993"),
    _FLAG_READ | _FLAG_NOTIFY | _FLAG_INDICATE,
)
_REMOTE_SERVICE = (
    _REMOTE_UUID,
    (_REMOTE_CHAR,),
)


class BLEHeadrushRemote:
    def __init__(self, ble, name="HCR"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle,),) = self._ble.gatts_register_services((_REMOTE_SERVICE,))
        self._connections = set()
        self._payload = advertising_payload(name=name, services=[_REMOTE_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            blink_led(1, 4)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_INDICATE_DONE:
            conn_handle, value_handle, status = data

    # def connect(self, address_type=None, address=None, callback=None):
    #     self._ble.gap_connect(address_type, address)

    def is_connected(self):
        return len(self._connections) > 0

    def send(self, command):
        # Write the local value, ready for a central to read.
        self._ble.gatts_write(self._handle, command)
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle)

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)


def main():
    ble = bluetooth.BLE()
    remote = BLEHeadrushRemote(ble)

    previous_pot_value = -1
    button_down = None
    button_hall_sensor = False
    button_hall_sensor_down = False
    button_pot = False
    button_pot_down = False
    while True:
        if remote.is_connected():
            # foot switches
            for command, button in _BUTTON_PIN_MAP.items():
                if not button_down == command and button.value() == 0:
                    button_down = command
                    print("sending '{command}'.".format(command=command))
                    # remote.send(struct.pack("I", command))
                    remote.send(command)
                    blink_led(2)
                    break
                elif button_down == command and button.value() == 1:
                    button_down = None

            # POT
            if _BUTTON_POT.value() == 0 and not button_pot_down:
                button_pot = not button_pot
                button_pot_down = True
            elif _BUTTON_POT.value() == 1 and button_pot_down:
                button_pot_down = False
            if button_pot:
                pot_value = int(_POT.read() / 32)
                if previous_pot_value not in [pot_value - 1, pot_value, pot_value + 1]:
                    # wheels: 61, 62, 63
                    number = 61
                    previous_pot_value = pot_value
                    remote.send("POT|{}|{}".format(number, pot_value))
                if _LED_POT_STATUS.value() == 0:
                    _LED_POT_STATUS.value(1)
            else:
                if _LED_POT_STATUS.value() == 1:
                    _LED_POT_STATUS.value(0)

            # Hall sensor
            if _BUTTON_HALL_SENSOR.value() == 0 and not button_hall_sensor_down:
                button_hall_sensor = not button_hall_sensor
                button_hall_sensor_down = True
            elif _BUTTON_HALL_SENSOR.value() == 1 and button_hall_sensor_down:
                button_hall_sensor_down = False
            if button_hall_sensor:
                hall_vallue = esp32.hall_sensor()
                print(hall_vallue)
                if _LED_HALL_SENSOR.value() == 0:
                    _LED_HALL_SENSOR.value(1)
            else:
                if _LED_HALL_SENSOR.value() == 1:
                    _LED_HALL_SENSOR.value(0)


if __name__ == "__main__":
    main()
