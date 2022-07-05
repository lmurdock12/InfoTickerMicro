# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT


import board
import neopixel
import adafruit_requests as requests
from src.NetworkManager import NetworkManager
from src.ota_updater import OTAUpdater
# Get wifi details and more from a secrets.py file
# try:
#     from src.secrets import secrets
# except ImportError:
#     print("WiFi secrets are kept in secrets.py, please add them there!")
#     raise

print("ESP32 SPI webclient test")

try:
    import json as json_module
except ImportError:
    import ujson as json_module

print("ESP32 SPI simple web server test!")

status_light = neopixel.NeoPixel(board.NEOPIXEL,1,brightness=0.2)
netManager = NetworkManager(status_light)
netManager.read_connections()
netManager.attempt_connection()

if netManager.check_connection():
    print("We are connected to the internet!")



    gitRepo = "https://github.com/lmurdock12/InfoTickerMicro"
    otaUpdater = OTAUpdater(gitRepo)

    getVersion = otaUpdater.get_version("src")
    print("The version is: ", getVersion)

    otaUpdater.get_latest_version()
    otaUpdater.get_latest_version()
    otaUpdater.get_latest_version()
    otaUpdater.get_latest_version()
    otaUpdater.get_latest_version()
    otaUpdater.get_latest_version()

else:
    print(":(")

    print("Unsuccessful attempt to connect to wifi...creating an access point instead")
    netManager.run_wifi_server()

