#!/bin/bash
# scripts/setup_client.sh
# Script di startup per l'istanza client GCE

# --- 1. Aggiorna sistema e installa dipendenze base ---
echo "--- Aggiornamento sistema e installazione dipendenze ---"
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip nmap git

# Installa le dipendenze Python
pip3 install requests dnspython PyYAML mysql-connector-python paramiko

# --- 2. Crea directory per gli script e i log ---
SIM_DIR="/opt/simulation"
LOG_DIR="/var/log/simulation"

echo "--- Creazione directory: ${SIM_DIR} e ${LOG_DIR} ---"
sudo mkdir -p "${SIM_DIR}"
sudo mkdir -p "${LOG_DIR}"
sudo chmod 777 "${LOG_DIR}" # Permessi ampi per il testing

# --- 3. Copia gli script Python e i file di configurazione ---
# Assumiamo che Terraform abbia copiato i file .py, .yaml e start_simulation.sh in /tmp/
# Questo è il comportamento comune quando si usa metadata_startup_script = file("path/to/script.sh")
# e gli altri file sono nella stessa directory locale dello script di startup.

echo "--- Copia script in ${SIM_DIR} ---"
# Sposta tutti i file necessari in /opt/simulation
sudo mv /tmp/*.py "${SIM_DIR}/"
sudo mv /tmp/*.yaml "${SIM_DIR}/" # Copierà config.yaml e malicious_config.yaml
sudo mv /tmp/start_simulation.sh "${SIM_DIR}/"

# Rendi lo script di avvio della simulazione eseguibile
sudo chmod +x "${SIM_DIR}/start_simulation.sh"

# --- 4. Imposta le variabili d'ambiente dagli metadati di Terraform ---
# Questi valori vengono passati da Terraform tramite la sezione `metadata` della risorsa `google_compute_instance`.
# DEVONO corrispondere esattamente ai nomi dei metadati in Terraform.

echo "--- Impostazione variabili d'ambiente da metadati Terraform ---"
WEB_SERVER_IP="${WEB_SERVER_IP_METADATA}" # Nome del metadata in Terraform
DNS_SERVER_IP="${DNS_SERVER_IP_METADATA}"   # Nome del metadata in Terraform
DB_SERVER_IP="${DB_SERVER_IP_METADATA}"     # Nome del metadata in Terraform

echo "WEB_SERVER_IP: ${WEB_SERVER_IP}"
echo "DNS_SERVER_IP: ${DNS_SERVER_IP}"
echo "DB_SERVER_IP: ${DB_SERVER_IP}"

# --- 5. Aggiorna i percorsi hardcoded in main.py (e malicious_main.py se simile) ---
# Il tuo main.py ha un percorso hardcoded per config.yaml che deve essere corretto.
# Fai la stessa cosa per malicious_main.py se legge malicious_config.yaml in modo simile.
echo "--- Correzione percorsi file di configurazione negli script Python ---"
sudo sed -i "s|r\"C:\\\\Users\\\\loren\\\\Desktop\\\\Uni\\\\Scalable test prova\\\\config.yaml\"|'${SIM_DIR}/config.yaml'|g" "${SIM_DIR}/main.py"
# Se malicious_main.py ha un percorso hardcoded simile per malicious_config.yaml:
# sudo sed -i "s|r\"C:\\\\Users\\\\loren\\\\Desktop\\\\Uni\\\\Scalable test prova\\\\malicious_config.yaml\"|'${SIM_DIR}/malicious_config.yaml'|g" "${SIM_DIR}/malicious_main.py"


# --- 6. Sostituisci gli IP placeholder nei file di configurazione YAML ---
# I tuoi file config.yaml e malicious_config.yaml hanno placeholder (es. 127.0.0.1).
# Sostituiamo questi placeholder con gli IP reali ottenuti dai metadati.
echo "--- Sostituzione IP placeholder nei file YAML ---"
sudo sed -i "s/web_server_ip: 127.0.0.1/web_server_ip: ${WEB_SERVER_IP}/g" "${SIM_DIR}/config.yaml"
sudo sed -i "s/dns_server_ip: 8.8.8.8/dns_server_ip: ${DNS_SERVER_IP}/g" "${SIM_DIR}/config.yaml"
sudo sed -i "s/db_server_ip: 127.0.0.1/db_server_ip: ${DB_SERVER_IP}/g" "${SIM_DIR}/config.yaml"

# Ripeti per malicious_config.yaml se contiene IP placeholder da aggiornare
# Esempio per malicious_config.yaml:
# sudo sed -i "s/target_web_ip: 127.0.0.1/target_web_ip: ${WEB_SERVER_IP}/g" "${SIM_DIR}/malicious_config.yaml"
# sudo sed -i "s/target_ssh_ip: 127.0.0.1/target_ssh_ip: ${ATTACKER_SSH_TARGET_IP}/g" "${SIM_DIR}/malicious_config.yaml"
# Assicurati di passare ATTACKER_SSH_TARGET_IP o altri IP come metadati da Terraform se necessario.


# --- 7. Avvia lo script di simulazione in background ---
echo "--- Avvio simulazione in background ---"
cd "${SIM_DIR}"
# nohup assicura che il processo continui anche dopo la disconnessione SSH
# &> reindirizza stdout e stderr a un file di log specifico
sudo nohup bash start_simulation.sh > "${LOG_DIR}/overall_simulation_startup.log" 2>&1 &

# Abilita SSH 
sudo sed -i 's/^#\?PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart ssh

echo "Client setup complete. Simulation started in background." | sudo tee -a "${LOG_DIR}/overall_simulation_startup.log"