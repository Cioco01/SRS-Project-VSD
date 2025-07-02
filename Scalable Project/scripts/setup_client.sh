#!/bin/bash
# scripts/setup_client.sh
# Script di startup per l'istanza client GCE

# Aggiorna il sistema
sudo apt-get update -y

# Installa Python 3 e pip
sudo apt-get install -y python3 python3-pip

# Installa le dipendenze Python
pip3 install requests dnspython PyYAML mysql-connector-python paramiko

# Installa Nmap (per il port scanning)
sudo apt-get install -y nmap

# Crea la directory per i log
sudo mkdir -p /var/log/simulation
sudo chmod 777 /var/log/simulation # Permessi ampi per il testing

# Crea la directory per gli script
sudo mkdir -p /opt/simulation

# Copia gli script Python e i file di configurazione
# Assicurati che i file .py e .yaml siano nella stessa directory dello script di startup sul tuo host locale
# Quando li passi a Terraform, di solito vengono messi in /tmp o /home/user.
# Modifica questi percorsi se i tuoi file verranno copiati in un'altra posizione da Terraform.
# Assumiamo che Terraform li copi in /tmp/
sudo mv /tmp/*.py /opt/simulation/
sudo mv /tmp/*.yaml /opt/simulation/ # Questo copierà sia config.yaml che malicious_config.yaml
sudo mv /tmp/start_simulation.sh /opt/simulation/

# Rendi lo script di avvio della simulazione eseguibile
sudo chmod +x /opt/simulation/start_simulation.sh

# Avvia lo script di simulazione in background
# nohup assicura che il processo continui anche dopo la disconnessione SSH
# &> reindirizza stdout e stderr a un file di log
sudo nohup /opt/simulation/start_simulation.sh &> /var/log/overall_simulation_startup.log &

echo "Client setup complete. Simulation started in background." | sudo tee -a /var/log/overall_simulation_startup.log