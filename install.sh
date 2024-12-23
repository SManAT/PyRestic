#!/bin/bash
sudo apt install pv cifs-utils python3.10-venv

echo "==== Intalling venv ===="

python3 -m venv .venv
.venv/bin/python3 -m pip install --upgrade pip
.venv/bin/pip install -e .

echo "==== FINISHED ===="

chmod 770 backup.sh
chmod 770 install.sh
