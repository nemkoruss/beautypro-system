#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Beauty Pro Bot setup...${NC}"

# Update and upgrade system
echo -e "${YELLOW}Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Check and install git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}Installing git...${NC}"
    sudo apt install git -y
else
    echo -e "${GREEN}Git is already installed${NC}"
fi

# Check and install python3
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Installing python3...${NC}"
    sudo apt install python3 -y
else
    echo -e "${GREEN}Python3 is already installed${NC}"
fi

# Check and install pip3
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}Installing python3-pip...${NC}"
    sudo apt install python3-pip -y
else
    echo -e "${GREEN}Pip3 is already installed${NC}"
fi

# Install requirements
echo -e "${YELLOW}Installing Python requirements...${NC}"
pip3 install -r requirements.txt

# Create .env file
echo -e "${YELLOW}Creating .env file...${NC}"
read -p "Enter BOT_TOKEN: " BOT_TOKEN
read -p "Enter ADMIN_IDS (comma separated): " ADMIN_IDS
read -p "Enter PHONE_NUMBER: " PHONE_NUMBER
read -p "Enter WEBSITE_URL: " WEBSITE_URL
read -p "Enter TELEGRAM_CHANNEL: " TELEGRAM_CHANNEL
read -p "Enter LOCATION_LAT: " LOCATION_LAT
read -p "Enter LOCATION_LON: " LOCATION_LON

cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
PHONE_NUMBER=$PHONE_NUMBER
WEBSITE_URL=$WEBSITE_URL
TELEGRAM_CHANNEL=$TELEGRAM_CHANNEL
LOCATION_LAT=$LOCATION_LAT
LOCATION_LON=$LOCATION_LON
DATABASE_URL=sqlite:///beauty_salon.db
EOF

echo -e "${GREEN}.env file created successfully${NC}"

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
python3 -c "
from database import db
db.init_db()
print('Database initialized successfully')
"

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${YELLOW}To start the bot, run: python3 main.py${NC}"