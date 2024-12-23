echo "==== Intalling venv ===="

python -m venv .venv
.venv/Scripts/python -m pip install --upgrade pip
.venv/Scripts/pip install -e .

echo "==== FINISHED ===="
