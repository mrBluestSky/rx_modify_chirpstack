from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from chirpstack_api import integration
from google.protobuf.json_format import Parse

from datetime import datetime, timedelta


class Handler(BaseHTTPRequestHandler):
    # True -  JSON marshaler
    # False - Protobuf marshaler (binary)
    json = True

    device_uplinks = {}

    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        query_args = parse_qs(urlparse(self.path).query)

        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)

        if query_args["event"][0] == "up":
            self.up(body)

    def up(self, body):
        up = self.unmarshal(body, integration.UplinkEvent())
        device_eui = up.device_info.dev_eui
        payload_hex = up.data.hex()

        if payload_hex == '3435':
            if device_eui in self.device_uplinks:
                self.device_uplinks[device_eui] += 1
            else:
                self.device_uplinks[device_eui] = 1

            seconds = up.time.seconds + up.time.nanos / 1e9
            readable_time = datetime.utcfromtimestamp(seconds)
            

            print(f"Total uplinks of {device_eui}: {self.device_uplinks[device_eui]}")
            print(f"{readable_time.strftime('%H:%M:%S.%f')}")
            #print(up)
            print(f"Uplink freq {up.tx_info.frequency}, RSSI {up.rx_info[0].rssi}, SNR {up.rx_info[0].snr}")


    def unmarshal(self, body, pl):
        if self.json:
            return Parse(body, pl)
        
        pl.ParseFromString(body)
        return pl
    
    def save_uplinks_to_file(self, device_eui, up_cntr):
        with open("uplinks_data.txt", "a") as file:
            file.write(f"Device EUI: {device_eui}, Uplinks sent: {up_cntr}\n")

httpd = HTTPServer(('10.1.199.203', 8091), Handler)
httpd.serve_forever()
