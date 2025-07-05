# scripts/main.py
import yaml
import os
import time # Aggiunto per il loop di runtime
from http_simulator import simulate_http_traffic
from dns_simulator import simulate_dns_queries
from db_simulator import simulate_db_access

def run_simulation_cycle(config_path="config.yaml"):
    """
    Esegue un ciclo di simulazione del traffico benigno, leggendo la configurazione.
    Gli IP dei server sono letti dalle variabili d'ambiente.
    """
    web_server_ip = os.getenv("WEB_SERVER_IP")
    dns_server_ip = os.getenv("DNS_SERVER_IP")
    db_server_ip = os.getenv("DB_SERVER_IP")

    if not all([web_server_ip, dns_server_ip, db_server_ip]):
        print("Errore: Variabili d'ambiente (WEB_SERVER_IP, DNS_SERVER_IP, DB_SERVER_IP) non impostate.")
        print("Assicurati che lo script di avvio di Terraform le abbia passate correttamente.")
        # Fallback per test locale, ma non raccomandato per GCP
        web_server_ip = web_server_ip or "127.0.0.1"
        dns_server_ip = dns_server_ip or "8.8.8.8"
        db_server_ip = db_server_ip or "127.0.0.1"
        print(f"Usando IP di fallback: Web={web_server_ip}, DNS={dns_server_ip}, DB={db_server_ip}")


    config = {}
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Avviso: {config_path} non trovato. Le anomalie non verranno simulate.")
    except yaml.YAMLError as e:
        print(f"Errore nel parsing di {config_path}: {e}. Le anomalie non verranno simulate.")

    # Imposta valori di default se le chiavi non sono presenti o se config.yaml non è stato caricato
    simulate_dns_spike = config.get("simulate_dns_spike", False)
    simulate_http_port_change = config.get("simulate_http_port_change", False)
    simulate_unusual_db_client = config.get("simulate_unusual_db_client", False)


    print("\n--- Inizio Ciclo di Simulazione Benigna ---")
    print(f"Configurazione anomalie: DNS Spike={simulate_dns_spike}, HTTP Port Change={simulate_http_port_change}, Unusual DB Client={simulate_unusual_db_client}")

    # HTTP Traffic
    print("\n--- Simulazione Traffico HTTP ---")
    simulate_http_traffic(web_server_ip, port=80, num_requests=5)
    if simulate_http_port_change:
        print("\n--- Simulazione Anomalia HTTP (Porta 8081) ---")
        simulate_http_traffic(web_server_ip, port=8081, num_requests=5)

    # DNS Queries
    print("\n--- Simulazione Query DNS ---")
    domains = ["example.com", "google.com", "unibo.it", "wikipedia.org", "github.com"]
    simulate_dns_queries(dns_server_ip, domains, spike=False, num_queries=5)
    if simulate_dns_spike:
        print("\n--- Simulazione Anomalia DNS (Spike) ---")
        simulate_dns_queries(dns_server_ip, domains, spike=True, num_queries=50)


    # DB Access
    print("\n--- Simulazione Accesso DB ---")
    # Usa le credenziali definite nel modulo Cloud SQL
    simulate_db_access(db_server_ip, user="sim_user", password="your_strong_password", anomaly=False)
    if simulate_unusual_db_client:
        print("\n--- Simulazione Anomalia DB (Accesso Inusuale) ---")
        # Tentativo con un database insolito, dovrebbe fallire se le permessi non sono concessi
        simulate_db_access(db_server_ip, user="sim_user", password="your_strong_password", anomaly=True)

    print("\n--- Fine Ciclo di Simulazione Benigna ---")

if __name__ == '__main__':
    # Quando eseguito direttamente, prova a usare il config.yaml locale
    # In GCP, questo script verrà chiamato da start_traffic_gen.sh con variabili d'ambiente
    run_simulation_cycle(config_path=os.path.join(os.path.dirname(__file__), "config.yaml"))