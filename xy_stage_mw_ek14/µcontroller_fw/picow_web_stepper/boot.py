# boot.py
import network
import time

# Fill in your Wi-Fi credentials
SSID = '#########'
PASSWORD = '##############'

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(SSID, PASSWORD)
        max_wait = 20 # Give it more time
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('Waiting for connection...')
            time.sleep(1)
        if wlan.status() != 3:
            raise RuntimeError('Network connection failed! Check SSID/Password and signal.')
    print('Connected! Network config:', wlan.ifconfig())

try:
    do_connect()
except Exception as e:
    print(f"Failed to connect to WiFi: {e}")