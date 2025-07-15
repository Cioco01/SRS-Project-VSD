# scripts/main.py
import yaml
import os
import time
from datetime import datetime
import random # <--- AGGIUNTO PER LA CASUALITÀ

from http_simulator import simulate_http_traffic
from dns_simulator import simulate_dns_queries
from db_simulator import simulate_db_access

def run_simulation_cycle(config_path="config.yaml"):
    """
    Esegue un ciclo di simulazione del traffico benigno o maligno, leggendo la configurazione.
    Gli IP dei server sono letti dalle variabili d'ambiente.
    Le simulazioni vengono scelte casualmente in base alle opzioni di configurazione.
    """
    web_server_ip = os.getenv("WEB_SERVER_IP")
    dns_server_ip = os.getenv("DNS_SERVER_IP")
    db_server_ip = os.getenv("DB_SERVER_IP")

    # Fallback per test locale (non raccomandato per GCP)
    if not all([web_server_ip, dns_server_ip, db_server_ip]):
        try:
            with open(config_path, 'r') as f:
                config_from_file = yaml.safe_load(f)
            web_server_ip = web_server_ip or config_from_file.get('web_server_ip', '127.0.0.1')
            dns_server_ip = dns_server_ip or config_from_file.get('dns_server_ip', '8.8.8.8')
            db_server_ip = db_server_ip or config_from_file.get('db_server_ip', '127.0.0.1')
        except FileNotFoundError:
            print(f"Errore: {config_path} non trovato. Non posso usare IP di fallback dal file.")
            web_server_ip = web_server_ip or '127.0.0.1'
            dns_server_ip = dns_server_ip or '8.8.8.8'
            db_server_ip = db_server_ip or '127.0.0.1'
        print("Errore: Variabili d'ambiente (WEB_SERVER_IP, DNS_SERVER_IP, DB_SERVER_IP) non impostate.")
        print("Assicurati che lo script di avvio di Terraform le abbia passate correttamente o di essere sulla VM.")
        print(f"Usando IP di fallback: Web={web_server_ip}, DNS={dns_server_ip}, DB={db_server_ip}\n")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    print(f"--- Inizio Ciclo di Simulazione ---")
    print(f"Configurazione anomalie abilitate: DNS Spike={config.get('simulate_dns_spike', False)}, HTTP Port Change={config.get('simulate_http_port_change', False)}, Unusual DB Client={config.get('simulate_unusual_db_client', False)}\n")

    # --- DEFINIZIONE DELLE AZIONI POSSIBILI ---
    # Creiamo un elenco di funzioni (azioni) che possono essere scelte casualmente.
    # Le azioni anomale vengono aggiunte solo se abilitate nel config.yaml.
    
    possible_actions = []

    # Azioni HTTP
    possible_actions.append(lambda: simulate_http_traffic(web_server_ip, port=80, num_requests=random.randint(3, 7)))
    if config.get("simulate_http_port_change", False):
        possible_actions.append(lambda: simulate_http_traffic(web_server_ip, port=8081, num_requests=random.randint(3, 7)))

    # Azioni DNS
    domains = ["example.com", "google.com", "unibo.it", "wikipedia.org", "github.com"]
    possible_actions.append(lambda: simulate_dns_queries(dns_server_ip, domains, spike=False))
    if config.get("simulate_dns_spike", False):
        possible_actions.append(lambda: simulate_dns_queries(dns_server_ip, domains, spike=True))

    # Azioni DB
    possible_actions.append(lambda: simulate_db_access(db_server_ip, user="sim_user", password="password", anomaly=False))
    if config.get("simulate_unusual_db_client", False):
        possible_actions.append(lambda: simulate_db_access(db_server_ip, user="sim_user", password="password", anomaly=True))

    # --- ESECUZIONE CASUALE DELLE AZIONI ---
    # Decidi quante azioni eseguire in questo ciclo (es. tra 1 e 3)
    num_actions_to_execute = random.randint(1, len(possible_actions)) 
    
    # Seleziona casualmente N azioni uniche dall'elenco
    selected_actions = random.sample(possible_actions, num_actions_to_execute)

    print(f"Esecuzione di {num_actions_to_execute} azioni casuali in questo ciclo:")
    for i, action in enumerate(selected_actions):
        print(f"  - Esecuzione azione {i+1}/{num_actions_to_execute}...")
        try:
            action() # Chiama la funzione dell'azione selezionata
            time.sleep(random.uniform(0.5, 2.0)) # Breve pausa tra le azioni all'interno dello stesso ciclo
        except Exception as e:
            print(f"ATTENZIONE: Errore durante l'esecuzione di un'azione casuale: {e}")
            # Non bloccare l'intera simulazione per un singolo errore di azione

    print(f"\n--- Fine Ciclo di Simulazione ---\n")
    
# Punto di ingresso principale
if __name__ == "__main__":
    config_file_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    
    simulation_cycle_duration = 1 # Secondi tra un ciclo e l'altro. Puoi modificarlo.

    while True:
        run_simulation_cycle(config_path=config_file_path)
        time.sleep(simulation_cycle_duration)
