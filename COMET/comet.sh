#!/bin/bash

# To start automatic background execution
#sudo nano /etc/systemd/system/comet.service
#sudo systemctl daemon-reload
#sudo systemctl start comet.service
#sudo systemctl status comet.service
# Variables
DEV_COMPUTER_IP=10.51.0.147
DEV_COMPUTER_USER=stepan-tyurin
SOURCE_DIR=/home/stepan-tyurin/Documents/terminal-test-terrain/COMET/
DEST_DIR=/home/rasp45g/python

if [ $# -eq 1 ]
  then
    case "$1" in
      "run") # Update python files and run interactable script
        scp -r ${DEV_COMPUTER_USER}@${DEV_COMPUTER_IP}:${SOURCE_DIR}src/*.py ${DEST_DIR}
        python manual.py
      ;;
      "simple") # Run interactable script without updating files
        python manual.py
      ;;
      "update") # Only update python and shell scripts
        scp -r ${DEV_COMPUTER_USER}@${DEV_COMPUTER_IP}:${SOURCE_DIR}src/*.py ${DEST_DIR}
        scp -r ${DEV_COMPUTER_USER}@${DEV_COMPUTER_IP}:${SOURCE_DIR}{*.sh,*.md,requirements.txt} ${DEST_DIR}
      ;;
      "update-full") # Update all including installing package requirements (requires internet connection)
        scp -r ${DEV_COMPUTER_USER}@${DEV_COMPUTER_IP}:${SOURCE_DIR}src/*.py ${DEST_DIR}
        scp -r ${DEV_COMPUTER_USER}@${DEV_COMPUTER_IP}:${SOURCE_DIR}{*.sh,*.md,requirements.txt} ${DEST_DIR}
        pip install -r ./requirements.txt
      ;;
      "clean") # Removes tmp files
        rm -rf ./measurements/*/tmp_*
      ;;
      "transfer") # Transfer all measurements file to the dev computer
        scp -r  ${DEST_DIR}/measurements/* ${DEV_COMPUTER_USER}@${DEV_COMPUTER_IP}:${SOURCE_DIR}/measurements
        scp -r  ${DEST_DIR}/logs/* ${DEV_COMPUTER_USER}@${DEV_COMPUTER_IP}:${SOURCE_DIR}/logs
      ;;
      *) echo "Accepted arguments:
          run (update python files and run main.py)
          update (update python and shell scripts without running)
          update-full (update all files including .venv)
          clean (removes all temporary files)
          transfer (transfer all measurements file to the dev computer)
          no arguments to only update python files
          "
    esac
  else # If no arguments given run automated measurements script
    python automatic.py
fi




