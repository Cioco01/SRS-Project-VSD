#!/bin/bash

# Abilita SSH 
sudo sed -i 's/^#\?PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart ssh


echo "DNS Server Setup Complete."