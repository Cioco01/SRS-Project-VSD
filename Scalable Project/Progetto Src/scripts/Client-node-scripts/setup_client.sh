#!/bin/bash
echo "--- Aggiornamento sistema e installazione dipendenze ---"
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip nmap git

# --- 1. Installare le dipendenze Python
pip3 install requests dnspython PyYAML mysql-connector-python paramiko

# --- 2. Creare directory per gli script e i log ---
SIM_DIR="/opt/simulation"
LOG_DIR="/var/log/simulation"

echo "--- Creazione directory: ${SIM_DIR} e ${LOG_DIR} ---"
sudo mkdir -p "${SIM_DIR}"
sudo mkdir -p "${LOG_DIR}"
sudo chmod 777 "${LOG_DIR}" # Permessi ampi per il testing

# --- 3. Copiare gli script Python e i file di configurazione ---

echo "--- Copia script in ${SIM_DIR} ---"
# Spostare tutti i file necessari in /opt/simulation
sudo mv /tmp/*.py "${SIM_DIR}/"
sudo mv /tmp/*.yaml "${SIM_DIR}/" # Copierà config.yaml e malicious_config.yaml
sudo mv /tmp/start_simulation.sh "${SIM_DIR}/"

# Rendi lo script di avvio della simulazione eseguibile
sudo chmod +x "${SIM_DIR}/start_simulation.sh"

# --- 4. Impostare le variabili d'ambiente dagli metadati di Terraform ---

echo "--- Impostazione variabili d'ambiente da metadati Terraform ---"
WEB_SERVER_IP="${WEB_SERVER_IP_METADATA}" 
DNS_SERVER_IP="${DNS_SERVER_IP_METADATA}"   
DB_SERVER_IP="${DB_SERVER_IP_METADATA}"     

echo "WEB_SERVER_IP: ${WEB_SERVER_IP}"
echo "DNS_SERVER_IP: ${DNS_SERVER_IP}"
echo "DB_SERVER_IP: ${DB_SERVER_IP}"

# --- 5. Aggiorare i percorsi hardcoded in main.py (e malicious_main.py se simile) ---
echo "--- Correzione percorsi file di configurazione negli script Python ---"
sudo sed -i "s|r\"C:\\\\Users\\\\loren\\\\Desktop\\\\Uni\\\\Scalable test prova\\\\config.yaml\"|'${SIM_DIR}/config.yaml'|g" "${SIM_DIR}/main.py"


# --- 6. Sostituire gli IP placeholder nei file di configurazione YAML ---
echo "--- Sostituzione IP placeholder nei file YAML ---"
sudo sed -i "s/web_server_ip: 127.0.0.1/web_server_ip: ${WEB_SERVER_IP}/g" "${SIM_DIR}/config.yaml"
sudo sed -i "s/dns_server_ip: 8.8.8.8/dns_server_ip: ${DNS_SERVER_IP}/g" "${SIM_DIR}/config.yaml"
sudo sed -i "s/db_server_ip: 127.0.0.1/db_server_ip: ${DB_SERVER_IP}/g" "${SIM_DIR}/config.yaml"

# --- 7. Avviare lo script di simulazione in background ---
echo "--- Avvio simulazione in background ---"
cd "${SIM_DIR}"
sudo nohup bash start_simulation.sh > "${LOG_DIR}/overall_simulation_startup.log" 2>&1 &

# --- 8. Abilita SSH ---
sudo sed -i 's/^#\?PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart ssh

echo "Client setup complete. Simulation started in background." | sudo tee -a "${LOG_DIR}/overall_simulation_startup.log"