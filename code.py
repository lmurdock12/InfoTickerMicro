# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT


import board

from src.NetworkManager import NetworkManager
from src.ota_updater import OTAUpdater
from adafruit_matrixportal.network import Network
# Get wifi details and more from a secrets.py file

from secrets import secrets

print("Currently stored secrets:",secrets)

net = Network(status_neopixel=board.NEOPIXEL)
net.connect()
print(net._wifi.is_connected)

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"

JSON_GET_URL = "https://api.github.com/repos/adafruit/Adafruit_CircuitPython_MatrixPortal/releases/latest"

res = net.fetch(TEXT_URL)
print(res)
res.close()


res = net.fetch(JSON_GET_URL)
print(res)


res = net.fetch(TEXT_URL)
print(res)


res = net.fetch(JSON_GET_URL)
print(res)

res = net.fetch(TEXT_URL)
print(res)


res = net.fetch(JSON_GET_URL)
print(res)


res = net.fetch(TEXT_URL)
print(res)




# gitRepo = "https://github.com/lmurdock12/InfoTickerMicro"
# otaUpdater = OTAUpdater(gitRepo,net)

# getVersion = otaUpdater.get_version("src")
# print("The version is: ", getVersion)

# try:
#     print("attempting OTA updating: ")
#     otaUpdater.get_latest_version()
# except:
#     print("ERROR")
#     pass
# print("_---------------------------------")
# try:
#     print("attempting OTA updating: ")
#     otaUpdater.get_latest_version()
# except:
#     print("ERROR")
#     pass


print("Success exiting....")
#otaUpdater.get_latest_version()
#otaUpdater.get_latest_version()
#otaUpdater.get_latest_version()
#otaUpdater.get_latest_version()
#otaUpdater.get_latest_version()


# print("ESP32 SPI webclient test")

# try:
#     import json as json_module
# except ImportError:
#     import ujson as json_module

# print("ESP32 SPI simple web server test!")

# status_light = neopixel.NeoPixel(board.NEOPIXEL,1,brightness=0.2)
# netManager = NetworkManager(status_light)
# netManager.read_connections()
# netManager.attempt_connection()

# if netManager.check_connection():
#     print("We are connected to the internet!")



#     gitRepo = "https://github.com/lmurdock12/InfoTickerMicro"
#     otaUpdater = OTAUpdater(gitRepo)

#     getVersion = otaUpdater.get_version("src")
#     print("The version is: ", getVersion)

#     otaUpdater.get_latest_version()
#     otaUpdater.get_latest_version()
#     otaUpdater.get_latest_version()
#     otaUpdater.get_latest_version()
#     otaUpdater.get_latest_version()
#     otaUpdater.get_latest_version()

# else:
#     print(":(")

#     print("Unsuccessful attempt to connect to wifi...creating an access point instead")
#     netManager.run_wifi_server()

