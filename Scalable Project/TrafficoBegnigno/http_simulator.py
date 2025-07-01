import requests
import time

def simulate_http_traffic(ip, port=80):
    url = f"http://{ip}:{port}"
    for i in range(5):
        try:
            r = requests.get(url, timeout=2)
            print(f"[HTTP] Status: {r.status_code} from {url}")
        except Exception as e:
            print(f"[HTTP] Failed to connect: {e}")
        time.sleep(2)
