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
# Disable Wi-Fi power saving; its sleep cycles cause false loss and latency spikes
PM_NONE = 0xa11140
wlan.config(pm=PM_NONE)

boot_time = time.time()

# --- Number of connection probes per telemetry reading ---
PROBES = 5
PROBE_GAP_MS = 200


def connect_wifi():
    if wlan.isconnected():
        return True

    wlan.connect(WIFI_SSID, WIFI_PASS)

    for _ in range(20):
        if wlan.isconnected():
            wlan.config(pm=PM_NONE)
            print("Connected to Wi-Fi! IP:", wlan.ifconfig()[0])
            return True
        time.sleep(1)

    print("Wi-Fi connect timed out, will retry next loop")
    return False


# --- Helper Functions to Measure Telemetry ---
def probe_once(addr):
    """Time one TCP connect to addr. Returns latency in ms, or None on failure."""
    s = None
    try:
        s = socket.socket()
        s.settimeout(2.0)
        start_time = time.ticks_ms()
        s.connect(addr)
        return time.ticks_diff(time.ticks_ms(), start_time)
    except Exception:
        return None
    finally:
        if s is not None:
            s.close()


def get_telemetry():
    gc.collect()
    rssi = wlan.status('rssi')

    try:
        addr = socket.getaddrinfo('1.1.1.1', 80)[0][-1]
    except Exception:
        addr = None

    results = []
    for i in range(PROBES):
        if i > 0:
            time.sleep_ms(PROBE_GAP_MS)
        results.append(probe_once(addr) if addr is not None else None)
    successes = [r for r in results if r is not None]

    packet_loss = round((PROBES - len(successes)) * 100 / PROBES)

    if successes:
        latency = round(sum(successes) / len(successes))
        jitter = max(successes) - min(successes)
    else:
        latency = 0
        jitter = 0

    if packet_loss == 0:
        status = "Optimal"
    elif successes:
        status = "Degraded"
    else:
        status = "Disconnected"

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
        data = get_telemetry()
        print(data)
        send(data)
    time.sleep(10)
