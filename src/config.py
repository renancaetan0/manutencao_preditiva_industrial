"""Configuração centralizada do projeto.

Lê variáveis do .env e expõe paths e parâmetros para os demais scripts.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Caminho da raiz do projeto (sobe um nível a partir de src/)
ROOT = Path(__file__).resolve().parent.parent

# Carrega .env da raiz
load_dotenv(ROOT / ".env")

# MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "smurfit_pdm_lab")

# Paths
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
POWERBI_EXPORTS = DATA_PROCESSED / "powerbi_exports"

# Modelagem
FAILURE_HORIZON_HOURS = int(os.getenv("FAILURE_HORIZON_HOURS", "24"))
CLASSIFICATION_THRESHOLD = float(os.getenv("CLASSIFICATION_THRESHOLD", "0.35"))

# Garante que pastas existem
for p in (DATA_PROCESSED, MODELS, POWERBI_EXPORTS):
    p.mkdir(parents=True, exist_ok=True)