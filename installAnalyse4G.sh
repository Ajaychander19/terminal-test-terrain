#!/bin/bash
echo "===== Installation of 4GAnalyser ====="

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  echo "Linux OS ($OSTYPE) detected."

  # Detect Python 3 version
  PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")

  if [[ "$PY_VER" != "unknown" ]]; then
    echo "Detected Python version: $PY_VER"
    echo "1) Checking if venv module is available..."
    # Try to install the matching venv package
    if ! python3 -m venv --help >/dev/null 2>&1; then
      echo "   'venv' module missing — installing python${PY_VER}-venv..."
      sudo apt-get update -y
      sudo apt-get install -y "python${PY_VER}-venv"
    else
      echo "   'venv' module already available."
    fi
  else
    echo "Warning: Unable to detect Python version automatically."
  fi

  echo "2) Creating Python virtual environment..."
  python3 -m venv venv

  echo "3) Activating virtual environment..."
  source venv/bin/activate

  echo "4) Installing required Python libraries..."
  pip install --upgrade pip
  pip install pandas shapely scipy

  deactivate

  echo "5) Copying user-defined dissectors for Wireshark..."
  mkdir -p ~/.config/wireshark
  cp user_dlts ~/.config/wireshark/.

  echo "6) Installation terminated."
  echo "7) Launching the software..."
  source venv/bin/activate
  mkdir -p tmp
  cd src
  python3 Interface.py
  deactivate

elif [[ "$OSTYPE" == "msys" ]]; then
  echo "Windows OS ($OSTYPE) detected."

  echo "1) Creating Python virtual environment..."
  python -m venv venv

  echo "2) Activating virtual environment..."
  source venv/Scripts/activate

  echo "3) Installing required Python libraries..."
  pip install pandas shapely scipy numpy

  echo "4) Copying user-defined dissectors for Wireshark..."
  mkdir -p "$APPDATA/Wireshark"
  cp user_dlts "$APPDATA/Wireshark/"

  echo "5) Installation terminated."
  echo "6) Launching the software..."
  mkdir -p tmp
  cd src
  python Interface.py
  deactivate
else
  echo "ERROR: OS not managed."
  echo "OS detected: $OSTYPE"
fi