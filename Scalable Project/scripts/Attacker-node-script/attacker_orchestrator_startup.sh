#!/bin/bash

# Abilita i privilegi sudo per il servizio Nmap e Hydra
echo "gcp-user ALL=(ALL) NOPASSWD:/usr/bin/nmap" | sudo tee /etc/sudoers.d/nmap-allow
echo "gcp-user ALL=(ALL) NOPASSWD:/usr/bin/hydra" | sudo tee -a /etc/sudoers.d/hydra-allow

# Aggiorna i pacchetti e installa le dipendenze base
sudo apt-get update
sudo apt-get install -y nmap hydra python3 python3-pip git screen nginx

# Installa le librerie Python per l'agente attaccante e il backend orchestratore
pip3 install requests paramiko python-nmap flask google-cloud-storage google-cloud-sql cloud-sql-python-connector pymysql

# Variabili d'ambiente passate da Terraform
export WEB_SERVER_IP="${web_server_ip}"
export DB_SERVER_IP="${db_server_ip}"
export INTERNAL_CLIENT_IP="${internal_client_ip}"
export ATTACKER_NODE_IP="${attacker_node_ip}" # L'IP interno di questa stessa VM
export GCP_PROJECT_ID="${gcp_project_id}"
export GCS_BUCKET_NAME="${gcs_bucket_name}"
export CLOUDSQL_CONNECTION_NAME="${cloudsql_connection_name}"
export CLOUDSQL_DATABASE_NAME="${cloudsql_database_name}"
export CLOUDSQL_USER_NAME="${cloudsql_user_name}"
export CLOUDSQL_USER_PASSWORD="${cloudsql_user_password}"

# Scarica l'agente e l'orchestratore (se sono in repository separati o combinati)
# Per semplicità, ipotizziamo che i tuoi file Python siano stati caricati sul bucket GCS
# e scaricati qui, oppure che siano stati clonati da un singolo repo.
# Assicurati che /opt/netchaos esista
sudo mkdir -p /opt/netchaos
sudo chown gcp-user:gcp-user /opt/netchaos

# Metodo alternativo: copiare i file python da /tmp (se Terraform li ha messi lì)
# cp /tmp/attacker_agent.py /opt/netchaos/attacker_agent.py
# cp /tmp/orchestrator_backend.py /opt/netchaos/orchestrator_backend.py

# O, se hai un repository combinato:
# git clone https://github.com/tuo-utente/netchaos-combined.git /opt/netchaos
# cd /opt/netchaos


# Avvia l'agente attaccante in una sessione screen
# L'agente attaccante ora risponderà sulla porta 5001 (localhost)
screen -dmS attacker_agent bash -c "cd /opt/netchaos && python3 attacker_agent.py"

# Avvia il backend dell'orchestratore (GUI) in una sessione screen
# Il backend dell'orchestratore risponderà sulla porta 5000 (0.0.0.0)
screen -dmS orchestrator_backend bash -c "cd /opt/netchaos && python3 orchestrator_backend.py"

# Configura Nginx come reverse proxy per il backend Flask (opzionale, per produzione/HTTPS)
# Se vuoi esporre la GUI su porta 80/443 invece di 5000 direttamente
# sudo bash -c 'cat << EOF > /etc/nginx/sites-available/netchaos
# server {
#     listen 80;
#     server_name _;
#     location / {
#         proxy_pass http://127.0.0.1:5000; # Proxy al backend Flask
#         proxy_set_header Host \$host;
#         proxy_set_header X-Real-IP \$remote_addr;
#         proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
#     }
# }
# EOF'
# sudo rm /etc/nginx/sites-enabled/default
# sudo ln -s /etc/nginx/sites-available/netchaos /etc/nginx/sites-enabled/netchaos
# sudo systemctl restart nginx

echo "Attacker/Orchestrator Node Setup Complete."