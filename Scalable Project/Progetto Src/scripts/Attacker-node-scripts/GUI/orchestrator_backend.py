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

GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'your-gcp-project-id')
GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'your-gcs-bucket-name')
CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME', 'your-project-id:your-region:your-cloudsql-instance-name')
CLOUDSQL_DATABASE_NAME = os.environ.get('CLOUDSQL_DATABASE_NAME', 'simulation_data')
CLOUDSQL_USER_NAME = os.environ.get('CLOUDSQL_USER_NAME', 'simuser')
CLOUDSQL_USER_PASSWORD = os.environ.get('CLOUDSQL_USER_PASSWORD', 'password123!') # USA SECRET MANAGER IN PRODUZIONE!

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
            CREATE TABLE IF NOT EXISTS network_events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp BIGINT,
                event_type VARCHAR(100),
                source_ip VARCHAR(15),
                destination_ip VARCHAR(15),
                port INT,
                protocol VARCHAR(10),
                description TEXT,
                ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        print("Tabella 'network_events' verificata/creata con successo.")
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

# --- Logica di Generazione e Salvataggio Dataset ---

def collect_and_store_dataset(duration_seconds):
    """
    Questa funzione ora non "raccoglie" direttamente, ma si assicura che il traffic_capture_agent
    stia salvando i dati nel DB per la durata.
    """
    print(f"Avvio coordinamento dataset per {duration_seconds} secondi...")

    # Non c'è bisogno di raccogliere eventi dal Capture Agent,
    # poiché il Traffic Capture Agent salverà direttamente nel DB.

    # Qui potresti chiamare il Traffic Capture Agent per avviarlo se non è già stato fatto.
    # Questo è meglio farlo all'inizio della simulazione
    # Non è necessario qui perché il traffic_capture_agent gira in background e salva.
    # collect_and_store_dataset è più per la gestione di "cosa fare DOPO la cattura"

    print(f"Traffic Capture Agent dovrebbe stare salvando dati nel DB.")
    # Se hai un GCS_BUCKET_NAME e vuoi ancora salvare un CSV riassuntivo (es. da DB):
    # Dopo la simulazione, potresti voler esportare un CSV dal DB (raw_network_traffic)
    # e caricarlo su GCS.

    # Esempio per esportare dal DB dopo la cattura
    # (Questo è un esempio, la logica potrebbe essere più complessa per query grandi)
    # conn = get_cloudsql_conn()
    # if conn:
    #     df = pd.read_sql_query("SELECT * FROM raw_network_traffic ORDER BY timestamp_capture DESC LIMIT 10000", conn)
    #     conn.close()
    #     # ... (logica per salvare df su CSV e poi GCS) ...
    # else:
    #     print("Impossibile connettersi al DB per esportare il dataset finale.")

    return {"status": "success", "message": "La cattura del traffico è gestita dal Traffic Capture Agent."}

    # 4. Carica su Cloud Storage
    try:
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(csv_filename)
        blob.upload_from_filename(local_csv_path)
        print(f"Dataset caricato su Cloud Storage: gs://{GCS_BUCKET_NAME}/{csv_filename}")
    except Exception as e:
        print(f"Errore caricamento su Cloud Storage: {e}")
        return {"status": "error", "message": f"Errore caricamento GCS: {str(e)}"}

    # 5. Inserisci i dati nel database Cloud SQL
    try:
        conn = get_cloudsql_conn()
        if conn:
            if not create_network_events_table(conn):
                raise Exception("Impossibile creare/verificare la tabella Cloud SQL.")

            cursor = conn.cursor()
            # Converte il DataFrame in una lista di tuple per l'inserimento
            data_to_insert = df[['timestamp', 'event_type', 'source_ip', 'destination_ip', 'port', 'protocol', 'description']].values.tolist()
            insert_query = """
                INSERT INTO network_events (timestamp, event_type, source_ip, destination_ip, port, protocol, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_query, data_to_insert)
            conn.commit()
            print(f"Inseriti {len(data_to_insert)} record in Cloud SQL.")
            cursor.close()
            conn.close()
        else:
            raise Exception("Impossibile stabilire la connessione a Cloud SQL per l'inserimento dati.")
    except Exception as e:
        print(f"Errore durante l'inserimento dati in Cloud SQL: {e}")
        return {"status": "error", "message": f"Errore inserimento Cloud SQL: {str(e)}"}
    finally:
        if os.path.exists(local_csv_path):
            os.remove(local_csv_path)
            print(f"File temporaneo {local_csv_path} eliminato.")

    return {"status": "success", "gcs_path": f"gs://{GCS_BUCKET_NAME}/{csv_filename}", "records_inserted": len(all_captured_events)}

# --- API Endpoints per la GUI ---

@app.route('/')
def index():
    """Serve la pagina HTML della GUI."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/start_simulation', methods=['POST'])
def start_simulation_endpoint():
    # ... (logica esistente) ...

    def run_full_simulation():
        # ... (logica esistente di traffico e attacchi) ...

        # 1. Avvia la cattura del traffico effettiva all'inizio della simulazione
        print("Avvio cattura traffico tramite Traffic Capture Agent...")
        capture_start_response = call_agent_api(TRAFFIC_CAPTURE_AGENT_URL, "/start_capture", method='POST', payload={"interface": "eth0"})
        print(f"Traffic Capture Agent Start Response: {capture_start_response}")
        if capture_start_response.get("status") == "error":
            print("ERRORE: Impossibile avviare la cattura traffico. La simulazione potrebbe non essere registrata correttamente.")
            # Gestire l'errore, magari fermare la simulazione o inviare una notifica

        # 2. Lascia che la simulazione si svolga per la durata specificata
        print(f"Simulazione attiva... attendendo {simulation_duration} secondi.")
        time.sleep(simulation_duration + 5) # Un piccolo buffer

        # 3. Ferma la cattura del traffico
        print("Invio comando per fermare la cattura traffico...")
        capture_stop_response = call_agent_api(TRAFFIC_CAPTURE_AGENT_URL, "/stop_capture", method='POST')
        print(f"Traffic Capture Agent Stop Response: {capture_stop_response}")

        # 4. A questo punto, i dati dovrebbero essere nel database 'raw_network_traffic'
        # Qui potresti chiamare una funzione per generare report o esportare dati dal DB.
        # collect_and_store_dataset(0) # Questo potrebbe essere usato per generare un CSV riassuntivo dal DB

        print("Simulazione completa terminata. Dati traffico nel database.")
        # ... (logica per GCS se vuoi un CSV riassuntivo del traffico catturato) ...

    threading.Thread(target=run_full_simulation).start()
    return jsonify({"status": "accepted", "message": f"Simulazione completa avviata in background per {simulation_duration} secondi."})

@app.route('/api/status', methods=['GET'])
def get_orchestrator_status():
    # ... (logica esistente) ...
    agent_types = {
        "Attacker Agent": ATTACKER_AGENT_URL,
        "Traffic Generator Agent": TRAFFIC_GENERATOR_AGENT_URL,
        # "Capture Agent": CAPTURE_AGENT_URL, # Rimuovi o rinomina il vecchio Capture Agent
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