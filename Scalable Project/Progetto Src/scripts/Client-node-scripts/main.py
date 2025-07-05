# scripts/main.py
import yaml
import os
import time # Aggiunto per il loop di runtime
from http_simulator import simulate_http_traffic
from dns_simulator import simulate_dns_queries
from db_simulator import simulate_db_access

def run_simulation_cycle(config_path="config.yaml"):
    """
    Esegue un ciclo di simulazione del traffico benigno o maligno, leggendo la configurazione.
    Gli IP dei server sono letti dalle variabili d'ambiente.
    """
    web_server_ip = os.getenv("WEB_SERVER_IP")
    dns_server_ip = os.getenv("DNS_SERVER_IP")
    db_server_ip = os.getenv("DB_SERVER_IP")

    # Fallback per test locale (non raccomandato per GCP)
    if not all([web_server_ip, dns_server_ip, db_server_ip]):
        # Rileggi la configurazione dal file per gli IP se le variabili d'ambiente non sono impostate
        # Questo è il tuo caso quando lo esegui localmente, ma NON sulla VM
        try:
            with open(config_path, 'r') as f:
                config_from_file = yaml.safe_load(f)
            web_server_ip = web_server_ip or config_from_file.get('web_server_ip', '127.0.0.1')
            dns_server_ip = dns_server_ip or config_from_file.get('dns_server_ip', '8.8.8.8')
            db_server_ip = db_server_ip or config_from_file.get('db_server_ip', '127.0.0.1')
        except FileNotFoundError:
            print(f"Errore: {config_path} non trovato. Non posso usare IP di fallback dal file.")
            # Se nemmeno il file è trovato, usa i default hardcoded
            web_server_ip = web_server_ip or '127.0.0.1'
            dns_server_ip = dns_server_ip or '8.8.8.8'
            db_server_ip = db_server_ip or '127.0.0.1'
        print("Errore: Variabili d'ambiente (WEB_SERVER_IP, DNS_SERVER_IP, DB_SERVER_IP) non impostate.")
        print("Assicurati che lo script di avvio di Terraform le abbia passate correttamente o di essere sulla VM.")
        print(f"Usando IP di fallback: Web={web_server_ip}, DNS={dns_server_ip}, DB={db_server_ip}\n")


    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    print(f"--- Inizio Ciclo di Simulazione ---")
    print(f"Configurazione anomalie: DNS Spike={config['simulate_dns_spike']}, HTTP Port Change={config['simulate_http_port_change']}, Unusual DB Client={config['simulate_unusual_db_client']}\n")

    # --- Simulazione Traffico HTTP ---
    print("--- Simulazione Traffico HTTP ---")
    simulate_http_traffic(web_server_ip, port=80, num_requests=5)
    if config.get("simulate_http_port_change", False): # Usa .get per sicurezza
        print("\n--- Simulazione Anomalia HTTP (Porta 8081) ---")
        simulate_http_traffic(web_server_ip, port=8081, num_requests=5)
    print()

    # --- Simulazione Query DNS ---
    print("--- Simulazione Query DNS ---")
    domains = ["example.com", "google.com", "unibo.it", "wikipedia.org", "github.com"]
    # CORREZIONE QUI: RIMOSSO 'num_queries=5'
    simulate_dns_queries(dns_server_ip, domains, spike=config["simulate_dns_spike"])
    if config.get("simulate_dns_spike", False): # Usa .get per sicurezza
        print("\n--- Simulazione Anomalia DNS (Spike) ---")
        # CORREZIONE QUI: RIMOSSO 'num_queries=50'
        simulate_dns_queries(dns_server_ip, domains, spike=True)
    print()

    # --- Simulazione Accesso DB ---
    print("--- Simulazione Accesso DB ---")
    # Usa le credenziali definite nel modulo Cloud SQL
    simulate_db_access(db_server_ip, user="sim_user", password="your_strong_password", anomaly=False)
    if config.get("simulate_unusual_db_client", False): # Usa .get per sicurezza
        print("\n--- Simulazione Anomalia DB (Accesso Inusuale) ---")
        # Tentativo con un database insolito, dovrebbe fallire se le permessi non sono concessi
        simulate_db_access(db_server_ip, user="sim_user", password="your_strong_password", anomaly=True)
    print()

    # Questo ciclo continua a eseguire le simulazioni indefinitamente
    # Puoi aggiungere un contatore o una condizione di uscita se desideri un numero finito di cicli
    # while True:
    #     print(f"--- Ciclo di simulazione in corso ({time.time()}) ---")
    #     time.sleep(60) # Attendi un minuto prima del prossimo ciclo

# Punto di ingresso principale
if __name__ == "__main__":
    # Il percorso a config.yaml dovrebbe essere relativo alla posizione di main.py
    run_simulation_cycle(config_path=os.path.join(os.path.dirname(__file__), "config.yaml"))