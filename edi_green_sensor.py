"""Python class for interfacing with an EdiGreen Home Sensor."""

from socket import *
import json
import os
import requests
from requests.auth import HTTPDigestAuth


class EdiGreenSensor:
    """Represents an Edimax EdiGreen Home Sensor."""

    def __init__(self, addr, mac, name="EdiMax", username="admin", password="1234"):
        if not addr:
            raise ValueError("Missing IP address")
        if not mac:
            raise ValueError("Missing MAC")
        if not name:
            raise ValueError("Missing name")
        if not username:
            raise ValueError("Missing username")
        if not password:
            raise ValueError("Missing password")
        self.addr = addr
        self.mac = mac
        self.name = name
        self.username = username
        self.password = password
        self._log_request = False
        self._log_response = False

    def __str__(self) -> str:
        return "[EdiGreenSensor: {} {} {}]".format(self.name, self.addr, self.mac)

    @staticmethod
    def search(password):
        # Create a UDP socket
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        sock.settimeout(5)

        # TODO(wdm) What are these magic bytes?
        payload = bytes.fromhex('ff ff ff ff ff ff 00 02 ff fd 00 00 00 00')

        try:
            sent = sock.sendto(payload, ('255.255.255.255', 24929))
            print('Searching for EdiMax sensor...')
            data, _ = sock.recvfrom(4096)
            mac = data[0:6].hex().upper()
            # TODO(wdm) What is this? data[6:10] == b'\x01\x02\xfe\xfd'
            # uid = mac + data[10:14]
            search = json.loads(data[14:])
            # print('Debug', search)
            sensor = EdiGreenSensor(search.get('search.ip'), mac, search.get(
                'search.name'), 'admin', password)
            if sensor:
                print('Found: ', sensor)
            return sensor
        except Exception as err:
            print(err)
        finally:
            sock.close()

    def send_cmd(self, cmd):
        """Send command to Edimax and return its response."""
        url = "http://{}:5678/edilife.cgi".format(self.addr)
        data = {
            "customer.name": "EDIMAX",
            "mac": self.mac,
            "cmd": cmd,
            "uid": None,  # Ignored?
        }
        if self._log_request:
            print('debug: url={} data={}'.format(url, data))

        response = requests.post(url, data=json.dumps(data),
                                 auth=HTTPDigestAuth(self.username, self.password))
        msg = _rotate_json(response.content)
        # print('Debug: msg={}'.format(msg))
        data = json.loads(msg)
        if self._log_response:
            print('debug: cmd_respone=', json.dumps(data, indent=2))
        return data['cmd'][1]

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
                "mac": None,
                "model": None,
                "name.maxlen": None,
                "name": None,
                "owner.token": None,
                "produce.country.code": None,
                "protocolversion": None,
                "uploaddata.enable": None,

                "cloud.ddns.domain": None,
                "cloud.ddns.port": None,
                "cloud.push.domain": None,
                "cloud.push.port": None,
                "cloud.ota.domain": None,
                "cloud.ota.port": None,
                "cloud.upload.domain": None,
                "cloud.upload.port": None,
                "cloud.upload.cert": None,
                # TODO(wdm) Any other fields?

                # These fields return null:
                "cloud.push.cert": None,
                "cloud.ota.cert": None,
                "cloud.upload.cert": None,
                "cgiversion": None,
                "model.id": None,
                "upgrade.status": None,
            },
            "network": {
                "http.port": None,
                "ip.type": None,
                "ip.dhcp.ip": None,
                "ip.static.ip": None,
                "ip.static.netmask": None,
                "ip.static.gateway": None,
                "ip.static.dns1": None,
                "wifi.check": None,
                "wifi.mode": None,

                # This field return values:
                "wifi.ssid": None,
                "wifi.auth": None,
                "wifi.encryption": None,
                "wifi.wpakey": None,

                "wifi.bssid": None,
                "wifi.channel": None,

                "wifi.wepkeyIndex": None,
                "wifi.wepkeyformat": None,
                "wifi.wepkeylength": None,
                "wifi.wepkey1": None,
                "wifi.wepkey2": None,
                "wifi.wepkey3": None,
                "wifi.wepkey4": None,
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
    password = os.environ.get('EDIMAX_PASSWORD')
    if not password:
        print('Please set environemt variable EDIMAX_PASSWORD')
        exit(1)

    sensor = EdiGreenSensor.search(password)
    if not sensor:
        print('Failed to find a EdiMax sensor')
        exit(1)
    print(sensor.get_readings())

    sensor._log_response = True
    sensor._log_request = True
    # sensor.get_all()
    sensor.set_led(1)
    sensor.set_led(0)


if __name__ == '__main__':
    test()
