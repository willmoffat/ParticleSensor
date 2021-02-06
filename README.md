# ParticleSensor

Interface with EdiMax EdiGreen Home particle sensor

### To get data from EdiMax EdiGreen AI-2002W:

You'll need the IP and MAC address of your sensor from your WiFi router.
You also need the password you chose when setting up your sensor.

For example:

```sh
EDIMAX_CONFIG='192.168.1.228:08BEAC0CF6FA:admin:XXXX' python ./edi_green_sensor.py
```

Output:

```sh
{'status': {'temperature': '21.8', 'moisture': 48, 'pm2.5': 20, 'pm10': 20, 'co2': '449', 'hcho': '0', 'tvoc': '147'}}
```

The ring LEDs should also turn on and off.
