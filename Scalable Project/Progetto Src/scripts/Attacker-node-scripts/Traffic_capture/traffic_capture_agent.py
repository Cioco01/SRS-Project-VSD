from flask import Flask, jsonify, request
import subprocess
import threading
import time
import os
from datetime import datetime
import re # Per parsing tcpdump

# Google Cloud SQL Connector
from google.cloud.sql.connector import Connector
import pymysql

app = Flask(__name__)

# --- Configurazione Cloud SQL ---
CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_DATABASE_NAME = os.environ.get('CLOUDSQL_DATABASE_NAME')
CLOUDSQL_USER_NAME = os.environ.get('CLOUDSQL_USER_NAME')
CLOUDSQL_USER_PASSWORD = os.environ.get('CLOUDSQL_USER_PASSWORD')

# Global state for tcpdump process
tcpdump_process = None
capture_thread = None
stop_capture_event = threading.Event()

# Buffer per gli eventi catturati prima dell'inserimento nel DB
captured_traffic_buffer = []
BUFFER_THRESHOLD = 50 # Inserisci nel DB ogni 50 pacchetti o ogni 10 secondi
LAST_DB_INSERT_TIME = time.time()
BUFFER_TIME_LIMIT = 10 # secondi

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
                    packet_length, flags, ttl, description, full_line
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Converte i dizionari in tuple nell'ordine della query
            data_to_insert = [
                (d.get('timestamp_capture'), d.get('source_ip'), d.get('destination_ip'),
                 d.get('source_port'), d.get('destination_port'), d.get('protocol'),
                 d.get('packet_length'), d.get('flags'), d.get('ttl'), d.get('description'), d.get('full_line'))
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
        'full_line': line.strip() #line #codicevecchio
    }

    # Timestamp (unix timestamp from relative, or use current time if relative not parsed)
    # The -ttt option gives microsecond-precision relative to the first packet
    # It's safer to use current time for absolute timestamp or configure tcpdump differently
    data['timestamp_capture'] = int(time.time() * 1000000) # Microseconds Unix timestamp

    #------PEZZO NUOVO 10/07 forse cancella da QUI------
    length_match = re.search(r'length (\d+)', line)
    if length_match:
        try:
            data['packet_length'] = int(length_match.group(1))
        except ValueError:
            logger.warning(f"Impossibile parsare la lunghezza del pacchetto dalla riga: {line.strip()}")
            data['packet_length'] = None
    #-------- A QUI-------	
    # Try to extract IP addresses and ports
    ip_port_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d+)\s*>\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d+):', line)
    if ip_port_match:
        data['source_ip'] = ip_port_match.group(1)
        data['source_port'] = int(ip_port_match.group(2))
        data['destination_ip'] = ip_port_match.group(3)
        data['destination_port'] = int(ip_port_match.group(4))

    # Try to extract protocol (TCP, UDP, ICMP, etc.)
    protocol_match = re.search(r':\s*(TCP|UDP|ICMP|ARP|IP)\b', line, re.IGNORECASE)
    if protocol_match:
        data['protocol'] = protocol_match.group(1).upper()
    else: # Fallback to a broader pattern for common protocols
        if 'Flags [' in line and 'UDP' not in line:
            data['protocol'] = 'TCP'
        elif 'UDP,' in line:
            data['protocol'] = 'UDP'
        elif 'ICMP,' in line:
            data['protocol'] = 'ICMP'
        elif 'ARP,' in line:
            data['protocol'] = 'ARP'

    # Extract packet length (if -l is used, length is often at the beginning of the line after ethertype)
    length_match = re.search(r'length (\d+):', line)
    if length_match:
        data['packet_length'] = int(length_match.group(1))

    # Extract TCP flags
    flags_match = re.search(r'Flags\s*\[([A-Z,]+)\]', line)
    if flags_match:
        data['flags'] = flags_match.group(1)

    # Extract TTL
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

    print(f"DEBUG: Funzione capture_traffic_and_store_loop avviata con interfaccia: {interface}") # NUOVA RIGA

    # Monitora l'interfaccia interna (subnet DMZ e private)
    # L'IP dell'attacker-node-01 è 10.0.1.3
    # L'interfaccia corretta dovrebbe essere quella collegata alla netchaos_vpc (es. eth0)
    # Se vuoi catturare tutto il traffico interno, non specificare un host.
    # Ma se vuoi solo il traffico che passa attraverso questa macchina o la riguarda,
    # potresti voler aggiungere filtri.
    # tcpdump -i eth0 -n -tttt -vvv -e -l # Cattura tutto su eth0

    # Filtro BPF per escludere il traffico SSH di gestione (se stai usando SSH sulla stessa interfaccia)
    # e il traffico verso l'IP pubblico dell'attacker-node, concentrandoti sulla rete interna.
    # L'IP interno di attacker-node-01 è 10.0.1.3
    # Se il data viewer è accessibile dall'esterno, potresti vedere traffico verso 35.195.245.74
    # che non è traffico "interno alla simulazione".
    # Filtriamo per il traffico all'interno della subnet 10.0.0.0/8
    # Questo escluderà anche il traffico tra l'orchestratore e i suoi agenti su 127.0.0.1

    # Ottieni l'IP interno dell'attacker-node (per escludere il traffico locale di Flask)
    attacker_node_internal_ip = os.environ.get('ATTACKER_NODE_IP', '10.0.1.3') # Usa la variabile d'ambiente

    print(f"DEBUG: ATTACKER_NODE_IP: {attacker_node_internal_ip}") # NUOVA RIGA

    # BPF filter: Cattura tutto il traffico che non sia sul localhost e non sia l'IP pubblico della VM,
    # e che sia diretto o provenga da un'altra VM interna (es. 10.0.x.x)
    # NOTA: Questo filtro è complesso e potrebbe aver bisogno di tuning.
    # Per semplicità, inizialmente potresti catturare tutto e filtrare in Python.
    # filter_expression = f"not (host 127.0.0.1) and net 10.0.0.0/8" # Cattura traffico interno
    # O più semplice per il traffico IN/OUT della VM sull'interfaccia di rete interna
    filter_expression = "src net 10.0.0.0/8 and dst net 10.0.0.0/8" # Lasciamo vuoto per catturare tutto su eth0, poi filtriamo in Python.
                           # O possiamo specificare l'interfaccia di rete VPC es. eth0
                           # tcpdump -i eth0 ...

    print(f"Avvio cattura traffico con tcpdump su interfaccia {interface}...")

    # Assicurati che l'utente 'cristian_ciocoiu' possa eseguire tcpdump senza password (già fatto nello startup script)
    # sudo tcpdump -i eth0 -n -tttt -vvv -e -l
    cmd = ['sudo', 'tcpdump', '-i', 'ens4', '-n', '-tttt', '-vvv', '-e', '-l', filter_expression]
    print(f"DEBUG: Comando tcpdump: {cmd}") # NUOVA RIGA
    
    try: # Aggiungi un blocco try-except qui per catturare errori di subprocess.Popen
        tcpdump_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        print(f"DEBUG: tcpdump process avviato con PID: {tcpdump_process.pid}") # NUOVA RIGA
    except Exception as e:
        print(f"ERRORE GRAVE: Impossibile avviare tcpdump! Errore: {e}") # NUOVA RIGA
        return # Esci dalla funzione se tcpdump non parte    
    # Leggi subito stderr per vedere errori di avvio di tcpdump
    stderr_immediate = tcpdump_process.stderr.readline().strip() # QUESTA È LA RIGA DA MANTENERE SE L'ABBIAMO AGGIUNTA
    if stderr_immediate:
        print(f"ERRORE TCPDUMP IMMEDIATO (STDERR): {stderr_immediate}")
    # Considera di terminare qui o di loggare in modo più severo se questo è un errore critico
    else:
        print("DEBUG: Nessun errore immediato su stderr da tcpdump.")	
    for line in iter(tcpdump_process.stdout.readline, ''):
        if stop_capture_event.is_set():
            print("Segnale di stop ricevuto. Termino cattura tcpdump.")
            break
        
        # Filtra linee vuote o di warning/errore di tcpdump
        if not line.strip() or "listening on" in line or "dumping on" in line or "error" in line.lower():
            continue

        # Non catturare il traffico loopback (127.0.0.1) o traffico specifico dell'orchestratore/agenti Flask
        # che non è traffico di simulazione di rete.
        # L'IP dell'orchestratore/attacker_agent è 10.0.1.3 (IP interno)
        # e interagiscono tra loro su 127.0.0.1.
        if "127.0.0.1" in line: # Exclude localhost traffic
             continue

        # Parsing della riga
        parsed_data = parse_tcpdump_line(line)

        # Filtra ulteriormente se i dati non sono validi o non rientrano nella simulazione interna
        if not parsed_data['source_ip'] or not parsed_data['destination_ip'] or \
           not (parsed_data['source_ip'].startswith('10.0.') or parsed_data['destination_ip'].startswith('10.0.')):
            continue # Salta pacchetti non pertinenti alla rete interna 10.0.x.x

        captured_traffic_buffer.append(parsed_data)

        # Inserisci i dati nel DB in batch
        current_time = time.time()
        if len(captured_traffic_buffer) >= BUFFER_THRESHOLD or \
           (current_time - LAST_DB_INSERT_TIME >= BUFFER_TIME_LIMIT and captured_traffic_buffer):
            print(f"Salvando {len(captured_traffic_buffer)} pacchetti nel DB...")
            insert_traffic_data(captured_traffic_buffer)
            captured_traffic_buffer.clear()
            LAST_DB_INSERT_TIME = current_time

    # Una volta che il loop si interrompe, svuota il buffer finale
    if captured_traffic_buffer:
        print(f"Salvando i pacchetti rimanenti ({len(captured_traffic_buffer)}) nel DB...")
        insert_traffic_data(captured_traffic_buffer)
        captured_traffic_buffer.clear()

    # Attendi che il processo tcpdump termini completamente
    tcpdump_process.wait()
    print("Cattura traffico tcpdump terminata.")

# Endpoint Flask per controllare la cattura
@app.route('/start_capture', methods=['POST'])
def start_capture():
    global tcpdump_process, capture_thread, stop_capture_event
    if tcpdump_process is not None and tcpdump_process.poll() is None:
        return jsonify({"status": "error", "message": "Cattura traffico già in corso."}), 400

    interface = request.json.get('interface', 'ens4') # Interfaccia di rete da monitorare
    
    stop_capture_event.clear()
    capture_thread = threading.Thread(target=capture_traffic_and_store_loop, args=(interface,))
    capture_thread.daemon = True # Permetti al thread di terminare con l'applicazione Flask
    capture_thread.start()
    return jsonify({"status": "success", "message": f"Cattura traffico avviata su {interface}."})

@app.route('/stop_capture', methods=['POST'])
def stop_capture():
    global tcpdump_process, stop_capture_event
    if tcpdump_process is None or tcpdump_process.poll() is not None:
        return jsonify({"status": "error", "message": "Nessuna cattura traffico in corso da fermare."}), 400

    stop_capture_event.set() # Segnala al thread di cattura di fermarsi
    # tcpdump_process.terminate() # Invia SIGTERM a tcpdump
    tcpdump_process.send_signal(subprocess.SIGINT) # Invia CTRL+C a tcpdump per una chiusura più pulita
    
    # Aspetta un breve periodo che il thread di cattura si pulisca
    if capture_thread and capture_thread.is_alive():
        capture_thread.join(timeout=5)

    tcpdump_process = None # Resetta lo stato
    return jsonify({"status": "success", "message": "Cattura traffico terminata."})

@app.route('/status', methods=['GET'])
def get_status():
    global tcpdump_process
    is_running = tcpdump_process is not None and tcpdump_process.poll() is None
    return jsonify({"status": "Traffic Capture Agent running", "capture_active": is_running, "timestamp": time.time()})

if __name__ == '__main__':
    print("Avvio Flask Traffic Capture Agent su http://127.0.0.1:5003")
    # Usa la porta 5003, la stessa usata in orchestrator_backend per CAPTURE_AGENT_URL
    # Debug=False per produzione
    app.run(host='127.0.0.1', port=5003, debug=False)
