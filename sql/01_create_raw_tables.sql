-- ============================================================
-- Arquivo: sql/01_create_raw_tables.sql
-- Objetivo: criar as 5 tabelas raw que receberão os CSVs do Kaggle.
-- Execute DEPOIS do 00_create_database.sql.
-- ============================================================

-- Sem este USE, o MySQL não saberia em qual banco criar as tabelas.
-- Mesmo que você já tenha selecionado o banco no Workbench,
-- é boa prática incluir o USE no arquivo — garante que sempre
-- vai para o banco certo, independentemente de qual estava selecionado.
USE smurfit_pdm_lab;


-- -------------------------------------------------------
-- TABELA: raw_machines
-- Fonte: PdM_machines.csv
-- Conteúdo: cadastro de cada máquina (modelo e idade)
-- Volume: 100 linhas (1 por máquina)
-- -------------------------------------------------------

-- Apaga a tabela se já existir antes de recriar.
-- Útil durante desenvolvimento: você pode rodar este script várias vezes
-- sem se preocupar com erros de "tabela já existe".
DROP TABLE IF EXISTS raw_machines;

CREATE TABLE raw_machines (

  -- machineID: identificador numérico da máquina (1 a 100 no dataset).
  -- INT          = número inteiro (suficiente para 100 máquinas)
  -- PRIMARY KEY  = chave única — não podem existir duas máquinas com o mesmo ID.
  --               O MySQL cria automaticamente um índice nesta coluna,
  --               tornando buscas por machineID muito rápidas.
  machineID INT          PRIMARY KEY,

  -- model: qual modelo é a máquina (valores: 'model1', 'model2', 'model3', 'model4').
  -- VARCHAR(20)  = texto variável de até 20 caracteres
  --               (20 é mais do que suficiente para 'model4')
  -- NOT NULL     = campo obrigatório — toda máquina deve ter um modelo definido.
  model     VARCHAR(20)  NOT NULL,

  -- age: idade da máquina em anos (0 a 20 no dataset).
  -- INT      = número inteiro (idade não tem casas decimais)
  -- NOT NULL = obrigatório
  age       INT          NOT NULL

);


-- -------------------------------------------------------
-- TABELA: raw_telemetry
-- Fonte: PdM_telemetry.csv
-- Conteúdo: leituras horárias dos 4 sensores de cada máquina
-- Volume: 876.100 linhas — esta é a maior tabela do projeto
-- -------------------------------------------------------
DROP TABLE IF EXISTS raw_telemetry;

CREATE TABLE raw_telemetry (

  -- datetime: o instante exato da leitura (ex: '2015-01-01 06:00:00').
  -- DATETIME = guarda data + hora juntos, com precisão de segundos.
  -- NOT NULL = toda leitura precisa de um timestamp — sem ele, a linha é inútil.
  datetime   DATETIME    NOT NULL,

  -- machineID: qual máquina gerou esta leitura.
  -- INT      = inteiro (1 a 100)
  -- NOT NULL = obrigatório — toda leitura deve ser associada a uma máquina.
  machineID  INT         NOT NULL,

  -- volt: leitura do sensor de voltagem.
  -- DECIMAL(10,4) = número com até 10 dígitos no total e 4 casas decimais.
  --   Exemplo: 168.4923 (7 dígitos inteiros + 4 decimais = 11 caracteres com o ponto)
  --   Por que 4 casas decimais? É a precisão que os sensores usam no dataset.
  -- Sem NOT NULL: leituras podem falhar ocasionalmente (sensor offline, dado faltando).
  --   NULL aqui significa "leitura não disponível", não zero.
  volt       DECIMAL(10,4),

  -- rotate: leitura do sensor de rotação (RPM — rotações por minuto).
  -- Mesma lógica de tipo e precisão que "volt".
  rotate     DECIMAL(10,4),

  -- pressure: leitura do sensor de pressão.
  pressure   DECIMAL(10,4),

  -- vibration: leitura do sensor de vibração.
  vibration  DECIMAL(10,4),

  -- PRIMARY KEY composta: a COMBINAÇÃO de machineID + datetime deve ser única.
  -- Por quê composta? Porque machineID sozinho não é único (uma máquina tem
  -- milhares de leituras) e datetime sozinho também não (100 máquinas leram
  -- no mesmo instante). Mas a COMBINAÇÃO dos dois é única: uma máquina
  -- não pode ter duas leituras no mesmo segundo.
  --
  -- Benefício extra: o MySQL cria automaticamente um índice nessa chave composta.
  -- Consultas que filtram por machineID ou por (machineID + datetime) serão
  -- rápidas mesmo com 876.100 linhas.
  PRIMARY KEY (machineID, datetime)

);


-- -------------------------------------------------------
-- TABELA: raw_errors
-- Fonte: PdM_errors.csv
-- Conteúdo: erros registrados durante a operação (não causam parada)
-- Volume: ~3.919 linhas
-- -------------------------------------------------------
DROP TABLE IF EXISTS raw_errors;

CREATE TABLE raw_errors (

  -- id: identificador sintético (gerado pelo banco, não vem do CSV).
  -- BIGINT         = inteiro grande (para suportar muitos registros)
  -- AUTO_INCREMENT = o MySQL gera automaticamente: 1, 2, 3, 4...
  --                  Você não precisa informar este valor na inserção.
  -- PRIMARY KEY    = chave única desta tabela
  --
  -- Por que usar um id sintético aqui, em vez de (machineID, datetime) como na telemetria?
  -- Porque a mesma máquina PODE ter dois erros no exato mesmo instante
  -- (dois sensores disparam ao mesmo tempo). Se usássemos (machineID, datetime)
  -- como PK, o segundo erro seria rejeitado. Com um id AUTO_INCREMENT, cada erro
  -- é inserido independentemente.
  id          BIGINT       AUTO_INCREMENT PRIMARY KEY,

  -- datetime: quando o erro ocorreu.
  -- NOT NULL = obrigatório.
  datetime    DATETIME     NOT NULL,

  -- machineID: qual máquina gerou o erro.
  machineID   INT          NOT NULL,

  -- errorID: código do erro ('error1' a 'error5' no dataset).
  -- VARCHAR(20) = texto de até 20 caracteres
  -- NOT NULL    = obrigatório
  errorID     VARCHAR(20)  NOT NULL,

  -- INDEX explícito em (machineID, datetime):
  -- Por que criar este índice se já temos o id como PK?
  -- Porque nossas consultas vão buscar erros de uma máquina específica
  -- em um período de tempo — ex: "erros da máquina 7 nas 24h antes da falha".
  -- O índice (machineID, datetime) torna esse tipo de consulta muito rápido.
  -- O nome "idx_errors_machine_dt" é um apelido que você escolhe (por convenção,
  -- começa com "idx_").
  INDEX idx_errors_machine_dt (machineID, datetime)

);


-- -------------------------------------------------------
-- TABELA: raw_maint
-- Fonte: PdM_maint.csv
-- Conteúdo: histórico de manutenções (substituição de componentes)
-- Volume: ~3.286 linhas
-- -------------------------------------------------------
DROP TABLE IF EXISTS raw_maint;

CREATE TABLE raw_maint (

  -- Mesmo padrão de id sintético que raw_errors.
  -- Justificativa: uma máquina pode ter dois componentes substituídos
  -- no mesmo instante (manutenção de múltiplos itens em uma parada).
  id          BIGINT       AUTO_INCREMENT PRIMARY KEY,

  datetime    DATETIME     NOT NULL,
  machineID   INT          NOT NULL,

  -- comp: qual componente foi substituído ('comp1', 'comp2', 'comp3', 'comp4').
  comp        VARCHAR(20)  NOT NULL,

  -- Mesmo índice de busca por máquina + período que raw_errors.
  INDEX idx_maint_machine_dt (machineID, datetime)

);


-- -------------------------------------------------------
-- TABELA: raw_failures
-- Fonte: PdM_failures.csv
-- Conteúdo: falhas reais (paradas da máquina)
-- Volume: ~761 linhas — o evento mais raro e mais importante do projeto
-- -------------------------------------------------------
DROP TABLE IF EXISTS raw_failures;

CREATE TABLE raw_failures (

  -- id sintético pelo mesmo motivo: falhas múltiplas simultâneas são possíveis.
  id          BIGINT       AUTO_INCREMENT PRIMARY KEY,

  datetime    DATETIME     NOT NULL,
  machineID   INT          NOT NULL,

  -- failure: qual componente falhou ('comp1', 'comp2', 'comp3', 'comp4').
  -- É o componente que causou a parada — diferente de "comp" em raw_maint
  -- que é o componente que foi substituído (pode ser manutenção preventiva).
  failure     VARCHAR(20)  NOT NULL,

  INDEX idx_failures_machine_dt (machineID, datetime)

);


-- Confirmação visual de que o script terminou sem erros.
SELECT 'Tabelas raw criadas com sucesso.' AS status;