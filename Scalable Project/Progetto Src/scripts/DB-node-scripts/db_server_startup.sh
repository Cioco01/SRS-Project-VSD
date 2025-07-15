#!/bin/bash
sudo apt-get update
sudo apt-get install -y mariadb-server
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Configurazione basilare di MariaDB per permettere accesso da IP interni
# In un ambiente reale, queste configurazioni sarebbero più stringenti
sudo bash -c "cat << EOF > /etc/mysql/mariadb.conf.d/50-remote.cnf
[mysqld]
bind-address = 0.0.0.0
EOF"
sudo systemctl restart mariadb

# Abilita SSH 
sudo sed -i 's/^#\?PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Creazione utente e database di esempio (se non gestito da Cloud SQL)
# Dato che Cloud SQL è il DB principale, questo è più per un DB secondario o per test interni
# Tuttavia, per completezza, mostro come si potrebbe fare
# sudo mysql -u root -e "CREATE DATABASE IF NOT EXISTS app_db;"
# sudo mysql -u root -e "CREATE USER 'app_user'@'%' IDENTIFIED BY 'app_password';"
# sudo mysql -u root -e "GRANT ALL PRIVILEGES ON app_db.* TO 'app_user'@'%';"
# sudo mysql -u root -e "FLUSH PRIVILEGES;"

echo "DB Server Setup Complete."