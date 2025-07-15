# scripts/port_scan_simulator.py
import subprocess
import json
from datetime import datetime
import os
import requests # Per get_local_ip

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

def simulate_port_scan(target_ip_range, scan_type="SYN", ports=None, log_file="/var/log/malicious_traffic.log"):
    """
    Simula una scansione delle porte utilizzando Nmap.
    Registra i risultati in un file di log JSON.
    """
    if ports is None:
        ports = "1-1024" # Default Nmap
    
    ports_str = ",".join(map(str, ports)) if isinstance(ports, list) else str(ports)
    
    nmap_command = ["nmap", "-Pn"] # -Pn: Treat all hosts as online -- skip host discovery
    
    if scan_type.upper() == "SYN":
        nmap_command.append("-sS") # SYN scan (stealth)
    elif scan_type.upper() == "TCP":
        nmap_command.append("-sT") # TCP connect scan
    elif scan_type.upper() == "UDP":
        nmap_command.append("-sU") # UDP scan
    else:
        print(f"[Port Scan] Tipo di scansione non supportato: {scan_type}. Usando scansione TCP.")
        nmap_command.append("-sT")

    nmap_command.extend(["-p", ports_str, target_ip_range])
    
    print(f"[Port Scan] Starting {scan_type} scan on {target_ip_range} for ports {ports_str}...")

    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "event_type": "Malicious_PortScan",
        "source_ip": LOCAL_IP,
        "target_ip_range": target_ip_range,
        "scan_type": scan_type,
        "ports_scanned": ports_str,
        "nmap_command": " ".join(nmap_command),
        "status": "Started",
        "message": f"Nmap {scan_type} scan initiated on {target_ip_range} for ports {ports_str}"
    }

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    try:
        # Esegui Nmap
        process = subprocess.run(nmap_command, capture_output=True, text=True, check=False, timeout=120)
        
        status = "Completed" if process.returncode == 0 else "Failed"
        if process.returncode != 0 and "Host seems down" in process.stderr:
             status = "Host Unreachable"

        log_entry_result = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "Malicious_PortScan_Result",
            "source_ip": LOCAL_IP,
            "target_ip_range": target_ip_range,
            "scan_type": scan_type,
            "ports_scanned": ports_str,
            "status": status,
            "return_code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "message": f"Nmap scan {status}."
        }
        print(f"[Port Scan] Nmap scan {status}. Output: {process.stdout[:200]}...") # Print first 200 chars

    except subprocess.TimeoutExpired:
        log_entry_result = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "Malicious_PortScan_Result",
            "source_ip": LOCAL_IP,
            "target_ip_range": target_ip_range,
            "scan_type": scan_type,
            "ports_scanned": ports_str,
            "status": "Timeout",
            "error": "Nmap process timed out.",
            "message": "Nmap scan timed out."
        }
        print(f"[Port Scan] Nmap scan timed out.")
    except FileNotFoundError:
        log_entry_result = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "Malicious_PortScan_Failed",
            "source_ip": LOCAL_IP,
            "error": "Nmap not found",
            "message": "Nmap command not found. Please ensure Nmap is installed on the system."
        }
        print(f"[Port Scan] Error: Nmap command not found. Please ensure Nmap is installed on the system.")
    except Exception as e:
        log_entry_result = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "Malicious_PortScan_Failed",
            "source_ip": LOCAL_IP,
            "error": str(e),
            "message": f"An unexpected error occurred during port scan: {e}"
        }
        print(f"[Port Scan] An unexpected error occurred: {e}")

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry_result) + "\n")

if __name__ == '__main__':
    # Esempio di utilizzo standalone per test locali
    simulate_port_scan("127.0.0.1", scan_type="SYN", ports=[22, 80, 443])
    simulate_port_scan("127.0.0.1", scan_type="TCP", ports=[8081])