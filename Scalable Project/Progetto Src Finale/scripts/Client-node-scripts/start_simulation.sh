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

echo "Esecuzione traffico benigno (loop infinito)..." | tee -a ${LOG_DIR}/simulation_status.log
# Avvia main.py e reindirizza l'output a un file di log.
# Il "nohup" e "&" servono a farlo girare in background anche se la sessione SSH si chiude.
#nohup python3 main.py >> ${LOG_DIR}/main_py_benign_output.log 2>&1 &
python3 main.py

#echo "La simulazione del traffico benigno è stata avviata in background." | tee -a ${LOG_DIR}/simulation_status.log
#echo "Controlla i log in ${LOG_DIR}/main_py_benign_output.log per l'output." | tee -a ${LOG_DIR}/simulation_status.log
#echo "Per terminare la simulazione, trova il processo python3 e uccidilo (es. pkill -f main.py)." | tee -a ${LOG_DIR}/simulation_status.log
