from flask import Flask, jsonify, request
import subprocess
import threading
import time
import os
from datetime import datetime
import re # Per parsing tcpdump
import signal

# Google Cloud SQL Connector
from google.cloud.sql.connector import Connector
import pymysql

app = Flask(__name__)

# Configurazione Cloud SQL
CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_DATABASE_NAME = os.environ.get('CLOUDSQL_DATABASE_NAME')
CLOUDSQL_USER_NAME = os.environ.get('CLOUDSQL_USER_NAME')
CLOUDSQL_USER_PASSWORD = os.environ.get('CLOUDSQL_USER_PASSWORD')

# Variabili globali per la cattura del traffico
tcpdump_process = None
capture_thread = None
stop_capture_event = threading.Event()

# Buffer per gli eventi catturati prima dell'inserimento nel DB
captured_traffic_buffer = []
BUFFER_THRESHOLD = 100 # Inserisci nel DB ogni 100 pacchetti o ogni 10 secondi
LAST_DB_INSERT_TIME = time.time()
BUFFER_TIME_LIMIT = 10 

connector = Connector() # Inizializza una sola volta

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
        # print("Connessione a Cloud SQL stabilita per Traffic Capture Agent.")
        return conn
    except Exception as e:
        print(f"Errore durante la connessione a Cloud SQL per Traffic Capture Agent: {e}")
        return None
def insert_traffic_data(data_list):
    """Inserisce una lista di record di traffico nel database raw_network_traffic."""
    if not data_list:
        return

    conn = None
    try:
        conn = get_cloudsql_conn()
        if conn:
            cursor = conn.cursor()
            insert_query = """
                INSERT INTO raw_network_traffic (
                    timestamp_capture, source_ip, destination_ip,
                    source_port, destination_port, protocol,
                    packet_length, flags, ttl, description, full_line, ingestion_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Converte i dizionari in tuple nell'ordine della query
            data_to_insert = [
                (d.get('timestamp_capture'), d.get('source_ip'), d.get('destination_ip'),
                 d.get('source_port'), d.get('destination_port'), d.get('protocol'),
                 d.get('packet_length'), d.get('flags'), d.get('ttl'), d.get('description'), d.get('full_line'), d.get('ingestion_time'))
                for d in data_list
            ]
            cursor.executemany(insert_query, data_to_insert)
            conn.commit()
            cursor.close()
            print(f"Inseriti {len(data_list)} record di traffico in raw_network_traffic.")
        else:
            print("Errore: Connessione DB non disponibile per inserimento traffico.")
    except Exception as e:
        print(f"Errore durante l'inserimento dati in raw_network_traffic: {e}")
    finally:
        if conn:
            conn.close()

def parse_tcpdump_line(line):
    """
    Parsifica una riga di output di tcpdump e restituisce un dizionario.
    tcpdump -l -n -ttt -vvv -e
    (timestamp) (ethernet_src) > (ethernet_dst), (eth_type) (len) (IP_info) (src_ip.port) > (dst_ip.port): (protocol_info)
    Esempio: 00:00:00.000000 02:42:0a:00:01:03 > 02:42:0a:00:03:02, ethertype IPv4 (0x0800), length 60: 10.0.1.3.56722 > 10.0.3.2.3306: Flags [S], seq 1234, win 65535, options [mss 1460,sackOK,TS val 12345678 ecr 0], length 0
    """
    data = {
        'timestamp_capture': None,
        'source_ip': None,
        'destination_ip': None,
        'source_port': None,
        'destination_port': None,
        'protocol': 'UNKNOWN',
        'packet_length': None,
        'flags': '', #None 
        'ttl': None,
        'description': '',
        'full_line': line.strip(),
        'ingestion_time': datetime.now()
    }
    # Aggiunta di un timestamp Unix in microsecondi
    data['timestamp_capture'] = int(time.time() * 1000000)

    length_match = re.search(r'length (\d+)', line)
    if length_match:
        try:
            data['packet_length'] = int(length_match.group(1))
        except ValueError:
            logger.warning(f"Impossibile parsare la lunghezza del pacchetto dalla riga: {line.strip()}")
            data['packet_length'] = None
            
    # Estrazione dell'indirizzo IP e delle porte
    ip_port_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d+)\s*>\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d+):', line)
    if ip_port_match:
        data['source_ip'] = ip_port_match.group(1)
        data['source_port'] = int(ip_port_match.group(2))
        data['destination_ip'] = ip_port_match.group(3)
        data['destination_port'] = int(ip_port_match.group(4))

    # Estrazione del protocollo (TCP, UDP, ICMP, ecc.)
    protocol_match = re.search(r':\s*(TCP|UDP|ICMP|ARP|IP)\b', line, re.IGNORECASE)
    if protocol_match:
        data['protocol'] = protocol_match.group(1).upper()
    else: 
        if 'Flags [' in line and 'UDP' not in line:
            data['protocol'] = 'TCP'
        elif 'UDP' in line:
            data['protocol'] = 'UDP'
        elif 'ICMP' in line:
            data['protocol'] = 'ICMP'
        elif 'udp' in line:
            data['protocol'] = 'UDP'
        elif 'ARP' in line:
            data['protocol'] = 'ARP'

    # Estrazione della lunghezza del pacchetto (se -l è usato, la lunghezza è spesso all'inizio della riga dopo ethertype)
    length_match = re.search(r'length (\d+):', line)
    if length_match:
        data['packet_length'] = int(length_match.group(1))

    # Estrazione dei flag TCP
    flags_match = re.search(r'Flags\s*\[([A-Z,]+)\]', line)
    if flags_match:
        data['flags'] = flags_match.group(1)

    # Estrazione del TTL
    ttl_match = re.search(r'ttl (\d+)', line)
    if ttl_match:
        data['ttl'] = int(ttl_match.group(1))

    # Aggiungi una descrizione sommaria
    data['description'] = f"{data['protocol']} packet from {data['source_ip']}:{data['source_port']} to {data['destination_ip']}:{data['destination_port']} (Len:{data['packet_length'] or 'N/A'})"

    return data

def capture_traffic_and_store_loop(interface='ens4'):
    """
    Cattura il traffico di rete e lo salva nel database.
    tcpdump -l: Line-buffered output
    tcpdump -n: Don't convert addresses to names
    tcpdump -ttt: Print timestamp in seconds and microseconds relative to the first packet
    tcpdump -vvv: Verbose output for more details
    tcpdump -e: Print the link-level header on each dump line
    """
    global tcpdump_process, captured_traffic_buffer, LAST_DB_INSERT_TIME

    print(f"DEBUG: Funzione capture_traffic_and_store_loop avviata con interfaccia: {interface}")

    # IP interno dell'attacker-node (per escludere il traffico locale di Flask)
    attacker_node_internal_ip = os.environ.get('ATTACKER_NODE_IP', '10.0.1.3')

    print(f"DEBUG: ATTACKER_NODE_IP: {attacker_node_internal_ip}")
    # Filtro per catturare solo il traffico interno tra i nodi della rete simulata
    filter_expression = "src net 10.0.0.0/8 and dst net 10.0.0.0/8"
    print(f"Avvio cattura traffico con tcpdump su interfaccia {interface}...")
    cmd = ['sudo', 'tcpdump', '-i', 'ens4', '-n', '-tttt', '-vvv', '-e', '-l', filter_expression]
    print(f"DEBUG: Comando tcpdump: {cmd}")
    
    try:
        tcpdump_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        print(f"DEBUG: tcpdump process avviato con PID: {tcpdump_process.pid}")
    except Exception as e:
        print(f"ERRORE GRAVE: Impossibile avviare tcpdump! Errore: {e}")
        return
    stderr_immediate = tcpdump_process.stderr.readline().strip()
    if stderr_immediate:
        print(f"ERRORE TCPDUMP IMMEDIATO (STDERR): {stderr_immediate}")
    else:
        print("DEBUG: Nessun errore immediato su stderr da tcpdump.")
    for line in iter(tcpdump_process.stdout.readline, ''):
        if stop_capture_event.is_set():
            print("Segnale di stop ricevuto. Termino cattura tcpdump.")
            break
        
        # Filtraggio di linee vuote o di warning/errore di tcpdump
        if not line.strip() or "listening on" in line or "dumping on" in line or "error" in line.lower():
            continue
        # Ignora traffico locale dell'attacker-node
        if "127.0.0.1" in line: 
             continue

        # Parsing della riga
        parsed_data = parse_tcpdump_line(line)
        # Ignora pacchetti senza IP di origine o destinazione
        if not parsed_data['source_ip'] or not parsed_data['destination_ip'] or \
           not (parsed_data['source_ip'].startswith('10.0.') or parsed_data['destination_ip'].startswith('10.0.')):
            continue 

        captured_traffic_buffer.append(parsed_data)

        # Inserire i dati nel DB in batch
        current_time = time.time()
        if len(captured_traffic_buffer) >= BUFFER_THRESHOLD or \
           (current_time - LAST_DB_INSERT_TIME >= BUFFER_TIME_LIMIT and captured_traffic_buffer):
            print(f"Salvando {len(captured_traffic_buffer)} pacchetti nel DB...")
            insert_traffic_data(captured_traffic_buffer)
            captured_traffic_buffer.clear()
            LAST_DB_INSERT_TIME = current_time

    # Una volta che il loop si interrompe, si svuota il buffer finale
    if captured_traffic_buffer:
        print(f"Salvando i pacchetti rimanenti ({len(captured_traffic_buffer)}) nel DB...")
        insert_traffic_data(captured_traffic_buffer)
        captured_traffic_buffer.clear()

    # Attesa del processo tcpdump che termini completamente
    tcpdump_process.wait()
    print("Cattura traffico tcpdump terminata.")

@app.route('/start_capture', methods=['POST'])
def start_capture():
    global tcpdump_process, capture_thread, stop_capture_event
    if tcpdump_process is not None and tcpdump_process.poll() is None:
        return jsonify({"status": "error", "message": "Cattura traffico già in corso."}), 400

    interface = request.json.get('interface', 'ens4')
    
    stop_capture_event.clear()
    capture_thread = threading.Thread(target=capture_traffic_and_store_loop, args=(interface,))
    capture_thread.daemon = True
    capture_thread.start()
    return jsonify({"status": "success", "message": f"Cattura traffico avviata su {interface}."})

@app.route('/stop_capture', methods=['POST'])
def stop_capture():
    global tcpdump_process, stop_capture_event
    if tcpdump_process is None or tcpdump_process.poll() is not None:
        return jsonify({"status": "error", "message": "Nessuna cattura traffico in corso da fermare."}), 400

    stop_capture_event.set() 

    try: 
        tcpdump_process.send_signal(signal.SIGINT)
        print("Inviato SIGINT a tcpdump_process.")
    except Exception as e:
        print(f"ATTENZIONE: Errore nell'invio di SIGINT a tcpdump: {e}")

    if capture_thread and capture_thread.is_alive():
        print("Attendendo la terminazione del thread di cattura...")
        capture_thread.join(timeout=5)
        if capture_thread.is_alive():
            print("Il thread di cattura non è terminato entro il timeout.")

    tcpdump_process = None
    return jsonify({"status": "success", "message": "Cattura traffico terminata."})

@app.route('/status', methods=['GET'])
def get_status():
    global tcpdump_process
    is_running = tcpdump_process is not None and tcpdump_process.poll() is None
    return jsonify({"status": "Traffic Capture Agent running", "capture_active": is_running, "timestamp": time.time()})

if __name__ == '__main__':
    print("Avvio Flask Traffic Capture Agent su http://127.0.0.1:5003")
    app.run(host='127.0.0.1', port=5003, debug=False)
