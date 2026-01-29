# Python GUI Environment

This folder contains the Python GUI environment (venv + dependencies).

## Setup

### Windows (PowerShell)
```powershell
cd gui_py
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python src/main.py

## MacOS
cd gui_py
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python src/main.py

