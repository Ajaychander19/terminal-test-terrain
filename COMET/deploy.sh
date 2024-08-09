#!/bin/bash
DEFAULT_RPI_USER="pi"
# raspberrypi.local is the default name that can be resolved to RPI's IP address. Use a proper IP address like
# 192.168.1.2. if your computer doesn't supports multicast DNS or if network settings or hostname were changed
DEFAULT_RPI_IP="raspberrypi.local"

# If IP and username were given as arguments, use them, else use default
RPI_USER="${1:-$DEFAULT_RPI_USER}"
RPI_IP="${2:-$DEFAULT_RPI_IP}"

REMOTE_DIR="/home/$RPI_USER/"

# Function to check if the Raspberry Pi is reachable via SSH
wait_for_ssh() {
    echo "Trying to connect to the Raspberry Pi at $RPI_USER@$RPI_IP..."
    while ! ssh -o ConnectTimeout=3 "$RPI_USER@$RPI_IP" exit 2>/dev/null; do
        echo "Raspberry Pi is not reachable. Retrying in 3 seconds..."
        sleep 3
    done
    echo "Raspberry Pi found"
}

# Replace the user name and directory in comet.sh script with the current user
sed -i "s|USER_COMPUTER_USERNAME=.*|USER_COMPUTER_USERNAME=$(whoami)|" comet.sh
sed -i "s|USER_DIR=.*|USER_DIR=$(pwd)|" comet.sh

# Wait for the Raspberry Pi to be reachable
wait_for_ssh

# Transfer files to the Raspberry Pi
FILES=("install.sh" "comet.sh" "requirements.txt")
echo "Transferring files to Raspberry Pi..."
for FILE in "${FILES[@]}"; do
    scp "$FILE" "$RPI_USER@$RPI_IP:$REMOTE_DIR"
done
scp -r ./src/*.py "$RPI_USER@$RPI_IP:$REMOTE_DIR/src"
scp -r ./src/shared/*.py "$RPI_USER@$RPI_IP:$REMOTE_DIR/src/shared"

# Execute the installation script on the Raspberry Pi
echo "Executing installation script on Raspberry Pi..."
ssh "$RPI_USER@$RPI_IP" "cd && sudo chmod 744 install.sh && bash install.sh --non-interactive"

echo "Deployment complete"