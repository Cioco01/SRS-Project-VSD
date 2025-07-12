# security-sim-project/scripts/orchestrator_backend.py
from flask import Flask, request, jsonify, send_from_directory
import requests
import json
import time
import threading
import os
import pandas as pd # Per l'elaborazione dei dati

# Google Cloud Imports
from google.cloud import storage
from google.cloud.sql.connector import Connector
import pymysql

app = Flask(__name__, static_folder='static') # Indica a Flask dove trovare i file statici

# --- Configurazione Globale ---
# Queste variabili sono popolate dallo startup script di Terraform (attacker_orchestrator_startup.sh)

# IP delle VM target (leggi da variabili d'ambiente)
WEB_SERVER_IP = os.environ.get('WEB_SERVER_IP', '10.0.1.10')
DB_SERVER_IP = os.environ.get('DB_SERVER_IP', '10.0.3.10')
INTERNAL_CLIENT_IP = os.environ.get('INTERNAL_CLIENT_IP', '10.0.2.10')
DNS_SERVER_IP = os.environ.get('DNS_SERVER_IP', '8.8.8.8') # Assicurati che sia configurato!

# URL degli agenti Flask (tutti sulla stessa VM, quindi localhost)
ATTACKER_AGENT_URL = "http://127.0.0.1:5001" # Base URL, gli endpoint saranno /attack, /status
TRAFFIC_GENERATOR_AGENT_URL = "http://127.0.0.1:5002" # Base URL, gli endpoint saranno /start_traffic_generation, /status
TRAFFIC_CAPTURE_AGENT_URL = "http://127.0.0.1:5003" # Nuovo URL per il traffic capture agent

GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME')
CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_DATABASE_NAME = os.environ.get('CLOUDSQL_DATABASE_NAME')
CLOUDSQL_USER_NAME = os.environ.get('CLOUDSQL_USER_NAME')
CLOUDSQL_USER_PASSWORD = os.environ.get('CLOUDSQL_USER_PASSWORD') # USA SECRET MANAGER IN PRODUZIONE!

# Mappatura dei nomi logici delle VM ai loro IP
TARGET_IPS = {
    "web-server": WEB_SERVER_IP,
    "db-server": DB_SERVER_IP,
    "internal-client": INTERNAL_CLIENT_IP,
    "dns-server": DNS_SERVER_IP # Per le query DNS se non è 8.8.8.8
}

# --- Cloud SQL Connector Setup ---
connector = Connector()
# Global connection pool (opzionale, per connessioni più efficienti)
# db_connection_pool = None # Potresti inizializzarlo qui

def get_cloudsql_conn():
    """Stabilisce una connessione al database Cloud SQL."""
    try:
        conn = connector.connect(
            CLOUDSQL_CONNECTION_NAME,
            "pymysql",
            user=CLOUDSQL_USER_NAME,
            password=CLOUDSQL_USER_PASSWORD,
            db=CLOUDSQL_DATABASE_NAME
        )
        print("Connessione a Cloud SQL stabilita.")
        return conn
    except Exception as e:
        print(f"Errore durante la connessione a Cloud SQL: {e}")
        return None

def create_network_events_table(conn):
    """Crea la tabella network_events se non esiste."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_network_traffic (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp_capture BIGINT NOT NULL,
                source_ip VARCHAR(45) NOT NULL,
                destination_ip VARCHAR(45) NOT NULL,
                source_port INT,
                destination_port INT,
                protocol VARCHAR(10) NOT NULL,
                packet_length INT,
                flags VARCHAR(20),
                ttl INT,
                description TEXT,
                full_line TEXT NOT NULL,
                ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        print("Tabella 'raw_network_traffic' verificata/creata con successo.")
        return True
    except Exception as e:
        print(f"Errore durante la creazione della tabella: {e}")
        return False

# --- Funzioni di Coordinamento Agenti ---

def call_agent_api(base_url, endpoint, method='GET', payload=None):
    """Funzione helper per chiamare le API degli agenti Flask."""
    url = f"{base_url}{endpoint}"
    print(f"Chiamata API all'agente: {method} {url}")
    try:
        if method == 'POST':
            response = requests.post(url, json=payload, timeout=60)
        else: # GET
            response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la chiamata a {url}: {e}")
        return {"status": "error", "message": f"Errore comunicazione con agente {url}: {str(e)}"}

# Coordina l'esecuzione degli attacchi
def coordinate_attacks(attacks_list, simulation_duration):
    """
    Coordina l'esecuzione degli attacchi pianificati inviando richieste all'Attacker Agent.
    """
    if not attacks_list:
        print("Nessun attacco da coordinare.")
        return

    print(f"Coordinamento di {len(attacks_list)} attacchi.")

    attack_threads = []
    
    for attack_config in attacks_list:
        attack_type = attack_config.get('attack_type')
        target_name = attack_config.get('target_name')
        params = attack_config.get('params', {})

        target_ip = TARGET_IPS.get(target_name)
        if not target_ip:
            print(f"ATTENZIONE: Target '{target_name}' non trovato per l'attacco '{attack_type}'. Saltato.")
            continue

        # Costruisci il payload per l'Attacker Agent
        # L'endpoint sull'Attacker Agent sarà /attack, e il payload conterrà i dettagli.
        attack_payload = {
            "attack_type": attack_type,
            "target_ip": target_ip,
            "duration_seconds": simulation_duration, # Assumiamo che l'attacco duri quanto la simulazione
            "params": params
        }

        # Lancia ogni attacco in un thread separato per eseguirli in parallelo
        def run_single_attack(payload):
            print(f"Avvio attacco '{payload['attack_type']}' su {payload['target_ip']}...")
            response = call_agent_api(ATTACKER_AGENT_URL, "/attack", method='POST', payload=payload)
            print(f"Risposta Attacker Agent per {payload['attack_type']}: {response}")

        thread = threading.Thread(target=run_single_attack, args=(attack_payload,))
        attack_threads.append(thread)
        thread.start()
        # Aggiungi un piccolo ritardo tra l'avvio dei thread se vuoi scaglionarli
        time.sleep(1) 
    
    print("Tutti gli attacchi sono stati lanciati.")

@app.route('/')
def index():
    """Serve la pagina HTML della GUI."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/start_simulation', methods=['POST'])
def start_simulation_endpoint():
   
    data = request.get_json()
    if not data or 'simulation_duration_seconds' not in data:
        return jsonify({"status": "error", "message": "Durata della simulazione non specificata."}), 400    

    simulation_duration = data.get('simulation_duration_seconds', 120) # Default a 120 secondi se non specificato
    attacks_to_schedule = data.get('attacks', []) # <--- RECUPERA GLI ATTACCHI DA QUI

    
    # Converti a intero e valida (buona pratica)
    try:
        simulation_duration = int(simulation_duration)
        if simulation_duration <= 0:
            return jsonify({"status": "error", "message": "Simulation duration must be a positive number"}), 400
    except ValueError:
        return jsonify({"status": "error", "message": "Simulation duration must be an integer"}), 400

    
    def run_full_simulation():
        # 1. Avvia la cattura del traffico effettiva all'inizio della simulazione
        print("Avvio cattura traffico tramite Traffic Capture Agent...")
        capture_start_response = call_agent_api(TRAFFIC_CAPTURE_AGENT_URL, "/start_capture", method='POST', payload={"interface": "eth0"})
        print(f"Traffic Capture Agent Start Response: {capture_start_response}")
        if capture_start_response.get("status") == "error":
            print("ERRORE: Impossibile avviare la cattura traffico. La simulazione potrebbe non essere registrata correttamente.")
            # Gestire l'errore, magari fermare la simulazione o inviare una notifica

        # 2. Avvia gli attacchi programmati
        coordinate_attacks(attacks_to_schedule, simulation_duration)

        # 3. Lascia che la simulazione si svolga per la durata specificata
        print(f"Simulazione attiva... attendendo {simulation_duration} secondi.")
        time.sleep(simulation_duration)

        # 4. Ferma la cattura del traffico
        print("Invio comando per fermare la cattura traffico...")
        capture_stop_response = call_agent_api(TRAFFIC_CAPTURE_AGENT_URL, "/stop_capture", method='POST')
        print(f"Traffic Capture Agent Stop Response: {capture_stop_response}")

        print("Simulazione completa terminata. Dati traffico nel database.")
        # ... (logica per GCS se vuoi un CSV riassuntivo del traffico catturato) ...

    threading.Thread(target=run_full_simulation).start()
    return jsonify({"status": "accepted", "message": f"Simulazione completa avviata in background per {simulation_duration} secondi."})

@app.route('/api/status', methods=['GET'])
def get_orchestrator_status():
       # Inizializza le variabili all'inizio della funzione
    orchestrator_status = {"status": "OK", "message": "Orchestrator is running."}
    agent_statuses = {}

    agent_types = {
        "Attacker Agent": ATTACKER_AGENT_URL,
        "Traffic Generator Agent": TRAFFIC_GENERATOR_AGENT_URL,
        "Traffic Capture Agent": TRAFFIC_CAPTURE_AGENT_URL # Aggiungi il nuovo
    }

    for name, url in agent_types.items():
        try:
            res = requests.get(f"{url}/status", timeout=5)
            if res.status_code == 200:
                agent_statuses[name] = res.json()
            else:
                agent_statuses[name] = {"status": "error", "message": f"HTTP Error {res.status_code}"}
        except requests.exceptions.RequestException as e:
            agent_statuses[name] = {"status": "error", "message": f"Non raggiungibile: {str(e)}"}

    return jsonify({"orchestrator": orchestrator_status, "agents": agent_statuses})


# --- Main Execution ---
if __name__ == '__main__':
    print("Avvio Flask backend dell'Orchestratore su http://0.0.0.0:5000")
    # Disabilita debug per non esporre informazioni sensibili in un ambiente di produzione
    app.run(host='0.0.0.0', port=5000, debug=False)