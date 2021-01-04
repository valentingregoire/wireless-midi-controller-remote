# This example demonstrates a UART periperhal.

import bluetooth
import random
import struct
import time
from ble_advertising import advertising_payload
from machine import Pin

from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("7a47b14d-04c5-440c-b701-c5ed67789dff")
_UART_TX = (
    bluetooth.UUID("588f33e0-4039-4373-a2f5-776a1ff38993"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("53d9bbbd-124c-4425-a506-ed99d7a0b001"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)


class BLEHeadrushRemote:
    def __init__(self, ble, name="Headrush-Commander-Remote"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services(
            (_UART_SERVICE,)
        )
        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback


def create_pin(pin_id: int) -> Pin:
    return Pin(pin_id, Pin.IN, Pin.PULL_UP)


BUTTON_PIN_MAP = {
    "button_rig_up": create_pin(32),
    "button_rig_down": create_pin(33),
    "button_scene1": create_pin(25),
    "button_scene2": create_pin(26),
    "button_scene3": create_pin(27),
    "button_scene4": create_pin(14),
    "button_tap_tempo": create_pin(12),
}


def main():
    ble = bluetooth.BLE()
    remote = BLEHeadrushRemote(ble)
    remote.on_write(lambda message: print(message))

    button_pressed = None
    while True:
        if remote.is_connected():
            for name, button in BUTTON_PIN_MAP.items():
                if not button_pressed == name and button.value() == 0:
                    button_pressed = name
                    print("sending '{name}'.".format(name=name))
                    remote.send(name)
                elif button_pressed == name and button.value() == 1:
                    button_pressed = None


if __name__ == "__main__":
    main()
