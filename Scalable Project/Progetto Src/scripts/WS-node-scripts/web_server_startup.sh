#!/bin/bash
sudo apt-get update
sudo apt-get install -y nginx
echo '<h1>NetChaos Web Server</h1><p>This is a simulated web server.</p>' | sudo tee /var/www/html/index.html
sudo systemctl start nginx
sudo systemctl enable nginx
echo "Web Server Setup Complete."