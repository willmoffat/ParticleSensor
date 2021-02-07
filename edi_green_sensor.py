"""Python class for interfacing with an EdiGreen Home Sensor."""

import json
import os
import requests
from requests.auth import HTTPDigestAuth


class EdiGreenSensor:
    """Represents an Edimax EdiGreen Home Sensor."""

    def __init__(self, addr, mac, username="admin", password="1234"):
        if not addr:
            raise ValueError("Missing IP address")
        if not mac:
            raise ValueError("Missing MAC")
        if not username:
            raise ValueError("Missing username")
        if not password:
            raise ValueError("Missing password")
        self.addr = addr
        self.mac = mac
        self.username = username
        self.password = password
        self._log_cmd = False
        self._log_result = False

    def send_cmd(self, cmd):
        """Send command to Edimax and return its response."""
        if self._log_cmd:
            print('debug: cmd=', json.dumps(cmd, indent=2))
        url = "http://{}:5678/edilife.cgi".format(self.addr)
        data = {
            "customer.name": "EDIMAX",
            "mac": self.mac,
            "cmd": cmd,
        }
        response = requests.post(url, data=json.dumps(data),
                                 auth=HTTPDigestAuth(self.username, self.password))
        msg = _rotate_json(response.content)
        # print('Debug: msg={}'.format(msg))
        data = json.loads(msg)
        cmd_result = data['cmd'][1]
        if self._log_result:
            print('debug: cmd_respone=', json.dumps(cmd_result, indent=2))
        return cmd_result

    def set_led(self, led_enable):
        """Set the led on or off."""
        return self.send_cmd([{"id": "set"}, {"feature": {"led.enable": led_enable}}])

    def get_readings(self):
        return self.send_cmd([{"id": "get"}, {"status": {
            "temperature": "0",
            "moisture": 0,
            "pm2.5": 0,
            "pm10": 0,
            "co2": "0",
            "hcho": "0",
            "tvoc": "0",
        }}]).get("status", {})

    def get_all(self):
        return self.send_cmd([{"id": "get"}, {
            "basic": {
                "fwversion": None,
                # Always returns null. TODO(wdm) Is this field name correct?
                "upgrade.status": None,
                "owner.token": None,
                "name": None
            },
            "status": {
                "systemtime": None,
                "temperature": None,
                "moisture": None,
                "pm2.5": None,
                "pm10": None,
                "co2": None,
                "hcho": None,
                "tvoc": None
            },
            "events": {
                "push.enable": None,
                "pm2.5.max": None,
                "pm10.max": None,
                "co2.max": None,
                "hcho.max": None,
                "tvoc.max": None,
                "temperature.min": None,
                "temperature.max": None,
                "moisture.min": None,
                "moisture.max": None
            },
            "feature": {
                "led.enable": None
            }
        }])


# Utility functions:


def _rotate_byte(byte, rotations):
    """Rotate byte to the left by the specified number of rotations."""
    return (byte << rotations | byte >> (8-rotations)) & 0xFF


def _rotate_json(response):
    """Byte rotate the Edimax response into plain JSON."""
    # First byte always decodes to '{' so the difference is the number of rotations.
    rotations = response[0] - ord('{')
    return '{' + ''.join(chr(_rotate_byte(byte, rotations)) for byte in response[1:])

# Testing:


def test():
    """Example invocations."""
    [addr, mac, username, password] = os.environ.get(
        'EDIMAX_CONFIG', ':::').split(':')
    sensor = EdiGreenSensor(addr, mac, username, password)

    print(sensor.get_readings())

    sensor._log_result = True
    sensor.get_all()
    sensor.set_led(1)
    sensor.set_led(0)


if __name__ == '__main__':
    test()
