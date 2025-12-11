#!/bin/bash
# Script de instalación para EC2 Worker

echo "Installing RDA Worker..."

# Update system
sudo yum update -y

# Install Python 3.11
sudo yum install python3.11 python3.11-pip -y

# Install dependencies
pip3.11 install -r requirements.txt

# Create systemd service
sudo cp rda-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rda-worker.service
sudo systemctl start rda-worker.service

echo "Worker installed and started!"