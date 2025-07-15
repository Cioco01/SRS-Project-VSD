# scripts/http_simulator.py
import requests
import time
import json
from datetime import datetime
import os

def get_local_ip():
    """Tenta di ottenere l'IP interno dell'istanza GCE."""
    try:
        # Questo endpoint è specifico per le VM di Google Compute Engine
        response = requests.get("http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip",
                                headers={"Metadata-Flavor": "Google"}, timeout=0.5)
        if response.status_code == 200:
            return response.text
    except requests.exceptions.RequestException:
        pass
    # Fallback per l'ambiente locale o se non riesce a ottenere l'IP GCE
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80)) # Connetti a un IP esterno per trovare l'IP locale
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1" # Default se non trova nessun IP
    finally:
        s.close()
    return ip

LOCAL_IP = get_local_ip()

def simulate_http_traffic(ip, port=80, num_requests=5,log_file=os.path.join(os.path.dirname(__file__), "http_traffic.log")):
    """
    Simula il traffico HTTP verso un server specificato.
    Registra gli eventi in un file di log JSON.
    """
    url = f"http://{ip}:{port}"
    print(f"[HTTP Simulator] Starting HTTP traffic to {url}")

    for i in range(num_requests):
        timestamp = datetime.now().isoformat()
        is_anomaly = (port == 8081) # L'anomalia è definita dal cambio di porta

        try:
            r = requests.get(url, timeout=5) # Aumentato il timeout per stabilità su rete reale
            log_entry = {
                "timestamp": timestamp,
                "event_type": "HTTP_Request",
                "source_ip": LOCAL_IP,
                "destination_ip": ip,
                "destination_port": port,
                "status_code": r.status_code,
                "url": url,
                "anomaly": is_anomaly,
                "message": f"Status: {r.status_code} from {url}"
            }
            print(f"[HTTP] Status: {r.status_code} from {url}")
        except requests.exceptions.ConnectionError as e:
            log_entry = {
                "timestamp": timestamp,
                "event_type": "HTTP_Request_Failed",
                "source_ip": LOCAL_IP,
                "destination_ip": ip,
                "destination_port": port,
                "status": "Connection Error",
                "url": url,
                "anomaly": is_anomaly,
                "error": str(e),
                "message": f"Failed to connect (ConnectionError): {e}"
            }
            print(f"[HTTP] Failed to connect (ConnectionError): {e}")
        except requests.exceptions.Timeout as e:
            log_entry = {
                "timestamp": timestamp,
                "event_type": "HTTP_Request_Failed",
                "source_ip": LOCAL_IP,
                "destination_ip": ip,
                "destination_port": port,
                "status": "Timeout",
                "url": url,
                "anomaly": is_anomaly,
                "error": str(e),
                "message": f"Request timed out: {e}"
            }
            print(f"[HTTP] Request timed out: {e}")
        except Exception as e:
            log_entry = {
                "timestamp": timestamp,
                "event_type": "HTTP_Request_Failed",
                "source_ip": LOCAL_IP,
                "destination_ip": ip,
                "destination_port": port,
                "status": "Other Error",
                "url": url,
                "anomaly": is_anomaly,
                "error": str(e),
                "message": f"An unexpected HTTP error occurred: {e}"
            }
            print(f"[HTTP] An unexpected HTTP error occurred: {e}")

        # Assicurati che la directory del log esista
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        time.sleep(2)

if __name__ == '__main__':
    # Esempio di utilizzo standalone per test locali
    simulate_http_traffic("127.0.0.1", port=80, num_requests=3)
    simulate_http_traffic("127.0.0.1", port=8081, num_requests=2)
