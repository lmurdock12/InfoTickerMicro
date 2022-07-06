# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
STATUS_NO_CONNECTION = (100, 0, 0)
STATUS_CONNECTING = (0, 0, 100)
STATUS_FETCHING = (200, 100, 0)
STATUS_DOWNLOADING = (0, 100, 100)
STATUS_CONNECTED = (0, 100, 0)
STATUS_DATA_RECEIVED = (0, 0, 100)
STATUS_OFF = (0, 0, 0)

import board
import time
import gc
from src.NetworkManager import HotSpotHandler
from src.ota_updater import OTAUpdater
from adafruit_matrixportal.network import Network
# Get wifi details and more from a secrets.py file
import json
from secrets import secrets

from digitalio import DigitalInOut, Pull
from adafruit_debouncer import Debouncer


#secrets_data

#Read the conn.json file for the current connection
secrets = None
try:

    with open("src/conn.json","r") as conn_list:
        print("opened the conn file")
        secrets = json.load(conn_list)
        print("Loaded:")
        print(secrets)
        # for ssid,pass_dict in potential_connections["ssids"].items():
        #     print(f"SSID: {ssid}, Pass: {pass_dict['pass']}")

except OSError as e:
    #If we get this error we were unable to open the conn.txt file so just move on to access point creation and try recreating the conn.txt file
    print("ERROR oppening conn.txt file")
    print("Error:",e)


#Attempt initial connection
net = Network(status_neopixel=board.NEOPIXEL)
print("Currently stored secrets:",secrets)
for test in net._wifi.esp.get_scan_networks():
    print("SSID: ",test["ssid"], "RSSI:", test["rssi"])

wifi_manager = net._wifi.manager(secrets)
#wifi_manager.connect_normal() #Will infinietly try to connect
#net.connect() #Will only connect through the secrets.py file


net._wifi.neo_status(STATUS_CONNECTING)
attempt = 1
max_attempts = 5
while not net._wifi.is_connected:
    print("Connecting to AP", secrets["ssid"])
    net._wifi.neo_status(STATUS_NO_CONNECTION)
    try:
        net._wifi.connect(secrets["ssid"], secrets["password"])
        net.requests = net._wifi.requests
        break

    except (RuntimeError, ConnectionError) as error:
        if max_attempts is not None and attempt >= max_attempts:
            break
        print("Could not connect to internet", error)
        print("Retrying in 3 seconds...")
        attempt += 1
        time.sleep(1.5)
    gc.collect()


if not net._wifi.is_connected:
    print("Starting up the Wifi manager since we could not connect to the network")
    #del wifi_manager
    wifi_manager.ssid = "My ESP!"
    wifi_manager.password = None

    hotspot = HotSpotHandler(wifi_manager)
    hotspot.run_wifi_server()


else:
    
    net._wifi.neo_status(STATUS_CONNECTED)
    print("Successfully connected! Have fun")
    

print(net._wifi.is_connected)


print("Connected to", str(net._wifi.esp.ssid, "utf-8"), "\tRSSI:", net._wifi.esp.rssi)
print("My IP address is", net._wifi.esp.pretty_ip(net._wifi.esp.ip_address))
print(
    "IP lookup adafruit.com: %s" % net._wifi.esp.pretty_ip(net._wifi.esp.get_host_by_name("adafruit.com"))
)
print("Ping google.com: %d ms" % net._wifi.esp.ping("google.com"))

gitRepo = "https://github.com/lmurdock12/InfoTickerMicro"
otaUpdater = OTAUpdater(gitRepo,net,main_dir="src")
gc.collect()
otaUpdater2 = OTAUpdater(gitRepo,net,main_dir="lib",new_version_dir="nextlib")


# print("get version check: ")
# getVersion = otaUpdater.get_version("src")
# print("The version is: ", getVersion)

# print("get latest version check")
# otaUpdater.get_latest_version()

# print("check for new version check")
# otaUpdater._check_for_new_version()

pin_down = DigitalInOut(board.BUTTON_DOWN)
pin_down.switch_to_input(pull=Pull.UP)
button_down = Debouncer(pin_down)
pin_up = DigitalInOut(board.BUTTON_UP)
pin_up.switch_to_input(pull=Pull.UP)
button_up = Debouncer(pin_up)

print("starting cycle")
while True:
    button_up.update()
    button_down.update()

    if button_up.fell:
        gc.collect()
        otaUpdater.install_update_if_available()
        gc.collect()
        print("installing the libs now")
        otaUpdater2.install_update_if_available()
        gc.collect()
    if button_down.fell:
        break

print("Goodbye")

# print("---------------removal time----------")
# print(otaUpdater._exists_dir("next"))
# otaUpdater._rmtree("next")
# print("----------after removal----------------")
# print(otaUpdater._exists_dir("next"))