import bluetooth
from ble_advertising import advertising_payload
from machine import Pin
from micropython import const


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

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("5c47e665-6580-4a15-91ea-02caea0ae4a7")
_UART_TX = (
    bluetooth.UUID("9138f9c0-9427-4299-85f3-7aa97b0d0c46"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("7a47b14d-04c5-440c-b701-c5ed67789dff"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

BLE = bluetooth.BLE()
BLE.active(True)
BLE.gatts_register_services((_UART_SERVICE,))
payload = advertising_payload(name="remote", services=[_UART_UUID])


def ble_handler(event: int, data) -> None:
    print("Event: {event}, data: {data}".format(event=event, data=data))


# def init_ble() -> None:
#     ble = bluetooth.BLE()
#     ble.active(True)
#     # ble.irq(ble_handler)
#     ble.gap_connect()


def main() -> None:
    button_pressed = None
    # init_ble()

    while True:
        for name, button in BUTTON_PIN_MAP.items():
            if not button_pressed == name and button.value() == 0:
                button_pressed = name
                print("button {name} is pressed.".format(name=name))
                # BLE.gap_advertise(None, adv_data=payload)
                BLE.gatts_notify()
            elif button_pressed == name and button.value() == 1:
                button_pressed = None


main()
