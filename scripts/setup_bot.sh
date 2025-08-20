#!/bin/bash

# Update and upgrade system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Check and install git
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    sudo apt install git -y
fi

# Check and install python
if ! command -v python3 &> /dev/null; then
    echo "Installing python3..."
    sudo apt install python3 -y
fi

# Check and install pip
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip3..."
    sudo apt install python3-pip -y
fi

# Install requirements
echo "Installing Python requirements..."
pip3 install -r requirements.txt

# Create .env file
echo "Creating .env file..."
read -p "Enter BOT_TOKEN: " BOT_TOKEN
read -p "Enter ADMIN_IDS (comma separated): " ADMIN_IDS
read -p "Enter PHONE_NUMBER: " PHONE_NUMBER
read -p "Enter WEBSITE_URL: " WEBSITE_URL
read -p "Enter TELEGRAM_CHANNEL: " TELEGRAM_CHANNEL
read -p "Enter MAP_COORDINATES (lat,lon): " MAP_COORDINATES

cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
PHONE_NUMBER=$PHONE_NUMBER
WEBSITE_URL=$WEBSITE_URL
TELEGRAM_CHANNEL=$TELEGRAM_CHANNEL
MAP_COORDINATES=$MAP_COORDINATES
EOF

echo ".env file created successfully!"

# Create systemd service
echo "Creating systemd service..."
sudo tee /lib/systemd/system/tg_bot.service > /dev/null << EOF
[Unit]
Description=Telegram bot for beauty studio
After=syslog.target
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
ExecStart=$PWD/venv/bin/python3 main.py
RestartSec=10
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable and start service
echo "Starting bot service..."
sudo systemctl start tg_bot.service
sudo systemctl enable tg_bot.service

# Check status
echo "Checking service status..."
sudo systemctl status tg_bot.service

echo "Setup completed successfully!"