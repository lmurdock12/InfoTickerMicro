# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT


import board

from src.NetworkManager import NetworkManager
from src.ota_updater import OTAUpdater
from adafruit_matrixportal.network import Network
# Get wifi details and more from a secrets.py file

from secrets import secrets



net = Network(status_neopixel=board.NEOPIXEL)

print("Currently stored secrets:",secrets)
for test in net._wifi.esp.get_scan_networks():
    print("SSID: ",test["ssid"], "RSSI:", test["rssi"])

net.connect()
print(net._wifi.is_connected)


print("Connected to", str(net._wifi.esp.ssid, "utf-8"), "\tRSSI:", net._wifi.esp.rssi)
print("My IP address is", net._wifi.esp.pretty_ip(net._wifi.esp.ip_address))
print(
    "IP lookup adafruit.com: %s" % net._wifi.esp.pretty_ip(net._wifi.esp.get_host_by_name("adafruit.com"))
)
print("Ping google.com: %d ms" % net._wifi.esp.ping("google.com"))

gitRepo = "https://github.com/lmurdock12/InfoTickerMicro"
otaUpdater = OTAUpdater(gitRepo,net,main_dir="src")

# print("get version check: ")
# getVersion = otaUpdater.get_version("src")
# print("The version is: ", getVersion)

# print("get latest version check")
# otaUpdater.get_latest_version()

# print("check for new version check")
# otaUpdater._check_for_new_version()


#otaUpdater.install_update_if_available()

# print("---------------removal time----------")
# print(otaUpdater._exists_dir("next"))
# otaUpdater._rmtree("next")
# print("----------after removal----------------")
# print(otaUpdater._exists_dir("next"))