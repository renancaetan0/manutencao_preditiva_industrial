"""Carrega CSVs do Kaggle no MySQL."""
import pandas as pd
from sqlalchemy import text

from src.config import DATA_RAW
from src.db import get_engine

# (arquivo CSV, nome da tabela MySQL)
INGEST_PLAN = [
    ("PdM_machines.csv",  "raw_machines"),
    ("PdM_telemetry.csv", "raw_telemetry"),
    ("PdM_errors.csv",    "raw_errors"),
    ("PdM_maint.csv",     "raw_maint"),
    ("PdM_failures.csv",  "raw_failures"),
]

def truncate_table(engine, table: str):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table}"))

def load_csv(file_name: str) -> pd.DataFrame:
    path = DATA_RAW / file_name
    df = pd.read_csv(path)
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
    return df

def ingest(engine, df: pd.DataFrame, table: str):
    df.to_sql(
        table, engine,
        if_exists="append",
        index=False,
        chunksize=10_000,  # insere em lotes
        method="multi",
    )

def main():
    engine = get_engine()
    for file_name, table in INGEST_PLAN:
        print(f"[ingest] {file_name} -> {table}")
        truncate_table(engine, table)
        df = load_csv(file_name)
        ingest(engine, df, table)
        print(f"[ingest] {len(df):,} linhas inseridas em {table}")

if __name__ == "__main__":
    main()