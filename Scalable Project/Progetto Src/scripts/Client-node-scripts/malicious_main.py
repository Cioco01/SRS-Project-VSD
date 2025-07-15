# scripts/malicious_main.py
import yaml
import os
from port_scan_simulator import simulate_port_scan
from brute_force_simulator import simulate_ssh_brute_force
from malware_drop_simulator import simulate_malware_drop
from lateral_movement_simulator import simulate_lateral_movement

def run_malicious_simulation_cycle(config_path="malicious_config.yaml"):
    """
    Esegue un ciclo di simulazione del traffico maligno, leggendo la configurazione.
    """
    config = {}
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Avviso: {config_path} non trovato. Gli attacchi non verranno simulati.")
        return # Non procedere se la config non c'è
    except yaml.YAMLError as e:
        print(f"Errore nel parsing di {config_path}: {e}. Gli attacchi non verranno simulati.")
        return

    print("\n--- Inizio Ciclo di Simulazione Maligna ---")

    # Port Scanning
    if config.get("enable_port_scan", False):
        print("\n--- Esecuzione Simulazione Port Scan ---")
        simulate_port_scan(
            target_ip_range=config["port_scan_target_ip_range"],
            scan_type=config["port_scan_type"],
            ports=config["port_scan_ports"]
        )

    # Brute-Force SSH
    if config.get("enable_brute_force_ssh", False):
        print("\n--- Esecuzione Simulazione Brute-Force SSH ---")
        simulate_ssh_brute_force(
            target_ip=config["brute_force_ssh_target_ip"],
            username=config["brute_force_ssh_username"],
            passwords=config["brute_force_ssh_passwords"]
        )

    # Malware Drop Simulation
    if config.get("enable_malware_drop", False):
        print("\n--- Esecuzione Simulazione Malware Drop ---")
        simulate_malware_drop(
            c2_domains=config["malware_drop_c2_domains"],
            file_paths=config["malware_drop_file_paths"],
            simulated_size_kb=config["malware_drop_simulated_size_kb"]
        )

    # Lateral Movement Simulation
    if config.get("enable_lateral_movement", False):
        print("\n--- Esecuzione Simulazione Movimento Laterale ---")
        simulate_lateral_movement(
            target_ips=config["lateral_movement_target_ips"],
            credentials=config["lateral_movement_credentials"]
        )

    print("\n--- Fine Ciclo di Simulazione Maligna ---")

if __name__ == '__main__':
    # Quando eseguito direttamente, prova a usare il malicious_config.yaml locale
    run_malicious_simulation_cycle(config_path=os.path.join(os.path.dirname(__file__), "malicious_config.yaml"))