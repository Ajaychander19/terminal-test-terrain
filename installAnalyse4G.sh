#!/bin/bash
echo "Installation of 4GAnalyser"

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

