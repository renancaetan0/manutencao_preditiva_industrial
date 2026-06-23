"""Roda validações de qualidade e grava em dq_results."""
from datetime import datetime

import pandas as pd
from sqlalchemy import text

from src.config import DATA_PROCESSED
from src.db import get_engine

CREATE_DQ = """
CREATE TABLE IF NOT EXISTS dq_results (
  id           BIGINT AUTO_INCREMENT PRIMARY KEY,
  run_ts       DATETIME    NOT NULL,
  table_name   VARCHAR(50) NOT NULL,
  check_name   VARCHAR(100) NOT NULL,
  status       VARCHAR(10) NOT NULL,
  observed     TEXT,
  expected     TEXT,
  details      TEXT
);
"""

ALTER_DQ = """
ALTER TABLE dq_results
  MODIFY observed TEXT,
  MODIFY expected TEXT,
  MODIFY details TEXT;
"""

def run_check(name, table, observed, expected, status, details=""):
    return {
        "run_ts": datetime.now(),
        "table_name": table,
        "check_name": name,
        "status": status,
        "observed": str(observed),
        "expected": str(expected),
        "details": details,
    }

def check_machines(engine, results):
    df = pd.read_sql("SELECT COUNT(*) AS n FROM raw_machines", engine)
    n = int(df.loc[0, "n"])
    results.append(run_check("row_count", "raw_machines", n, 100,
                             "PASS" if n == 100 else "FAIL"))

    df = pd.read_sql("SELECT model, COUNT(*) c FROM raw_machines GROUP BY model", engine)
    expected_models = {"model1", "model2", "model3", "model4"}
    observed = set(df["model"])
    results.append(run_check("model_domain", "raw_machines", observed, expected_models,
                             "PASS" if observed == expected_models else "WARN"))

# ... implemente check_telemetry, FEITO:
def check_telemetry(engine, results):
    """Valida volume, período, máquinas distintas, nulos e duplicatas da raw_telemetry."""

    # 1. Volume total da tabela.
    # O dataset tem 100 máquinas, cada uma com 8.761 leituras horárias.
    # Portanto, o total esperado é 100 * 8.761 = 876.100 linhas.
    df = pd.read_sql("SELECT COUNT(*) AS n FROM raw_telemetry", engine)
    n = int(df.loc[0, "n"])

    results.append(run_check(
        name="row_count",
        table="raw_telemetry",
        observed=n,
        expected=876100,
        status="PASS" if n == 876100 else "WARN",
        details="Total esperado: 100 máquinas x 8.761 leituras por máquina."
    ))

    # 2. Quantidade de máquinas distintas.
    # Esperamos encontrar leituras das 100 máquinas cadastradas.
    df = pd.read_sql("""
        SELECT COUNT(DISTINCT machineID) AS n_machines
        FROM raw_telemetry
    """, engine)

    n_machines = int(df.loc[0, "n_machines"])

    results.append(run_check(
        name="distinct_machines",
        table="raw_telemetry",
        observed=n_machines,
        expected=100,
        status="PASS" if n_machines == 100 else "FAIL",
        details="A telemetria deve conter leituras para as 100 máquinas."
    ))

    # 3. Período coberto pela telemetria.
    # Aqui não estamos dizendo se está certo ou errado; estamos documentando
    # o intervalo real encontrado para consulta posterior.
    df = pd.read_sql("""
        SELECT
            MIN(datetime) AS min_datetime,
            MAX(datetime) AS max_datetime
        FROM raw_telemetry
    """, engine)

    min_dt = df.loc[0, "min_datetime"]
    max_dt = df.loc[0, "max_datetime"]

    results.append(run_check(
        name="datetime_range",
        table="raw_telemetry",
        observed=f"{min_dt} até {max_dt}",
        expected="aprox. 1 ano de leituras horárias",
        status="PASS",
        details="Registra o menor e o maior timestamp encontrados na telemetria."
    ))

    # 4. Valores nulos nos sensores.
    # Como os sensores são a base da modelagem, nulos aqui merecem atenção.
    df = pd.read_sql("""
        SELECT
            SUM(CASE WHEN volt IS NULL THEN 1 ELSE 0 END) AS null_volt,
            SUM(CASE WHEN rotate IS NULL THEN 1 ELSE 0 END) AS null_rotate,
            SUM(CASE WHEN pressure IS NULL THEN 1 ELSE 0 END) AS null_pressure,
            SUM(CASE WHEN vibration IS NULL THEN 1 ELSE 0 END) AS null_vibration
        FROM raw_telemetry
    """, engine)

    nulls = {
        "volt": int(df.loc[0, "null_volt"]),
        "rotate": int(df.loc[0, "null_rotate"]),
        "pressure": int(df.loc[0, "null_pressure"]),
        "vibration": int(df.loc[0, "null_vibration"]),
    }

    total_nulls = sum(nulls.values())

    results.append(run_check(
        name="sensor_nulls",
        table="raw_telemetry",
        observed=nulls,
        expected="0 nulos nos sensores",
        status="PASS" if total_nulls == 0 else "WARN",
        details="Verifica se existem leituras ausentes em volt, rotate, pressure ou vibration."
    ))

    # 5. Duplicatas por máquina e horário.
    # A regra de negócio é: uma máquina deve ter no máximo uma leitura
    # para cada timestamp. Se aparecer mais de uma, há duplicidade.
    df = pd.read_sql("""
        SELECT COUNT(*) AS duplicated_keys
        FROM (
            SELECT machineID, datetime, COUNT(*) AS c
            FROM raw_telemetry
            GROUP BY machineID, datetime
            HAVING c > 1
        ) duplicated
    """, engine)

    duplicated_keys = int(df.loc[0, "duplicated_keys"])

    results.append(run_check(
        name="duplicate_machine_datetime",
        table="raw_telemetry",
        observed=duplicated_keys,
        expected=0,
        status="PASS" if duplicated_keys == 0 else "FAIL",
        details="Cada par (machineID, datetime) deve aparecer uma única vez."
    ))
# ... implemente check_errors, check_maint, check_failures,
#     check_referential_integrity, check_telemetry_gaps
# SEGUE:
def check_errors(engine, results):
    """Valida volume, domínio e nulos da tabela raw_errors."""

    # 1. Volume esperado da tabela.
    # O dataset PdM_errors.csv costuma ter 3.919 eventos de erro.
    df = pd.read_sql("SELECT COUNT(*) AS n FROM raw_errors", engine)
    n = int(df.loc[0, "n"])

    results.append(run_check(
        name="row_count",
        table="raw_errors",
        observed=n,
        expected=3919,
        status="PASS" if n == 3919 else "WARN",
        details="Total esperado de eventos em PdM_errors.csv."
    ))

    # 2. Domínio de errorID.
    # errorID deve conter apenas error1, error2, error3, error4 e error5.
    df = pd.read_sql("""
        SELECT errorID, COUNT(*) AS c
        FROM raw_errors
        GROUP BY errorID
    """, engine)

    expected_errors = {"error1", "error2", "error3", "error4", "error5"}
    observed_errors = set(df["errorID"])

    results.append(run_check(
        name="error_domain",
        table="raw_errors",
        observed=observed_errors,
        expected=expected_errors,
        status="PASS" if observed_errors == expected_errors else "WARN",
        details="Verifica se errorID contém apenas os códigos esperados."
    ))

    # 3. Nulos em colunas obrigatórias.
    df = pd.read_sql("""
        SELECT
            SUM(CASE WHEN datetime IS NULL THEN 1 ELSE 0 END) AS null_datetime,
            SUM(CASE WHEN machineID IS NULL THEN 1 ELSE 0 END) AS null_machineID,
            SUM(CASE WHEN errorID IS NULL THEN 1 ELSE 0 END) AS null_errorID
        FROM raw_errors
    """, engine)

    nulls = {
        "datetime": int(df.loc[0, "null_datetime"]),
        "machineID": int(df.loc[0, "null_machineID"]),
        "errorID": int(df.loc[0, "null_errorID"]),
    }

    results.append(run_check(
        name="required_nulls",
        table="raw_errors",
        observed=nulls,
        expected="0 nulos em datetime, machineID e errorID",
        status="PASS" if sum(nulls.values()) == 0 else "FAIL",
        details="Campos obrigatórios não devem ter valores ausentes."
    ))


def check_maint(engine, results):
    """Valida volume, domínio e nulos da tabela raw_maint."""

    # 1. Volume esperado da tabela.
    # O dataset PdM_maint.csv costuma ter 3.286 eventos de manutenção.
    df = pd.read_sql("SELECT COUNT(*) AS n FROM raw_maint", engine)
    n = int(df.loc[0, "n"])

    results.append(run_check(
        name="row_count",
        table="raw_maint",
        observed=n,
        expected=3286,
        status="PASS" if n == 3286 else "WARN",
        details="Total esperado de eventos em PdM_maint.csv."
    ))

    # 2. Domínio de comp.
    # comp deve conter apenas comp1, comp2, comp3 e comp4.
    df = pd.read_sql("""
        SELECT comp, COUNT(*) AS c
        FROM raw_maint
        GROUP BY comp
    """, engine)

    expected_components = {"comp1", "comp2", "comp3", "comp4"}
    observed_components = set(df["comp"])

    results.append(run_check(
        name="component_domain",
        table="raw_maint",
        observed=observed_components,
        expected=expected_components,
        status="PASS" if observed_components == expected_components else "WARN",
        details="Verifica se comp contém apenas os componentes esperados."
    ))

    # 3. Nulos em colunas obrigatórias.
    df = pd.read_sql("""
        SELECT
            SUM(CASE WHEN datetime IS NULL THEN 1 ELSE 0 END) AS null_datetime,
            SUM(CASE WHEN machineID IS NULL THEN 1 ELSE 0 END) AS null_machineID,
            SUM(CASE WHEN comp IS NULL THEN 1 ELSE 0 END) AS null_comp
        FROM raw_maint
    """, engine)

    nulls = {
        "datetime": int(df.loc[0, "null_datetime"]),
        "machineID": int(df.loc[0, "null_machineID"]),
        "comp": int(df.loc[0, "null_comp"]),
    }

    results.append(run_check(
        name="required_nulls",
        table="raw_maint",
        observed=nulls,
        expected="0 nulos em datetime, machineID e comp",
        status="PASS" if sum(nulls.values()) == 0 else "FAIL",
        details="Campos obrigatórios não devem ter valores ausentes."
    ))


def check_failures(engine, results):
    """Valida volume, domínio e nulos da tabela raw_failures."""

    # 1. Volume esperado da tabela.
    # O dataset PdM_failures.csv costuma ter 761 falhas reais.
    df = pd.read_sql("SELECT COUNT(*) AS n FROM raw_failures", engine)
    n = int(df.loc[0, "n"])

    results.append(run_check(
        name="row_count",
        table="raw_failures",
        observed=n,
        expected=761,
        status="PASS" if n == 761 else "WARN",
        details="Total esperado de eventos em PdM_failures.csv."
    ))

    # 2. Domínio de failure.
    # failure deve conter apenas comp1, comp2, comp3 e comp4.
    df = pd.read_sql("""
        SELECT failure, COUNT(*) AS c
        FROM raw_failures
        GROUP BY failure
    """, engine)

    expected_failures = {"comp1", "comp2", "comp3", "comp4"}
    observed_failures = set(df["failure"])

    results.append(run_check(
        name="failure_domain",
        table="raw_failures",
        observed=observed_failures,
        expected=expected_failures,
        status="PASS" if observed_failures == expected_failures else "WARN",
        details="Verifica se failure contém apenas os componentes esperados."
    ))

    # 3. Nulos em colunas obrigatórias.
    df = pd.read_sql("""
        SELECT
            SUM(CASE WHEN datetime IS NULL THEN 1 ELSE 0 END) AS null_datetime,
            SUM(CASE WHEN machineID IS NULL THEN 1 ELSE 0 END) AS null_machineID,
            SUM(CASE WHEN failure IS NULL THEN 1 ELSE 0 END) AS null_failure
        FROM raw_failures
    """, engine)

    nulls = {
        "datetime": int(df.loc[0, "null_datetime"]),
        "machineID": int(df.loc[0, "null_machineID"]),
        "failure": int(df.loc[0, "null_failure"]),
    }

    results.append(run_check(
        name="required_nulls",
        table="raw_failures",
        observed=nulls,
        expected="0 nulos em datetime, machineID e failure",
        status="PASS" if sum(nulls.values()) == 0 else "FAIL",
        details="Campos obrigatórios não devem ter valores ausentes."
    ))


def check_referential_integrity(engine, results):
    """Verifica se eventos e leituras apontam para máquinas cadastradas."""

    # 1. machineIDs órfãos na telemetria.
    # Um machineID órfão é um ID que aparece numa tabela de eventos/leitura,
    # mas não existe em raw_machines.
    checks = {
        "raw_telemetry": "SELECT DISTINCT t.machineID FROM raw_telemetry t LEFT JOIN raw_machines m USING (machineID) WHERE m.machineID IS NULL",
        "raw_errors": "SELECT DISTINCT t.machineID FROM raw_errors t LEFT JOIN raw_machines m USING (machineID) WHERE m.machineID IS NULL",
        "raw_maint": "SELECT DISTINCT t.machineID FROM raw_maint t LEFT JOIN raw_machines m USING (machineID) WHERE m.machineID IS NULL",
        "raw_failures": "SELECT DISTINCT t.machineID FROM raw_failures t LEFT JOIN raw_machines m USING (machineID) WHERE m.machineID IS NULL",
    }

    for table, query in checks.items():
        df = pd.read_sql(query, engine)
        orphan_count = len(df)
        orphan_ids = df["machineID"].tolist()

        results.append(run_check(
            name="machineID_referential_integrity",
            table=table,
            observed=orphan_ids,
            expected="[]",
            status="PASS" if orphan_count == 0 else "FAIL",
            details="Todos os machineIDs devem existir em raw_machines."
        ))


def check_telemetry_gaps(engine, results):
    """Verifica continuidade horária e diária da tabela raw_telemetry."""

    # 1. Leituras por máquina.
    # O esperado neste dataset é 8.761 timestamps por máquina.
    df = pd.read_sql("""
        SELECT
            machineID,
            COUNT(DISTINCT datetime) AS horas_com_leitura
        FROM raw_telemetry
        GROUP BY machineID
    """, engine)

    min_hours = int(df["horas_com_leitura"].min())
    max_hours = int(df["horas_com_leitura"].max())
    machines_not_8761 = df[df["horas_com_leitura"] != 8761]["machineID"].tolist()

    results.append(run_check(
        name="hourly_readings_per_machine",
        table="raw_telemetry",
        observed=f"min={min_hours}, max={max_hours}, maquinas_fora={machines_not_8761}",
        expected="8761 leituras por máquina",
        status="PASS" if len(machines_not_8761) == 0 else "WARN",
        details="Confere se todas as máquinas têm a mesma quantidade esperada de leituras horárias."
    ))

    # 2. Dias com quantidade diferente de 24 leituras.
    # Atenção: primeiro e último dia podem ter menos de 24 leituras se o dataset
    # começa ou termina no meio do dia. Por isso tratamos como WARN, não FAIL.
    df = pd.read_sql("""
        WITH leituras_por_dia AS (
            SELECT
                machineID,
                DATE(datetime) AS data_leitura,
                COUNT(*) AS qtd_leituras
            FROM raw_telemetry
            GROUP BY machineID, DATE(datetime)
        )
        SELECT
            data_leitura,
            qtd_leituras,
            COUNT(*) AS qtd_maquinas_afetadas,
            GROUP_CONCAT(machineID ORDER BY machineID) AS maquinas
        FROM leituras_por_dia
        WHERE qtd_leituras <> 24
        GROUP BY data_leitura, qtd_leituras
        ORDER BY data_leitura, qtd_leituras
    """, engine)

    irregular_days = len(df)

    if irregular_days == 0:
        observed = "nenhum dia irregular"
        details = "Todas as máquinas têm 24 leituras em todos os dias."
        status = "PASS"
    else:
        observed = df.head(10).to_dict(orient="records")
        details = "Existem dias com quantidade diferente de 24 leituras; conferir se são apenas início/fim do recorte."
        status = "WARN"

    results.append(run_check(
        name="daily_24_readings",
        table="raw_telemetry",
        observed=observed,
        expected="24 leituras por máquina por dia",
        status=status,
        details=details
    ))

def main():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(CREATE_DQ))
        conn.execute(text(ALTER_DQ))
        conn.execute(text("TRUNCATE TABLE dq_results"))

    results = []
    check_machines(engine, results)
    # ... coloque também check_telemetry.. FEITO:
    check_telemetry(engine, results)
    # ... coloque também check_errors, check_maint, check_failures,
    #     check_referential_integrity, check_telemetry_gaps
    # SEGUE:
    check_errors(engine, results)
    check_maint(engine, results)
    check_failures(engine, results)
    check_referential_integrity(engine, results)
    check_telemetry_gaps(engine, results)

    df = pd.DataFrame(results)
    df.to_sql("dq_results", engine, if_exists="append", index=False)
    df.to_csv(DATA_PROCESSED / "dq_results.csv", index=False)

    print(df.groupby("status").size())

if __name__ == "__main__":
    main()
