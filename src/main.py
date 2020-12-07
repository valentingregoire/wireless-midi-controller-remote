import struct

import bluetooth
from machine import Pin
from micropython import const

from ble_advertising import advertising_payload


def create_pin(pin_id: int) -> Pin:
    return Pin(pin_id, Pin.IN, Pin.PULL_UP)


def bling_led(led: Pin) -> None:
    led.value(1)
    LED_ON = True


# in seconds
LED_BLING_TIME = 1
LED_ON = False


BUTTON_PIN_MAP = {
    # "button_rig_up": create_pin(32),
    # "button_rig_down": create_pin(33),
    # "button_scene1": create_pin(25),
    # "button_scene2": create_pin(26),
    # "button_scene3": create_pin(27),
    # "button_scene4": create_pin(14),
    # "button_tap_tempo": create_pin(12)
    49: create_pin(32),
    55: create_pin(33),
    56: create_pin(25),
    57: create_pin(26),
    58: create_pin(27),
    59: create_pin(14),
    60: create_pin(12),
}

BLUETOOTH_STATUS_LED = Pin(13, Pin.OUT, Pin.PULL_UP)
BLUETOOTH_STATUS_LED.value(0)

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_INDICATE_DONE = const(20)

_FLAG_READ = const(0x0002)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)

_ENV_SENSE_UUID = bluetooth.UUID("7a47b14d-04c5-440c-b701-c5ed67789dff")
_TEMP_CHAR = (
    bluetooth.UUID("588f33e0-4039-4373-a2f5-776a1ff38993"),
    _FLAG_READ | _FLAG_NOTIFY | _FLAG_INDICATE,
)
_ENV_SENSE_SERVICE = (
    _ENV_SENSE_UUID,
    (_TEMP_CHAR,),
)


class BLEHeadrushRemote:
    def __init__(self, ble, name="HCR"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle,),) = self._ble.gatts_register_services((_ENV_SENSE_SERVICE,))
        self._connections = set()
        self._payload = advertising_payload(name=name, services=[_ENV_SENSE_UUID])
        self._advertise()
        BLUETOOTH_STATUS_LED.value(1)

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
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

    button_pressed = None
    while True:
        if remote.is_connected():
            for command, button in BUTTON_PIN_MAP.items():
                if not button_pressed == command and button.value() == 0:
                    button_pressed = command
                    print("sending '{command}'.".format(command=command))
                    remote.send(struct.pack("I", command))
                elif button_pressed == command and button.value() == 1:
                    button_pressed = None


if __name__ == "__main__":
    main()
