# Raspberry Pi Pico W Internet & Wi-Fi Monitor 
A self-contained, real-time local network telemetry monitor pwered by Pico W running MicroPython. Plug it into your home electricity and track Wi-Fi quality right from your phone.

## How it works

- The Pico measures Wi-Fi RSSI, latency/jitter/packet loss (via a TCP connect to `1.1.1.1:80`), and uptime every 10 seconds, then posts that telemetry to an [Adafruit IO](https://io.adafruit.com) feed called `intern-monitor` (public visibility, so it can be read without an API key).
- `index.html` is a static page (hosted on GitHub Pages) that polls the public feed every 10 seconds and renders the dashboard. It has no server component and needs no credentials — it works from any browser, anywhere.
- If the feed's last update is older than 60 seconds, the page shows "Offline" (the Pico can't post when the internet is down, so stale data means offline).

## Setup

1. Copy `config.example.py` to `config.py` and fill in your real `WIFI_SSID`, `WIFI_PASS`, `AIO_USER`, and `AIO_KEY` (from your Adafruit IO account). `config.py` is gitignored — never commit it.
2. Create a feed named `intern-monitor` in your Adafruit IO account (or let `main.py`'s first run fail loudly if it doesn't exist — you'll need to create it once via the Adafruit IO API or dashboard, and set its visibility to **public**).
3. Flash the Pico:
   ```bash
   pip install mpremote
   mpremote cp main.py :main.py
   mpremote cp config.py :config.py
   mpremote reset
   ```
4. Publish `index.html` via GitHub Pages (Settings → Pages → Deploy from a branch → `main` → `/`).

## Reflashing after changes

Whenever you edit `main.py` or `config.py`, push the new version to the Pico and reset it:

```bash
mpremote cp main.py :main.py
mpremote cp config.py :config.py   # only needed if config.py changed
mpremote reset
```

To watch the Pico's live serial output for debugging, run `mpremote connect <port>` (this briefly interrupts the running loop, which resumes automatically after the next `mpremote reset`).
