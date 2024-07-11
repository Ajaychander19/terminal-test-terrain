#!/bin/bash
DEFAULT_RPI_USER="rasp45g"
DEFAULT_RPI_IP="10.51.0.185"

# If IP and username were given as arguments, use them, else use default
RPI_USER="${1:-$DEFAULT_RPI_USER}"
RPI_IP="${2:-$DEFAULT_RPI_IP}"

REMOTE_DIR="/home/$RPI_USER/"

# Files to transfer
FILES=("install.sh" "comet.sh" "requirements.txt" "src/ATCommandSender.py" "src/ATResponses.py" "src/automatic.py"
       "src/manual.py" "src/MeasurementsWriter.py" "src/SerialConnection.py")

# Transfer files to the Raspberry Pi
echo "Transferring files to Raspberry Pi..."
for FILE in "${FILES[@]}"; do
    scp "$FILE" "$RPI_USER@$RPI_IP:$REMOTE_DIR"
done

# Execute the installation script on the Raspberry Pi
echo "Executing installation script on Raspberry Pi..."
ssh "$RPI_USER@$RPI_IP" "cd && sudo chmod 744 install.sh && sudo bash install.sh"

echo "Deployment complete"