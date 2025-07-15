# scripts/dns_simulator.py
import dns.resolver
import time
import json
from datetime import datetime
import os
import requests # Per get_local_ip

# Funzione per ottenere l'IP locale, riusata da http_simulator
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

def simulate_dns_queries(dns_ip, domains, spike=False,log_file=os.path.join(os.path.dirname(__file__), "dns_traffic.log")):
    """
    Simula query DNS verso un server DNS specificato.
    Registra gli eventi in un file di log JSON.
    """
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_ip]
    resolver.timeout = 5 # Timeout per le query DNS
    resolver.lifetime = 5 # Durata totale per la risoluzione

    num_queries = 50 if spike else 5
    sleep_interval = 0.1 if spike else 1

    print(f"[DNS Simulator] Starting DNS queries to {dns_ip} (Spike: {spike})")

    for i in range(num_queries):
        timestamp = datetime.now().isoformat()
        domain = domains[i % len(domains)]
        is_anomaly = spike # L'anomalia è definita dallo spike

        try:
            answer = resolver.resolve(domain, 'A')
            resolved_ip = answer[0].address
            log_entry = {
                "timestamp": timestamp,
                "event_type": "DNS_Query",
                "source_ip": LOCAL_IP,
                "destination_ip": dns_ip,
                "destination_port": 53,
                "protocol": "UDP/TCP", # Generalmente UDP, ma può essere TCP per grandi risposte
                "domain": domain,
                "resolved_ip": resolved_ip,
                "anomaly": is_anomaly,
                "message": f"{domain} -> {resolved_ip}"
            }
            print(f"[DNS] {domain} -> {resolved_ip}")
        except dns.resolver.NXDOMAIN:
            log_entry = {
                "timestamp": timestamp,
                "event_type": "DNS_Query_Failed",
                "source_ip": LOCAL_IP,
                "destination_ip": dns_ip,
                "destination_port": 53,
                "protocol": "UDP/TCP",
                "domain": domain,
                "status": "NXDOMAIN",
                "anomaly": is_anomaly,
                "error": "Non-existent domain",
                "message": f"Query failed for {domain}: NXDOMAIN"
            }
            print(f"[DNS] Query failed for {domain}: NXDOMAIN")
        except dns.resolver.Timeout:
            log_entry = {
                "timestamp": timestamp,
                "event_type": "DNS_Query_Failed",
                "source_ip": LOCAL_IP,
                "destination_ip": dns_ip,
                "destination_port": 53,
                "protocol": "UDP/TCP",
                "domain": domain,
                "status": "Timeout",
                "anomaly": is_anomaly,
                "error": "Query timed out",
                "message": f"Query timed out for {domain}"
            }
            print(f"[DNS] Query timed out for {domain}")
        except Exception as e:
            log_entry = {
                "timestamp": timestamp,
                "event_type": "DNS_Query_Failed",
                "source_ip": LOCAL_IP,
                "destination_ip": dns_ip,
                "destination_port": 53,
                "protocol": "UDP/TCP",
                "domain": domain,
                "status": "Other Error",
                "anomaly": is_anomaly,
                "error": str(e),
                "message": f"An unexpected DNS query error occurred for {domain}: {e}"
            }
            print(f"[DNS] An unexpected DNS query error occurred for {domain}: {e}")

        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        time.sleep(sleep_interval)

if __name__ == '__main__':
    # Esempio di utilizzo standalone per test locali
    simulate_dns_queries("8.8.8.8", ["google.com", "bing.com"], spike=False, num_queries=3)
    simulate_dns_queries("8.8.8.8", ["google.com", "bing.com"], spike=True, num_queries=10)
