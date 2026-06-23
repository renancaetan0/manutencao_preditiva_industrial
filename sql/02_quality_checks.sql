-- ============================================================
-- Arquivo: sql/02_quality_checks.sql
-- Objetivo: verificar a qualidade dos dados nas tabelas raw.
-- Execute no Workbench DEPOIS de 01_create_raw_tables.sql e
-- depois que o script Python 01_ingest_to_mysql.py já rodou
-- (as tabelas precisam estar populadas com dados).
-- ============================================================

USE smurfit_pdm_lab;


-- ============================================================
-- VERIFICAÇÃO 1: Volume por tabela
-- O QUE ESTAMOS CHECANDO: se a quantidade de linhas de cada tabela
-- bate com o esperado do dataset do Kaggle.
-- VALORES ESPERADOS: machines=100, telemetry=876.100,
--                   errors=3.919, maint=3.286, failures=761
-- ============================================================

-- SELECT com valores literais + UNION ALL para criar uma tabela resumo.
-- Cada bloco SELECT conta linhas de uma tabela.
-- O texto entre aspas ('machines', 'telemetry', etc.) é um rótulo fixo
-- que você define para identificar cada linha do resultado.
-- UNION ALL empilha os resultados um abaixo do outro.
SELECT 'machines'  AS tabela, COUNT(*) AS total_linhas FROM raw_machines
UNION ALL
SELECT 'telemetry',           COUNT(*)                 FROM raw_telemetry
UNION ALL
SELECT 'errors',              COUNT(*)                 FROM raw_errors
UNION ALL
SELECT 'maint',               COUNT(*)                 FROM raw_maint
UNION ALL
SELECT 'failures',            COUNT(*)                 FROM raw_failures;


-- ============================================================
-- VERIFICAÇÃO 2: Domínio da coluna "model"
-- O QUE ESTAMOS CHECANDO: se a coluna "model" só contém valores
-- válidos ('model1', 'model2', 'model3', 'model4').
-- Um valor inesperado aqui (ex: 'Model1' com maiúscula, 'modelo3' em PT)
-- indica problema na carga dos dados.
-- ============================================================

-- GROUP BY model: agrupa as linhas por valor de model.
-- COUNT(*): conta quantas máquinas existem em cada modelo.
-- Resultado esperado: 4 linhas, uma para cada model1..model4.
SELECT
    model,       -- qual é o valor do campo model
    COUNT(*) AS total_maquinas  -- quantas máquinas têm esse modelo
FROM raw_machines
GROUP BY model   -- agrupa por valor único de model
ORDER BY model;  -- ordena alfabeticamente para facilitar leitura


-- ============================================================
-- VERIFICAÇÃO 3: Domínio da coluna "errorID"
-- O QUE ESTAMOS CHECANDO: se errorID só tem valores 'error1'...'error5'.
-- Qualquer outro valor é dado inválido ou problema de encoding.
-- ============================================================

-- Mesmo padrão de GROUP BY: agrupa por errorID e conta ocorrências.
-- Resultado esperado: 5 linhas, uma para cada error1..error5.
SELECT
    errorID,
    COUNT(*) AS total_ocorrencias
FROM raw_errors
GROUP BY errorID
ORDER BY errorID;


-- ============================================================
-- VERIFICAÇÃO 4: Período coberto pela telemetria
-- O QUE ESTAMOS CHECANDO:
--   - A data mais antiga (MIN) deve ser próxima de 2015-01-01
--   - A data mais recente (MAX) deve ser próxima de 2015-12-31
--   - Devemos ter 100 machineIDs distintos
--   - O total de linhas deve bater com o esperado (876.100 linhas)
-- ============================================================

SELECT
    MIN(datetime)              AS data_mais_antiga,    -- primeira leitura registrada
    MAX(datetime)              AS data_mais_recente,   -- última leitura registrada
    COUNT(DISTINCT machineID)  AS maquinas_distintas,  -- quantas máquinas únicas aparecem
    COUNT(*)                   AS total_leituras       -- total de linhas na tabela
FROM raw_telemetry;


-- ============================================================
-- VERIFICAÇÃO 5: Duplicatas na telemetria
-- O QUE ESTAMOS CHECANDO: se existe alguma combinação (machineID, datetime)
-- que aparece mais de uma vez — o que violaria a regra de negócio
-- "uma leitura por máquina por hora".
-- RESULTADO ESPERADO: zero linhas (nenhuma duplicata).
-- ============================================================

-- GROUP BY machineID, datetime: agrupa por par (máquina + instante).
-- COUNT(*) AS c: conta quantas linhas existem para cada par.
-- HAVING c > 1: mostra SÓ os grupos com mais de 1 linha = as duplicatas.
-- LIMIT 10: mostra no máximo 10 exemplos (se houver centenas, não queremos tudo).
SELECT
    machineID,
    datetime,
    COUNT(*) AS c        -- quantas vezes esta combinação aparece
FROM raw_telemetry
GROUP BY machineID, datetime
HAVING c > 1             -- filtra: só grupos com mais de 1 ocorrência
LIMIT 10;                -- limita a 10 exemplos para não sobrecarregar


-- ============================================================
-- VERIFICAÇÃO 6: Integridade referencial — machineIDs órfãos
-- O QUE ESTAMOS CHECANDO: se existe algum machineID em raw_telemetry
-- que NÃO tem cadastro correspondente em raw_machines.
-- Isso seria um problema de qualidade: leituras de uma "máquina fantasma".
-- RESULTADO ESPERADO: zero linhas (todos os IDs têm cadastro).
-- ============================================================

-- LEFT JOIN: traz TODOS os machineIDs da telemetria, e completa com
-- os dados de raw_machines onde houver correspondência.
-- Onde NÃO houver correspondência, m.machineID fica NULL.
-- WHERE m.machineID IS NULL: filtra só as linhas sem correspondência
-- = os "órfãos" que estão na telemetria mas não no cadastro.
-- DISTINCT: evita repetir o mesmo machineID órfão várias vezes.
SELECT DISTINCT t.machineID AS machineID_orfao
FROM raw_telemetry AS t
LEFT JOIN raw_machines AS m
    USING (machineID)       -- une onde t.machineID = m.machineID
WHERE m.machineID IS NULL;  -- filtra: só as linhas onde não houve correspondência


-- ============================================================
-- VERIFICAÇÃO 7: Continuidade temporal — lacunas na telemetria
-- O QUE ESTAMOS CHECANDO: se cada máquina tem o número esperado de
-- leituras horárias. O dataset cobre o intervalo de 2015-01-01 06:00
-- até 2016-01-01 06:00, totalizando 8.761 timestamps por máquina.
-- Com 100 máquinas, esperamos 100 × 8.761 = 876.100 leituras.
-- Esta query mostra as máquinas com MENOS leituras → possíveis lacunas.
-- ============================================================

-- COUNT(DISTINCT datetime): conta instantes únicos de cada máquina.
-- GROUP BY machineID: agrupa por máquina.
-- ORDER BY horas ASC (padrão): mostra as máquinas com menos leituras primeiro.
-- LIMIT 5: mostra as 5 máquinas com maior suspeita de lacuna.
SELECT
    machineID,
    COUNT(DISTINCT datetime) AS horas_com_leitura  -- instantes únicos por máquina
FROM raw_telemetry
GROUP BY machineID
ORDER BY horas_com_leitura ASC   -- menor primeiro = mais lacunas
LIMIT 5;

-- ============================================================
-- VERIFICAÇÃO 8: Continuidade diária — dias com quantidade diferente de 24 leituras
-- O QUE ESTAMOS CHECANDO: se cada máquina tem exatamente 24 leituras por dia,
-- assumindo que a telemetria é horária.
--
-- Se os dados são coletados de hora em hora, o esperado é:
--   1 máquina × 24 horas = 24 leituras por dia.
--
-- Quando uma máquina aparece com menos de 24 leituras em um dia, pode indicar
-- lacuna de telemetria: alguma hora não foi registrada.
--
-- Quando aparece com mais de 24 leituras, pode indicar duplicidade ou leituras
-- extras no mesmo dia.
--
-- ATENÇÃO: o primeiro e o último dia do dataset podem aparecer com menos de
-- 24 leituras se o arquivo começar ou terminar no meio do dia. Nesse caso,
-- não é necessariamente erro; é apenas o recorte temporal do dataset.
--
-- Esta query retorna somente os dias em que alguma máquina tem quantidade
-- diferente de 24 leituras, mostrando também quais máquinas foram afetadas.
-- ============================================================

-- DATE(datetime): extrai apenas a data, removendo a hora.
-- GROUP BY machineID, DATE(datetime): agrupa por máquina e por dia.
-- COUNT(*): conta quantas leituras aquela máquina teve naquele dia.
-- WHERE qtd_leituras <> 24: filtra apenas dias fora do esperado.
-- GROUP_CONCAT(machineID): lista as máquinas afetadas em uma única linha.
WITH leituras_por_dia AS (
    SELECT
        machineID,
        DATE(datetime) AS data_leitura,
        COUNT(*) AS qtd_leituras,
        MIN(datetime) AS primeira_leitura,
        MAX(datetime) AS ultima_leitura
    FROM raw_telemetry
    GROUP BY machineID, DATE(datetime)
)
SELECT
    data_leitura,
    qtd_leituras,
    COUNT(*) AS qtd_maquinas_afetadas,
    GROUP_CONCAT(machineID ORDER BY machineID) AS maquinas,
    MIN(primeira_leitura) AS primeira_leitura_no_grupo,
    MAX(ultima_leitura) AS ultima_leitura_no_grupo
FROM leituras_por_dia
WHERE qtd_leituras <> 24
GROUP BY data_leitura, qtd_leituras
ORDER BY data_leitura, qtd_leituras;