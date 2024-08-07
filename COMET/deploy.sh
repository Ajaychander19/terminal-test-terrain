#!/bin/bash
DEFAULT_RPI_USER="pi"
# pi.local is the default name that can be resolved to RPI's IP address. Use a proper IP address like 192.168.1.2. if
# anything was changed from default on the RPI.
DEFAULT_RPI_IP="pi.local"

# If IP and username were given as arguments, use them, else use default
RPI_USER="${1:-$DEFAULT_RPI_USER}"
RPI_IP="${2:-$DEFAULT_RPI_IP}"

REMOTE_DIR="/home/$RPI_USER/"


# Replace the user name and directory in comet.sh script with the current user
sed -i "s|USER_COMPUTER_USERNAME=.*|USER_COMPUTER_USERNAME=$(whoami)|" comet.sh
sed -i "s|USER_DIR=.*|USER_DIR=$(pwd)|" comet.sh

# Transfer files to the Raspberry Pi
FILES=("install.sh" "comet.sh" "requirements.txt")
echo "Transferring files to Raspberry Pi..."
for FILE in "${FILES[@]}"; do
    scp "$FILE" "$RPI_USER@$RPI_IP:$REMOTE_DIR"
done

scp -r "./src/" "$RPI_USER@$RPI_IP:$REMOTE_DIR"

# Execute the installation script on the Raspberry Pi
echo "Executing installation script on Raspberry Pi..."
ssh "$RPI_USER@$RPI_IP" "cd && sudo chmod 744 install.sh && sudo bash install.sh --non-interactive"

echo "Deployment complete"