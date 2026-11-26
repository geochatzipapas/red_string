#!/bin/bash
# Χρήση:  chmod +x build_mac.sh   και μετά   ./build_mac.sh
set -e
cd "$(dirname "$0")"

echo "=== Εγκατάσταση απαραίτητων πακέτων ==="
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade pyinstaller PySide6

echo "=== Δημιουργία των 4 παιχνιδιών (θέλει λίγα λεπτά) ==="
python3 -m PyInstaller --noconfirm --clean --windowed --name Cyber_Fakelos game_cyber.py
python3 -m PyInstaller --noconfirm --windowed --name Astynomikos_Fakelos game_police.py
python3 -m PyInstaller --noconfirm --windowed --name Sherlock_Ntetektiv game_sherlock.py
python3 -m PyInstaller --noconfirm --windowed --name Blande_Kleptes game_caper.py

echo
echo "Τέλος! Οι εφαρμογές (.app) βρίσκονται στον φάκελο dist."
