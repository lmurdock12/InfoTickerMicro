import os
import board
import busio
import json
import supervisor

from digitalio import DigitalInOut
import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_esp32spi.adafruit_esp32spi_wifimanager as wifimanager
import adafruit_esp32spi.adafruit_esp32spi_wsgiserver as server
from adafruit_esp32spi import adafruit_esp32spi
import neopixel

try:
    import json as json_module
except ImportError:
    import ujson as json_module

class SimpleWSGIApplication:
    """
    An example of a simple WSGI Application that supports
    basic route handling and static asset file serving for common file types
    """

    INDEX = "/index.html"
    CHUNK_SIZE = 8912  # max number of bytes to read at once when reading files

    def __init__(self, static_dir=None, debug=False):
        self._debug = debug
        self._listeners = {}
        self._start_response = None
        self._static = static_dir
        if self._static:
            self._static_files = ["/" + file for file in os.listdir(self._static)]

    def __call__(self, environ, start_response):
        """
        Called whenever the server gets a request.
        The environ dict has details about the request per wsgi specification.
        Call start_response with the response status string and headers as a list of tuples.
        Return a single item list with the item being your response data string.
        """
        if self._debug:
            self._log_environ(environ)

        self._start_response = start_response
        status = ""
        headers = []
        resp_data = []

        key = self._get_listener_key(
            environ["REQUEST_METHOD"].lower(), environ["PATH_INFO"]
        )
        if key in self._listeners:
            status, headers, resp_data = self._listeners[key](environ)
        if environ["REQUEST_METHOD"].lower() == "get" and self._static:
            path = environ["PATH_INFO"]
            if path in self._static_files:
                status, headers, resp_data = self.serve_file(
                    path, directory=self._static
                )
            elif path == "/" and self.INDEX in self._static_files:
                status, headers, resp_data = self.serve_file(
                    self.INDEX, directory=self._static
                )

        self._start_response(status, headers)
        return resp_data

    def on(self, method, path, request_handler):
        """
        Register a Request Handler for a particular HTTP method and path.
        request_handler will be called whenever a matching HTTP request is received.
        request_handler should accept the following args:
            (Dict environ)
        request_handler should return a tuple in the shape of:
            (status, header_list, data_iterable)
        :param str method: the method of the HTTP request
        :param str path: the path of the HTTP request
        :param func request_handler: the function to call
        """
        self._listeners[self._get_listener_key(method, path)] = request_handler

    def serve_file(self, file_path, directory=None):
        status = "200 OK"
        headers = [("Content-Type", self._get_content_type(file_path))]

        full_path = file_path if not directory else directory + file_path

        def resp_iter():
            with open(full_path, "rb") as file:
                while True:
                    chunk = file.read(self.CHUNK_SIZE)
                    if chunk:
                        yield chunk
                    else:
                        break

        return (status, headers, resp_iter())

    def _log_environ(self, environ):  # pylint: disable=no-self-use
        print("environ map:")
        for name, value in environ.items():
            print(name, value)

    def _get_listener_key(self, method, path):  # pylint: disable=no-self-use
        return "{0}|{1}".format(method.lower(), path)

    def _get_content_type(self, file):  # pylint: disable=no-self-use
        ext = file.split(".")[-1]
        if ext in ("html", "htm"):
            return "text/html"
        if ext == "js":
            return "application/javascript"
        if ext == "css":
            return "text/css"
        if ext in ("jpg", "jpeg"):
            return "image/jpeg"
        if ext == "png":
            return "image/png"
        return "text/plain"


class HotSpotHandler:

    def __init__(self,wifi_manager):

        self.wifi_manager = wifi_manager

        static = "src/static"
        try:
            static_files = os.listdir(static)
            if "index.html" not in static_files:
                raise RuntimeError(
                    """
                    This example depends on an index.html, but it isn't present.
                    Please add it to the {0} directory""".format(
                        static
                    )
                )

        except (OSError) as e:
            raise RuntimeError(
                """
                This example depends on a static asset directory.
                Please create one named {0} in the root of the device filesystem.""".format(
                    static
                )
            ) from e
        self.web_app = SimpleWSGIApplication(static_dir="src/static")
        self.web_app.on("GET", "/led_on", self.led_on)
        self.web_app.on("GET", "/led_off", self.led_off)
        self.web_app.on("POST", "/ajax/ledcolor", self.led_color)
        self.web_app.on("GET","/ajax/ssids",self.curr_ssids)
        self.web_app.on("POST","/setWifi",self.set_wifi) 

        self.netList = self.scan_networks()   

    def scan_networks(self):

        print("rescanning networks")

        nets = self.wifi_manager.esp.scan_networks()
        networkList  = []
        for net in nets:
            curr_ap_ssid = str(net["ssid"],"utf-8")

            if curr_ap_ssid not in networkList:
                networkList.append(curr_ap_ssid)

        print(networkList)
        return {'ssids':networkList}


    # Our HTTP Request handlers
    def led_on(self,environ):  # pylint: disable=unused-argument
        print("led on!")
        #self.status_light.fill((0, 0, 100))
        return self.web_app.serve_file("src/static/index.html")
    def led_off(self,environ):  # pylint: disable=unused-argument
        print("led off!")
        self.status_light.fill(0)
        return self.web_app.serve_file("static/index.html")
    def led_color(self,environ):  # pylint: disable=unused-argument
        json = json_module.loads(environ["wsgi.input"].getvalue())
        print(json)
        rgb_tuple = (json.get("r"), json.get("g"), json.get("b"))
        self.status_light.fill(rgb_tuple)
        return ("200 OK", [], [])

    def curr_ssids(self,environ):
        


        jsonNets = json.dumps(self.netList)
        print(jsonNets)
        headers = [("Content-Type","application/json")]
        
        return ("200 OK",headers,jsonNets)

    def set_wifi(self,environ):

        print("GOT /setWifi request")
        jsonData = json_module.loads(environ["wsgi.input"].getvalue())
        print(jsonData["ssid"])
        print(jsonData["pass"])
        self.wifi_manager.esp.disconnect()

        conn_data = {"ssid":jsonData["ssid"],"password":jsonData["pass"]}

        print("new conn data:")
        print(conn_data)

        with open("src/conn.json","w") as conn_file:

            print("opened the conn file")
            json.dump(conn_data,conn_file)
        
        print("Saved the connection to the conn.json file")

        print("Successfully connected to wifi network, resetting board...")
        supervisor.reload()


    def run_wifi_server(self):
        #Starting WIFI service
        
        #Create the access point and the HTML page
        self.wifi_manager.create_ap()

        # Here we setup our server, passing in our web_app as the application
        server.set_interface(self.wifi_manager.esp)
        wsgiServer = server.WSGIServer(80, application=self.web_app)

        print("open this IP in your browser: ", self.wifi_manager.esp.pretty_ip(self.wifi_manager.esp.ip_address))

        # Start the server
        wsgiServer.start()
        while True:
            # Our main loop where we have the server poll for incoming requests
            try:
                wsgiServer.update_poll()
                # Could do any other background tasks here, like reading sensors
            except (ValueError, RuntimeError) as e:
                print("Failed to update server, restarting ESP32\n", e)
                self.esp.reset()
                
                #TODO: Need error handling and resetting at somepoint...or just reboot the whole board

                continue


class NetworkManager:

    def __init__(self,status_light):

        # ESP initialization code
        # If you are using a board with pre-defined ESP32 Pins:
        self.esp32_cs = DigitalInOut(board.ESP_CS)
        self.esp32_ready = DigitalInOut(board.ESP_BUSY)
        self.esp32_reset = DigitalInOut(board.ESP_RESET)

        #Initialize the spi connection and esp library to talk to the co-processor
        self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self.esp = adafruit_esp32spi.ESP_SPIcontrol(self.spi, self.esp32_cs, self.esp32_ready, self.esp32_reset)

        requests.set_socket(socket, self.esp)
        self.status_light = status_light


        if self.esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
            print("ESP32 found and in idle mode")
        print("Firmware vers.", self.esp.firmware_version)
        print("MAC addr:", [hex(i) for i in self.esp.MAC_address])


        self.activeNetworks = self.esp.scan_networks()
        
        static = "/static"
        try:
            static_files = os.listdir(static)
            if "index.html" not in static_files:
                raise RuntimeError(
                    """
                    This example depends on an index.html, but it isn't present.
                    Please add it to the {0} directory""".format(
                        static
                    )
                )

        except (OSError) as e:
            raise RuntimeError(
                """
                This example depends on a static asset directory.
                Please create one named {0} in the root of the device filesystem.""".format(
                    static
                )
            ) from e
        self.web_app = SimpleWSGIApplication(static_dir="/static")
        self.web_app.on("GET", "/led_on", self.led_on)
        self.web_app.on("GET", "/led_off", self.led_off)
        self.web_app.on("POST", "/ajax/ledcolor", self.led_color)
        self.web_app.on("GET","/ajax/ssids",self.curr_ssids)
        self.web_app.on("POST","/setWifi",self.set_wifi)

#Load in the JSON file of the saved connections
        self.potential_connections = None


    def scan_networks(self):
        print("rescanning networks")

        networkList  = []
        for net in self.activeNetworks:
            curr_ap_ssid = str(net["ssid"],"utf-8")

            if curr_ap_ssid not in networkList:
                networkList.append(curr_ap_ssid)

        print(networkList)
        return {'ssids':networkList}

    def read_connections(self):

        try:

            with open("src/conn.json","r") as conn_list:
                print("opened the conn file")
                self.potential_connections = json.load(conn_list)
                print("Loaded:")
                print(self.potential_connections)
                # for ssid,pass_dict in potential_connections["ssids"].items():
                #     print(f"SSID: {ssid}, Pass: {pass_dict['pass']}")

        except OSError as e:
            #If we get this error we were unable to open the conn.txt file so just move on to access point creation and try recreating the conn.txt file
            print("ERROR oppening conn.txt file")
            print("Error:",e)
     
    def attempt_connection(self):

        if self.potential_connections is not None:
            print("Attempting to connect to an existing wifi network...")

            currNetworks = self.esp.scan_networks()
        
            #Scan for connections and loop through each found connection
            for ap in currNetworks:
            #for ap in []:
                #print("\t%s\t\tRSSI: %d" % (str(ap["ssid"], "utf-8"), ap["rssi"]))
                if self.esp.is_connected:
                    break

                curr_ap_ssid = str(ap["ssid"],"utf-8")

                #If network name is saved in the json file...attempt to connect
                if curr_ap_ssid in self.potential_connections["ssids"]:
                    print(f"Found network settings for '{curr_ap_ssid}' - attempting to connect!")
                else:
                    #Skip attempt if settings for name not found
                    print(f"No network settings found for '{curr_ap_ssid}' - skipping...")
                    continue


                attempts = 1
                max_attempts = 3
                while not self.esp.is_connected and attempts < max_attempts + 1:
                    print("Attempt #",attempts)
                    try:

                        passwrd = self.potential_connections["ssids"][curr_ap_ssid]
                        print(curr_ap_ssid)
                        print(passwrd)
                        self.esp.connect_AP(curr_ap_ssid, passwrd,20)
                        #esp.connect_AP("iPhone","moistslime",20)
                    
                    except Exception as e:

                        attempts += 1
                        print("could not connect to AP:", e)
                        continue
                print("------------------------------------------")

        else:
            print("No potential connection to be made")

    def check_connection(self):

        if self.esp.is_connected:

            print("Successfully connected to wifi, enjoy!")
            self.status_light.fill((45, 134, 234))

            print("Connected to", str(self.esp.ssid, "utf-8"), "\tRSSI:", self.esp.rssi)
            print("My IP address is", self.esp.pretty_ip(self.esp.ip_address))
            print(
                "IP lookup adafruit.com: %s" % self.esp.pretty_ip(self.esp.get_host_by_name("adafruit.com"))
            )
            print("Ping google.com: %d ms" % self.esp.ping("google.com"))

            print("Testing GET capability: ")
            TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
            JSON_GET_URL = "https://httpbin.org/get"
            JSON_POST_URL = "https://httpbin.org/post"
            
            req = requests
            print("Conn: ",self.esp.is_connected)
            print("Fetching text from %s" % TEXT_URL)
            response = req.get(TEXT_URL)
            print("-" * 40)
            

            print("Text Response: ", response.text)
            print("-" * 40)
            response.close()

            print("Conn: ",self.esp.is_connected)
            print("Fetching JSON data from %s" % JSON_GET_URL)
            response = req.get(JSON_GET_URL)
            print("-" * 40)
            response.close()

            print("Conn: ",self.esp.is_connected)            
            print("Fetching JSON data from %s" % JSON_GET_URL)
            response = req.get(JSON_GET_URL)
            print("-" * 40)
            response.close()
            print("Conn: ",self.esp.is_connected)
            print("Fetching JSON data from %s" % JSON_GET_URL)
            response = req.get(JSON_GET_URL)
            print("-" * 40)
            response.close()

            print("Conn: ",self.esp.is_connected)
            print("Fetching JSON data from %s" % JSON_GET_URL)
            response = req.get(JSON_GET_URL)
            print("-" * 40)
            response.close()

            print("Conn: ",self.esp.is_connected)
            print("Fetching JSON data from %s" % JSON_GET_URL)
            response = req.get(JSON_GET_URL)
            print("-" * 40)
            response.close()   
            return True
        else:
            return False

    # Our HTTP Request handlers
    def led_on(self,environ):  # pylint: disable=unused-argument
        print("led on!")
        self.status_light.fill((0, 0, 100))
        return self.web_app.serve_file("static/index.html")
    def led_off(self,environ):  # pylint: disable=unused-argument
        print("led off!")
        self.status_light.fill(0)
        return self.web_app.serve_file("static/index.html")
    def led_color(self,environ):  # pylint: disable=unused-argument
        json = json_module.loads(environ["wsgi.input"].getvalue())
        print(json)
        rgb_tuple = (json.get("r"), json.get("g"), json.get("b"))
        self.status_light.fill(rgb_tuple)
        return ("200 OK", [], [])

    def curr_ssids(self,environ):
        jsonNets = json.dumps(self.scan_networks())
        headers = [("Content-Type","application/json")]

        return self.web_app.serve_file("src/static/index.html")
        return ("200 OK",headers,jsonNets)

    def set_wifi(self,environ):

        print("GOT /setWifi request")
        jsonData = json_module.loads(environ["wsgi.input"].getvalue())
        print(jsonData["ssid"])
        print(jsonData["pass"])
        self.esp.disconnect()

        # TODO: Does this update the web UI if it fails?
        print("Time to validate")
        attempts = 1
        max_attempts = 2
        while not self.esp.is_connected and attempts < max_attempts + 1:
            print("Attempt:",attempts)
            try:

                self.esp.connect_AP(jsonData["ssid"], jsonData["pass"])

            
            except Exception as e:

                attempts += 1
                print("could not connect to APe:", e)
                continue
        
        print(self.esp.is_connected)
        print("------------------------------------------")

        if self.esp.is_connected:
            print("successfully connect to:", jsonData["ssid"])
            #successMSG = json.dumps({"msg":"Successfully connected to network! Rebooting board"})
            #return ("200 OK",headers,successMSG)
            #return("200 OK",[],[])

            self.potential_connections["ssids"][jsonData["ssid"]] = jsonData["pass"]
            print("new potential connections:")
            print(self.potential_connections)

            with open("src/conn.json","w") as conn_list:

                print("opened the conn file")
                self.potential_connections = json.dump(self.potential_connections,conn_list)
            
            print("Saved the connection to the conn.json file")

            print("Successfully connected to wifi network, resetting board...")
            supervisor.reload()


        else:
            headers = [("Content-Type","application/json")]
            print("fail to connect to: ", jsonData["ssid"])
            errMSG = json.dumps({"msg":"Unable to connect to network, maybe the password is incorrect"})
            self.esp.create_AP("My ESP32 AP!","supersecret")
            return ("401 Unauthorized",headers,errMSG)


    def run_wifi_server(self):
        #Starting WIFI service

        self.status_light.fill((228,136,20))
        
        #Create the access point and the HTML page
        secrets = {"ssid": "My ESP32 AP!", "password": "supersecret"}
        #wifi = wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)
        self.esp.create_AP("My ESP32 AP!","supersecret")

        # Here we setup our server, passing in our web_app as the application
        server.set_interface(self.esp)
        wsgiServer = server.WSGIServer(80, application=self.web_app)

        print("open this IP in your browser: ", self.esp.pretty_ip(self.esp.ip_address))

        # Start the server
        wsgiServer.start()
        while True:
            # Our main loop where we have the server poll for incoming requests
            try:
                wsgiServer.update_poll()
                # Could do any other background tasks here, like reading sensors
            except (ValueError, RuntimeError) as e:
                print("Failed to update server, restarting ESP32\n", e)
                self.esp.reset()
                
                #TODO: Need error handling and resetting at somepoint...or just reboot the whole board

                continue

    