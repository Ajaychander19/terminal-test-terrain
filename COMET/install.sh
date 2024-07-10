#!/bin/bash


#### INSTALL PYTHON AND REQUIRED PACK
PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_VERSION" -lt 11 ]; then
  echo "Python 3.$PYTHON_VERSION detected which was not tested and might not be compatible";
  while true; do
    read -rp $'Install Python3.11 (y) or proceed with current version? (n)\n' yn
    case $yn in
        [Yy]* )
          echo "Installing Python3.11"
          echo "------------------------------"
          sudo add-apt-repository ppa:deadsnakes/ppa;
          sudo apt update;
          sudo apt install python3.11;
          PYTHON_VERSION=11
          break;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no";;
    esac
  done
elif [ "$PYTHON_VERSION" -lt 6 ]; then
  echo "Incompatible Python version detected (Python 3.$PYTHON_VERSION)";
  while true; do
    read -rp $'Install Python3.11 (y) or abort? (n)\n' yn
    case $yn in
        [Yy]* )
          echo "Installing Python3.11"
          echo "------------------------------"
          sudo add-apt-repository ppa:deadsnakes/ppa;
          sudo apt update;
          sudo apt install python3.11;
          PYTHON_VERSION=11
          break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no";;
    esac
  done
fi

# Instead of modifying the symlink which can break the system, set an alias to the necessary python version
alias python='/usr/bin/python3.$PYTHON_VERSION'

# Remove external package management
if test -f "/usr/lib/python3.$PYTHON_VERSION/EXTERNALLY-MANAGED"; then
    echo "Enable installing python packages with pip"
    sudo mv "/usr/lib/python3.$PYTHON_VERSION/EXTERNALLY-MANAGED" "/usr/lib/python3.$PYTHON_VERSION/EXTERNALLY-MANAGED.old"
fi

# Install packages
echo "Installing required python packages"
echo "------------------------------"
pip install -r ./requirements.txt



#### GIVE PERMISSIONS TO THE EXECUTABLES
# just in case
sudo chmod 744 ./comet.sh
sudo chmod 744 ./automatic.py
sudo chmod 744 ./main.sh



#### CREATE SYSTEMD SERVICE
WORKING_DIR=$(pwd)
USERNAME=$(whoami)
SERVICE_FILE_CONTENT="[Unit]
Description=COMET

[Service]
ExecStart=${WORKING_DIR}/comet.sh
WorkingDirectory=${WORKING_DIR}
StandardOutput=file:${WORKING_DIR}/logs/output.log
StandardError=file:${WORKING_DIR}/logs/error.log
User=${USERNAME}
Group=${USERNAME}
Restart=no

[Install]
WantedBy=multi-user.target"

# Write the service file
# Uses tee to have enough privileges to write so system file
echo "${SERVICE_FILE_CONTENT}" | sudo tee "/etc/systemd/system/comet.service" > /dev/null

# Set the correct permissions
chmod 755 "/etc/systemd/system/comet.service"

# Enable service at boot
sudo systemctl daemon-reload
sudo systemctl enable comet
echo "The program will now automatically start at boot"
echo "------------------------------"
echo


#### START COMET
while true; do
    read -rp $'Start the program now? (y/n)\n' yn
    case $yn in
        [Yy]* ) sudo systemctl start comet.service; break;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no";;
    esac
done

echo "------------------------------"
echo "Installation complete"