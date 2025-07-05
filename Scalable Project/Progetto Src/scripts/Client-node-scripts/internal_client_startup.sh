#!/bin/bash
echo "Inizio setup Internal Client Node..."
export HOME="/home/cristian_ciocoiu" # Assicurati che HOME sia impostato correttamente
sudo apt-get update
sudo apt-get install -y python3 python3-pip curl

# Installa le dipendenze Python per il traffic generator
pip3 install --user requests dnspython pymysql

# Directory per gli script Python
SCRIPT_DIR="${HOME}/NetChaos"
sudo mkdir -p "${SCRIPT_DIR}"
sudo chown -R cristian_ciocoiu:cristian_ciocoiu "${SCRIPT_DIR}"

# Copia lo script del traffic generator qui (da fare manualmente o con Terraform)
# cp /path/locale/traffic_generator_agent.py "${SCRIPT_DIR}/traffic_generator_agent.py"

# Avvia il traffic generator (se vuoi che sia su un nodo separato)
# Se il traffic generator gira sull'attacker-node, questo blocco non è necessario qui
# screen -dmS traffic_generator bash -c "cd ${SCRIPT_DIR} && python3 traffic_generator_agent.py"
# echo "Traffic Generator Agent avviato su Internal Client."

echo "Internal Client Setup Complete."