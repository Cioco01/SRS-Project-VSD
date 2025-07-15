#!/bin/bash

# --- Configurazione Iniziale ---
echo "Inizio setup Attacker/Orchestrator Node..."
export HOME="/home/cristian_ciocoiu/" # Assicurati che HOME sia impostato correttamente per l'utente gcp-user

# Abilita i privilegi sudo per il servizio Nmap e Hydra e altri potenziali strumenti
echo "cristian_ciocoiu ALL=(ALL) NOPASSWD:/usr/bin/nmap" | sudo tee -a /etc/sudoers.d/nmap-allow
echo "cristian_ciocoiu ALL=(ALL) NOPASSWD:/usr/bin/hydra" | sudo tee -a /etc/sudoers.d/hydra-allow
echo "cristian_ciocoiu ALL=(ALL) NOPASSWD:/usr/bin/tcpdump" | sudo tee -a /etc/sudoers.d/tcpdump-allow # Per potenziale cattura traffico
echo "cristian_ciocoiu ALL=(ALL) NOPASSWD:/usr/sbin/tcpdump" | sudo tee -a /etc/sudoers.d/tcpdump-allow
echo "cristian_ciocoiu ALL=(ALL) NOPASSWD:/usr/bin/screen" | sudo tee -a /etc/sudoers.d/screen-allow
echo "cristian_ciocoiu ALL=(ALL) NOPASSWD:/usr/bin/dsniff" | sudo tee -a /etc/sudoers.d/dsniff-allow
echo "cristian_ciocoiu ALL=(ALL) NOPASSWD:/usr/bin/hping3" | sudo tee -a /etc/sudoers.d/hping3-allow

# Aggiorna i pacchetti e installa le dipendenze base
sudo apt-get update
sudo apt-get install -y nmap hydra python3 python3-pip git screen nginx tcpdump dsniff hping3

# Installa le librerie Python necessarie
# Ho rimosso 'google-cloud-sql' che non esiste e aggiunto 'google-api-python-client' se dovesse servire per altre API
# Ho aggiunto 'pandas' e 'numpy' per potenziale elaborazione dati
pip3 install --user requests paramiko python-nmap flask google-cloud-storage cloud-sql-python-connector pymysql pandas numpy google-api-python-client

# Variabili d'ambiente (popolate da Terraform)
# Queste saranno usate dagli script Python.
export GCP_PROJECT_ID="gruppo-9-456912" #"${gcp_project_id}"
export CLOUDSQL_CONNECTION_NAME="gruppo-9-456912:europe-west1:simulation-db-instance" # Il tuo Cloud SQL connection name
export CLOUDSQL_DATABASE_NAME="simulation_data" # ASSICURATI CHE SIA simulation_data e non data-viewer-db
export CLOUDSQL_USER_NAME="simuser" # Il tuo utente Cloud SQL
export CLOUDSQL_USER_PASSWORD="password" # La tua password Cloud SQL

# Variabili d'ambiente per la configurazione della rete
# Questi IP sono impostati da Terraform e passati come variabili d'ambiente
# In terrraform, puoi usare `output` per esportarli, QUINDI CAMBIARE OUTPUT

export WEB_SERVER_IP="10.0.1.4"  #"${web_server_ip}"
export DB_SERVER_IP="10.0.3.2"  #"${db_server_ip}"
export INTERNAL_CLIENT_IP="10.0.2.2"  #"${internal_client_ip}"
export ATTACKER_NODE_IP="10.0.1.3" #"${attacker_node_ip}" # L'IP interno di questa stessa VM
export DNS_SERVER_IP="10.0.1.2" #"${dns_server_ip}"
export GCS_BUCKET_NAME="gruppo-9-456912-traffic-data"   #"${gcs_bucket_name}"
#export CLOUDSQL_CONNECTION_NAME="${cloudsql_connection_name}"
#export CLOUDSQL_DATABASE_NAME="${cloudsql_database_name}"
#export CLOUDSQL_USER_NAME="${cloudsql_user_name}"
#export CLOUDSQL_USER_PASSWORD="${cloudsql_user_password}"

# Directory per gli script Python e i file statici della GUI
SCRIPT_DIR="${HOME}/NetChaos"
STATIC_DIR="${SCRIPT_DIR}/static"
sudo mkdir -p "${SCRIPT_DIR}"
sudo chown -R cristian_ciocoiu:cristian_ciocoiu "${SCRIPT_DIR}"

# Abilita SSH 
sudo sed -i 's/^#\?PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Assicurati che la directory static esista e abbia i permessi
mkdir -p "${STATIC_DIR}"
# E che il tuo index.html sia copiato in ${STATIC_DIR}/index.html

echo "Verifica e creazione delle tabelle del database Cloud SQL..."
DB_INIT_SCRIPT="${SCRIPT_DIR}/DB_setup/db_init.py"

# Esegui lo script SQL per creare le tabelle
python3 "${DB_INIT_SCRIPT}" || {
    echo "Errore durante l'esecuzione dello script di inizializzazione del database."
    exit 1
}

CAPTURE_DIR="${SCRIPT_DIR}/Traffic_capture"

echo "Inizializzazione del database completata."

# --- Avvio Servizi ---

echo "Avvio servizi Flask con screen..."

# Avvia l'agente attaccante (porta 5001, localhost)
screen -dmS attacker_agent bash -c "cd ${SCRIPT_DIR} && python3 attacker_agent.py"
echo "Attacker Agent avviato."

# Avvia il generatore di traffico (porta 5002, localhost)
screen -dmS traffic_generator_agent bash -c "cd ${SCRIPT_DIR} && python3 traffic_generator_agent.py"
echo "Traffic Generator Agent avviato."

# Avvia il traffic capture agent (porta 5003, localhost)
screen -dmS traffic_capture_agent bash -c "cd ${CAPTURE_DIR} && python3 traffic_capture_agent.py"
echo "Traffic Capture Agent avviato."

# Avvia il backend dell'orchestratore (GUI) (porta 5000, 0.0.0.0)
screen -dmS orchestrator_backend bash -c "cd ${SCRIPT_DIR} && python3 orchestrator_backend.py"
echo "Orchestrator Backend avviato."

screen -dmS data_viewer_backend bash -c "cd ${SCRIPT_DIR} && python3 data_viewer_backend.py"
echo "Data Viewer Backend avviato."

echo "Attacker/Orchestrator Node Setup Complete."


## DA FARE COME CODICE PER OGNI VM PER SSH:
# Abilita SSH 
# sudo sed -i 's/^#\?PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
# sudo systemctl restart ssh