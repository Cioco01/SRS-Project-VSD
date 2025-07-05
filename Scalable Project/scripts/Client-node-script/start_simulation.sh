#!/bin/bash
# scripts/start_simulation.sh
# Questo script viene avviato dal setup_client.sh e gira in loop sul client GCE
# Orchestrerà sia il traffico benigno che quello maligno.

LOG_DIR="/var/log/simulation" # Directory centralizzata per tutti i log
mkdir -p ${LOG_DIR} # Assicurati che la directory esista

# Ottieni l'IP effettivo del client (utile per i log)
CLIENT_IP=$(hostname -I | awk '{print $1}')

# Esporta le variabili d'ambiente per gli script Python (vengono da setup_client.sh)
export WEB_SERVER_IP
export DNS_SERVER_IP
export DB_SERVER_IP

cd /opt/simulation # Entra nella directory dove sono stati copiati gli script Python

echo "Starting overall simulation loop..." | tee -a ${LOG_DIR}/simulation_status.log
echo "WEB_SERVER_IP: $WEB_SERVER_IP" | tee -a ${LOG_DIR}/simulation_status.log
echo "DNS_SERVER_IP: $DNS_SERVER_IP" | tee -a ${LOG_DIR}/simulation_status.log
echo "DB_SERVER_IP: $DB_SERVER_IP" | tee -a ${LOG_DIR}/simulation_status.log

while true; do
    echo "--- $(date) - Inizio ciclo di simulazione completo ---" | tee -a ${LOG_DIR}/simulation_status.log

    echo "Esecuzione traffico benigno..." | tee -a ${LOG_DIR}/simulation_status.log
    python3 main.py >> ${LOG_DIR}/main_py_benign_output.log 2>&1
    
    echo "Esecuzione traffico maligno..." | tee -a ${LOG_DIR}/simulation_status.log
    python3 malicious_main.py >> ${LOG_DIR}/main_py_malicious_output.log 2>&1

    echo "--- $(date) - Fine ciclo di simulazione completo. Pausa di 60 secondi ---" | tee -a ${LOG_DIR}/simulation_status.log
    sleep 60 # Pausa di un minuto tra un ciclo di simulazione e l'altro
done