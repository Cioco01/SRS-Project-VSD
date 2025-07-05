# security-sim-project/scripts/traffic_generator_agent.py
from flask import Flask, request, jsonify
import requests
import time
import threading
import random
import os
import dns.resolver # Richiede 'dnspython'

app = Flask(__name__)

# Variabili d'ambiente (popolate dallo startup script)
WEB_SERVER_IP = os.environ.get('WEB_SERVER_IP', '10.0.1.10')
DB_SERVER_IP = os.environ.get('DB_SERVER_IP', '10.0.3.10')
INTERNAL_CLIENT_IP = os.environ.get('INTERNAL_CLIENT_IP', '10.0.2.10') # Questo stesso IP
DNS_SERVER_IP = os.environ.get('DNS_SERVER_IP', '8.8.8.8') # O il tuo DNS interno
CAPTURE_AGENT_URL = "http://127.0.0.1:5003/log_event" # L'URL del capture agent locale

# --- Funzioni di Generazione Traffico ---

def send_log_event(event_type, source_ip, destination_ip, port, protocol, description):
    """Invia un evento al Capture Agent."""
    payload = {
        "timestamp": int(time.time()),
        "event_type": event_type,
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "port": port,
        "protocol": protocol,
        "description": description
    }
    try:
        response = requests.post(CAPTURE_AGENT_URL, json=payload, timeout=5)
        response.raise_for_status()
        # print(f"Evento inviato: {event_type}")
    except requests.exceptions.RequestException as e:
        print(f"Errore invio evento al Capture Agent: {e}")

def simulate_http_Browse(duration_seconds, source_ip, target_ip):
    """Simula richieste HTTP al web server."""
    print(f"Avvio simulazione Browse per {duration_seconds}s da {source_ip} a {target_ip}")
    start_time = time.time()
    while (time.time() - start_time) < duration_seconds:
        try:
            response = requests.get(f"http://{target_ip}", timeout=2)
            if response.status_code == 200:
                send_log_event("http_request_benign", source_ip, target_ip, 80, "TCP", "HTTP GET /")
            else:
                send_log_event("http_request_error", source_ip, target_ip, 80, "TCP", f"HTTP GET / Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            send_log_event("http_request_failed", source_ip, target_ip, 80, "TCP", f"HTTP GET / failed: {e}")
        time.sleep(random.uniform(0.5, 3.0)) # Ritardo variabile

def simulate_dns_queries(duration_seconds, source_ip, target_dns_ip):
    """Simula query DNS."""
    print(f"Avvio simulazione DNS per {duration_seconds}s da {source_ip} a {target_dns_ip}")
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [target_dns_ip]
    domains = ["google.com", "example.com", "microsoft.com", "cloudflare.com"]
    start_time = time.time()
    while (time.time() - start_time) < duration_seconds:
        domain = random.choice(domains)
        try:
            resolver.query(domain, "A")
            send_log_event("dns_query_benign", source_ip, target_dns_ip, 53, "UDP", f"DNS query for {domain}")
        except dns.resolver.NXDOMAIN:
            send_log_event("dns_query_nxdomain", source_ip, target_dns_ip, 53, "UDP", f"DNS NXDOMAIN for {domain}")
        except Exception as e:
            send_log_event("dns_query_failed", source_ip, target_dns_ip, 53, "UDP", f"DNS query failed for {domain}: {e}")
        time.sleep(random.uniform(1.0, 5.0))

def simulate_db_access(duration_seconds, source_ip, target_db_ip):
    """Simula accessi al database."""
    print(f"Avvio simulazione DB access per {duration_seconds}s da {source_ip} a {target_db_ip}")
    # Nota: Non ci connettiamo realmente al DB per non complicare le credenziali qui.
    # Si simula solo l'evento di tentativo di connessione.
    start_time = time.time()
    while (time.time() - start_time) < duration_seconds:
        # Simulate successful connection attempt
        send_log_event("db_access_benign", source_ip, target_db_ip, 3306, "TCP", "Simulated DB connection attempt")
        time.sleep(random.uniform(0.8, 4.0))

def inject_abnormal_traffic(duration_seconds, source_ip, target_ip):
    """Inietta un pattern di traffico anomalo (es. molte richieste a porte non standard)."""
    print(f"Iniezione traffico anomalo per {duration_seconds}s da {source_ip} a {target_ip}")
    start_time = time.time()
    while (time.time() - start_time) < duration_seconds:
        abnormal_port = random.choice([21, 23, 25, 139, 445, 8080, 9000]) # Porte inusuali per un web server
        send_log_event("abnormal_port_scan_like", source_ip, target_ip, abnormal_port, "TCP", f"Request to unusual port {abnormal_port}")
        time.sleep(random.uniform(0.1, 0.5)) # Frequenza più alta

def inject_api_anomaly(duration_seconds, source_ip, target_ip):
    """Simula chiamate API anomale (es. troppe richieste non autenticate)."""
    print(f"Iniezione anomalia API per {duration_seconds}s da {source_ip} a {target_ip}")
    start_time = time.time()
    while (time.time() - start_time) < duration_seconds:
        try:
            # Simula una richiesta API non autenticata a un endpoint inesistente o protetto
            response = requests.post(f"http://{target_ip}/api/v1/admin/unauthorized_action", timeout=2)
            send_log_event("api_unauthorized_attempt", source_ip, target_ip, 80, "TCP", f"Unauthorized API call. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
             send_log_event("api_unauthorized_failed", source_ip, target_ip, 80, "TCP", f"Unauthorized API call failed: {e}")
        time.sleep(random.uniform(0.2, 1.0))

# --- API Endpoints per il Traffic Generator ---

@app.route('/start_traffic_generation', methods=['POST'])
def start_traffic_generation_endpoint():
    data = request.json
    duration = data.get('duration_seconds', 60)
    traffic_types = data.get('traffic_types', ['http_Browse', 'dns_queries', 'db_access'])
    anomaly_types = data.get('anomaly_types', [])
    source_ip = INTERNAL_CLIENT_IP # L'IP di questo agente, che genera il traffico

    if not isinstance(duration, int) or duration <= 0:
        return jsonify({"status": "error", "message": "La durata deve essere un numero intero positivo."}), 400

    print(f"Ricevuta richiesta di generazione traffico per {duration}s. Tipi: {traffic_types}, Anomalie: {anomaly_types}")

    # Avvia le simulazioni in thread separati
    threads = []
    if "http_Browse" in traffic_types:
        threads.append(threading.Thread(target=simulate_http_Browse, args=(duration, source_ip, WEB_SERVER_IP)))
    if "dns_queries" in traffic_types:
        threads.append(threading.Thread(target=simulate_dns_queries, args=(duration, source_ip, DNS_SERVER_IP)))
    if "db_access" in traffic_types:
        threads.append(threading.Thread(target=simulate_db_access, args=(duration, source_ip, DB_SERVER_IP)))

    if "abnormal_traffic" in anomaly_types:
        threads.append(threading.Thread(target=inject_abnormal_traffic, args=(duration, source_ip, WEB_SERVER_IP)))
    if "api_anomaly" in anomaly_types:
        threads.append(threading.Thread(target=inject_api_anomaly, args=(duration, source_ip, WEB_SERVER_IP)))

    for t in threads:
        t.start()

    return jsonify({"status": "accepted", "message": f"Generazione traffico avviata in background per {duration} secondi."})

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"status": "Traffic Generator Agent running", "timestamp": time.time()})

if __name__ == '__main__':
    # Traffic Generator Agent sulla porta 5002, accessibile solo da localhost (orchestrator)
    app.run(host='127.0.0.1', port=5002)