import network
import socket
import time
import gc
import ujson
import urequests
from config import WIFI_SSID, WIFI_PASS, AIO_USER, AIO_KEY

AIO_URL = "https://io.adafruit.com/api/v2/{}/feeds/intern-monitor/data".format(AIO_USER)

# --- Wi-Fi Connection Setup ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

boot_time = time.time()

# --- Global tracking variable for Jitter ---
last_latency = 0


def connect_wifi():
    if wlan.isconnected():
        return True

    wlan.connect(WIFI_SSID, WIFI_PASS)

    for _ in range(20):
        if wlan.isconnected():
            print("Connected to Wi-Fi! IP:", wlan.ifconfig()[0])
            return True
        time.sleep(1)

    print("Wi-Fi connect timed out, will retry next loop")
    return False


# --- Helper Function to Measure Telemetry ---
def get_telemetry():
    global last_latency
    rssi = wlan.status('rssi')
    start_time = time.ticks_ms()

    try:
        addr_info = socket.getaddrinfo('1.1.1.1', 80)
        addr = addr_info[0][-1]

        s = socket.socket()
        s.settimeout(2.0)
        s.connect(addr)
        s.close()

        latency = time.ticks_diff(time.ticks_ms(), start_time)
        status = "Optimal"
        packet_loss = 0

        # Calculate Jitter (difference from last read)
        if last_latency > 0:
            jitter = abs(latency - last_latency)
        else:
            jitter = 0
        last_latency = latency

    except Exception:
        latency = 0
        jitter = 0
        status = "Disconnected"
        packet_loss = 100

    return {
        "status": status,
        "rssi": rssi,
        "latency": latency,
        "jitter": jitter,
        "packet_loss": packet_loss,
        "uptime": time.time() - boot_time
    }


def send(data):
    gc.collect()
    response = None
    try:
        response = urequests.post(
            AIO_URL,
            headers={"X-AIO-Key": AIO_KEY},
            json={"value": ujson.dumps(data)}
        )
    except Exception as e:
        print("Failed to send telemetry:", e)
    finally:
        if response is not None:
            response.close()


# --- Main Loop ---
while True:
    if connect_wifi():
        send(get_telemetry())
    time.sleep(10)
