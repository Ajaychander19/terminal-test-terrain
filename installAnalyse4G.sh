#!/bin/bash
echo "Installation of 4GAnalyser"
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
mkdir OUT
cd src
python3 Interface.py
deactivate

