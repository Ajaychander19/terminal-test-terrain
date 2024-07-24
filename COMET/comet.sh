#!/bin/bash

USER_COMPUTER_IP=10.51.0.147 #192.168.1.1
USER_COMPUTER_USERNAME=stepan-tyurin
USER_DIR=/home/stepan-tyurin/Documents/terminal-test-terrain/COMET

if [ $# -eq 1 ]
  then
    case "$1" in
      "run")
        python automatic.py
      ;;
      "run-interactive")
        python interactive.py
      ;;
      "update") # Only update python and shell scripts
        scp -r ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/src/*.py .
        scp -r ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/requirements.txt .
        scp -r ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/comet.sh .
        scp -r ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/install.sh .
      ;;
      "update-full") # Update all including installing package requirements (requires internet connection)
        scp -r ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/src/*.py .
        scp -r ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/requirements.txt .
        scp -r ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/comet.sh .
        scp -r ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/install.sh .
        pip install -r ./requirements.txt
      ;;
      "clean") # Removes tmp files
        rm -rf ./measurements/*/tmp_*
      ;;
      "clean-full") # Removes all measurements and logs
        rm -rf ./measurements/*
        rm -rf ./cev/*
        sudo rm -rf ./logs/*
      ;;
      "transfer") # Transfer all measurements file to the dev computer
        scp -r ./measurements/* ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/measurements
        scp -r ./cev/* ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/cev
        scp -r ./logs/* ${USER_COMPUTER_USERNAME}@${USER_COMPUTER_IP}:${USER_DIR}/logs
      ;;
      *) echo "Accepted arguments:
          run (run the non-interactive version)
          run-interactive (run the interactive version)
          update (update python and shell scripts without running)
          update-full (update all files including .venv)
          clean (removes all temporary files)
          clean-full (removes all temporary files and logs)
          transfer (transfer logs and all measurements file to the dev computer)
          no arguments to run the non-interactive version
          "
    esac
  else # If no arguments given run automated measurements script.
    if ping -c 1 -W 1 google.com > /dev/null 2>&1; then # if connected to network, wait until clock is synchronized
      while ! timedatectl status | grep -q 'System clock synchronized: yes'; do
        sleep 1
      done
    fi
    python automatic.py
fi
