#!/bin/bash
sudo apt-get update
sudo apt-get install -y nginx
echo '<h1>NetChaos Web Server</h1><p>This is a simulated web server.</p>' | sudo tee /var/www/html/index.html
sudo systemctl start nginx
sudo systemctl enable nginx
# Abilita SSH 
sudo sed -i 's/^#\?PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart ssh
echo "Web Server Setup Complete."