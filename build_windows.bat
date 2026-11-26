@echo off
chcp 65001 >nul
echo === Εγκατάσταση απαραίτητων πακέτων ===
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller PySide6
if errorlevel 1 goto fail

echo === Δημιουργία των 4 παιχνιδιών (θέλει λίγα λεπτά) ===
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Cyber_Fakelos game_cyber.py
if errorlevel 1 goto fail
python -m PyInstaller --noconfirm --onefile --windowed --name Astynomikos_Fakelos game_police.py
if errorlevel 1 goto fail
python -m PyInstaller --noconfirm --onefile --windowed --name Sherlock_Ntetektiv game_sherlock.py
if errorlevel 1 goto fail
python -m PyInstaller --noconfirm --onefile --windowed --name Blande_Kleptes game_caper.py
if errorlevel 1 goto fail

echo.
echo Τέλος! Τα .exe βρίσκονται στον φάκελο "dist".
pause
exit /b 0

:fail
echo.
echo Κάτι πήγε στραβά. Διάβασε το μήνυμα λάθους παραπάνω.
pause
exit /b 1
