#!/bin/bash

WORKING_DIR=$(pwd)
USERNAME=$(whoami)

# Check for non-interactive mode
INTERACTIVE=true
if [[ "$1" == "--non-interactive" ]]; then
  INTERACTIVE=false
fi

install_python () {
  echo "Installing Python3.11"
  echo "------------------------------"
  sudo add-apt-repository ppa:deadsnakes/ppa;
  sudo apt update;
  sudo apt install python3.11;
}


#### INSTALL PYTHON AND REQUIRED PACKAGES
PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_VERSION" -lt 11 ]; then
  echo "Python 3.$PYTHON_VERSION detected which was not tested and might not be compatible";
  if [ "$INTERACTIVE" = true ]; then
    while true; do
      read -rp $'Install Python3.11 (y) or proceed with current version? (n)\n' yn
      case $yn in
          [Yy]* )
            install_python
            PYTHON_VERSION=11
            break;;
          [Nn]* ) break;;
          * ) echo "Please answer yes or no";;
      esac
    done
  else
    echo "Non-interactive mode: Proceeding with current Python version"
  fi
elif [ "$PYTHON_VERSION" -lt 9 ]; then
  echo "Incompatible Python version detected (Python 3.$PYTHON_VERSION)";
  if [ "$INTERACTIVE" = true ]; then
    while true; do
      read -rp $'Install Python3.11 (y) or abort? (n)\n' yn
      case $yn in
          [Yy]* )
            install_python
            PYTHON_VERSION=11
            break;;
          [Nn]* ) exit;;
          * ) echo "Please answer yes or no";;
      esac
    done
  else
    echo "Non-interactive mode: Installing Python3.11"
    install_python
  fi
fi

# Instead of modifying the symlink which can break the system, set an alias to the necessary python version
alias python='/usr/bin/python3.$PYTHON_VERSION'

# Remove external package management
if test -f "/usr/lib/python3.$PYTHON_VERSION/EXTERNALLY-MANAGED"; then
    echo "Enable installing python packages with pip"
    sudo mv "/usr/lib/python3.$PYTHON_VERSION/EXTERNALLY-MANAGED" "/usr/lib/python3.$PYTHON_VERSION/EXTERNALLY-MANAGED.old"
fi

# Check if pip is installed, install it if not
if ! command -v pip &> /dev/null
then
    echo "pip is not installed. Installing now..."
    sudo apt update
    sudo apt install -y python3-pip
    echo "pip has been installed."
fi

# Install packages
echo "Installing required python packages"
echo "------------------------------"
pip install -r ./requirements.txt



#### GIVE PERMISSIONS TO THE EXECUTABLES
# just in case
sudo chmod 744 ./comet.sh
sudo chmod 744 ./automatic.py
sudo chmod 744 ./manual.sh


#### CREATE SUBDIRECTORIES
# They are normally created in Python but just in case
mkdir -p ./logs
mkdir -p ./measurements
mkdir -p ./cev


#### CREATE SYSTEMD SERVICES
# SETUP MAIN MEASUREMENTS SERVICE
SERVICE_FILE_CONTENT="[Unit]
Description=COMET

[Service]
ExecStart=${WORKING_DIR}/comet.sh
WorkingDirectory=${WORKING_DIR}
StandardOutput=file:${WORKING_DIR}/logs/measurements_output.log
StandardError=file:${WORKING_DIR}/logs/measurements_error.log
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

# SETUP NMEA LOGGER SERVICE
NMEA_LOGGER_CONTENT="[Unit]
Description=NMEA Output Logger

[Service]
ExecStart=/usr/bin/python3 ${WORKING_DIR}/NMEALogger.py
WorkingDirectory=${WORKING_DIR}
StandardError=file:${WORKING_DIR}/logs/nmea_logger.err
User=${USERNAME}
Group=${USERNAME}
Restart=always

[Install]
WantedBy=multi-user.target"

# Write the service file
# Uses tee to have enough privileges to write so system file
echo "${NMEA_LOGGER_CONTENT}" | sudo tee "/etc/systemd/system/nmea_logger.service" > /dev/null

# Set the correct permissions
chmod 755 "/etc/systemd/system/nmea_logger.service"



# Enable service at boot
sudo systemctl daemon-reload
sudo systemctl enable comet
sudo systemctl enable nmea_logger
echo "The program will now automatically start at boot"
echo "------------------------------"
echo


#### START COMET
if [ "$INTERACTIVE" = true ]; then
  while true; do
      read -rp $'Start the program now? (y/n)\n' yn
      case $yn in
          [Yy]* ) sudo systemctl start comet.service; break;;
          [Nn]* ) break;;
          * ) echo "Please answer yes or no";;
      esac
  done
else
  echo "Starting COMET"
  sudo systemctl start comet.service;
fi

echo "------------------------------"
echo "Installation complete"