#!/bin/bash
echo "Installation of 4GAnalyser"
if [[ "$OSTYPE" == "linux-gnu" ]]; then
  echo "linux OS ($OSTYPE) detected."
  echo "1) Creation of python virtual environment"
  python3 -m venv .
  echo "2)Activate virtual environement"
  source bin/activate
  echo "3) Installation of required python library"
  pip install pandas shapely scipy
  deactivate
  echo "4) Copy of user-defined dissectors for wireshark"
  cp user_dlts ~/.config/wireshark/.
  echo "5) Installation terminated"
  source bin/activate
  echo "6) Launching the software"
  mkdir tmp
  cd src
  python3 Interface.py
  deactivate
elif [[ "$OSTYPE" == "msys" ]]; then
  echo "Windows OS ($OSTYPE) detected."
  echo "1) Creation of python virtual environment"
  python -m venv .

  echo "2) Activate virtual environment"
  source Scripts/activate  # Windows: 'Scripts', Linux: 'bin'

  echo "3) Installation of required python libraries"
  pip install pandas shapely scipy numpy

  echo "4) Copy of user-defined dissectors for Wireshark"
  mkdir -p "$APPDATA/Wireshark"
  cp user_dlts "$APPDATA/Wireshark/"

  echo "5) Installation terminated"

  echo "6) Launching the software"
  mkdir -p tmp
  cd src
  python Interface.py
  deactivate
else
  echo "ERROR: OS not managed."
  echo "OS detected: $OSTYPE"
fi
