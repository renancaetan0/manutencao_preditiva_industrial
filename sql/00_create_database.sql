-- ============================================================
-- Arquivo: sql/00_create_database.sql
-- Objetivo: criar o banco de dados principal do projeto.
-- Execute ESTE arquivo PRIMEIRO, antes de qualquer outro SQL.
-- ============================================================

-- DROP DATABASE IF EXISTS: apaga o banco inteiro (se existir) antes de recriar.
-- Por que isso? Para garantir que estamos começando do zero, sem resquícios
-- de execuções anteriores. Em desenvolvimento, é seguro.
-- ATENÇÃO: em um banco de produção real, NUNCA faça isso sem backup —
-- apaga todos os dados permanentemente!
DROP DATABASE IF EXISTS smurfit_pdm_lab;

-- CREATE DATABASE: cria o banco de dados.
-- "smurfit_pdm_lab" é o nome — aparecerá na lista de conexões do Workbench.
CREATE DATABASE smurfit_pdm_lab
  CHARACTER SET utf8mb4
  -- utf8mb4: define o conjunto de caracteres (encoding) do banco.
  -- utf8mb4 é o Unicode completo moderno — suporta acentos, caracteres
  -- especiais de todos os idiomas e até emojis.
  -- Sempre use utf8mb4. O "utf8" antigo do MySQL tem um bug histórico
  -- (não suporta todos os caracteres Unicode de 4 bytes).

  COLLATE utf8mb4_unicode_ci;
  -- COLLATE define as regras de comparação e ordenação de texto.
  -- unicode_ci = "unicode, case-insensitive":
  --   - "ci" (case-insensitive) = 'Model3' e 'model3' são considerados iguais
  --   - Isso é o comportamento esperado para dados como nomes de modelos e categorias

-- USE: diz ao MySQL "a partir daqui, execute os próximos comandos
-- DENTRO do banco smurfit_pdm_lab".
-- Sem este comando, o MySQL não saberia em qual banco criar as tabelas.
-- É como "abrir a pasta certa" antes de trabalhar.
USE smurfit_pdm_lab;

-- SELECT com texto literal: apenas exibe uma mensagem de confirmação.
-- 'Banco smurfit_pdm_lab criado.' é um valor de texto fixo (não vem de nenhuma tabela).
-- AS status renomeia a coluna de saída para "status".
-- Serve só para você ver na tela do Workbench que o script chegou até aqui sem erro.
SELECT 'Banco smurfit_pdm_lab criado.' AS status;