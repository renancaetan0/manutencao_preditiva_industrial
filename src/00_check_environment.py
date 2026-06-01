"""Checa se o ambiente está pronto para rodar o pipeline."""
import sys
from pathlib import Path

from src.config import (
    DATA_RAW, MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
    MYSQL_DATABASE,
)

EXPECTED_CSVS = [
    "PdM_telemetry.csv",
    "PdM_errors.csv",
    "PdM_maint.csv",
    "PdM_failures.csv",
    "PdM_machines.csv",
]

def check_python():
    print(f"[python] {sys.version.split()[0]} em {sys.executable}")

def check_packages():
    required = ["pandas", "numpy", "sqlalchemy", "pymysql",
                "sklearn", "joblib", "matplotlib"]
    for pkg in required:
        try:
            __import__(pkg)
            print(f"[pkg]    {pkg} OK")
        except ImportError:
            print(f"[pkg]    {pkg} FALTA")

def check_csvs():
    if not DATA_RAW.exists():
        print(f"[data]   pasta {DATA_RAW} não existe")
        return
    for csv in EXPECTED_CSVS:
        p = DATA_RAW / csv
        status = "OK" if p.exists() else "FALTA"
        print(f"[data]   {csv}: {status}")

def check_mysql():
    try:
        from sqlalchemy import create_engine, text
        # Conecta no servidor SEM database (pode não existir ainda)
        url = f"mysql+pymysql://{MYSQL_USER}:***@{MYSQL_HOST}:{MYSQL_PORT}"
        engine = create_engine(url.replace("***", _get_pwd()))
        with engine.connect() as conn:
            r = conn.execute(text("SELECT VERSION()")).scalar()
            print(f"[mysql]  conectado, versão {r}")
    except Exception as e:
        print(f"[mysql]  FALHOU: {e}")

def _get_pwd():
    from src.config import MYSQL_PASSWORD
    return MYSQL_PASSWORD

if __name__ == "__main__":
    print("=== check environment ===")
    check_python()
    check_packages()
    check_csvs()
    check_mysql()
    print("=== fim ===")