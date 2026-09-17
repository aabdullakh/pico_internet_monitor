import network
import socket
import time
import ujson

# --- Wi-Fi Connection Setup ---
WIFI_SSID = "WhiteSky-JLB"
WIFI_PASS = "vk9gdb7s"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASS)

while not wlan.isconnected():
    time.sleep(1)

print("Connected to Wi-Fi! IP:", wlan.ifconfig()[0])

# --- Global tracking variable for Jitter ---
last_latency = 0

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
        "uptime": time.ticks_ms() // 1000
    }

# --- Start Web Server Safely ---
server = None
try:
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    server.listen(1)
    print('Web server listening on', addr)
except Exception as e:
    print('Failed to bind server socket:', e)

# --- Main Request Loop ---
while server:
    try:
        conn, client_addr = server.accept()
        request = conn.recv(4096)

        if b'/api/data' in request:
            data = get_telemetry()
            response_body = ujson.dumps(data)
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Connection: close\r\n"
                "\r\n"
                + response_body
            )
            conn.send(response)
        else:
            conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
            
            with open('index.html', 'r') as f:
                while True:
                    chunk = f.read(512)
                    if not chunk:
                        break
                    conn.send(chunk)

        conn.close()

    except Exception as e:
        print('Runtime Error:', e)