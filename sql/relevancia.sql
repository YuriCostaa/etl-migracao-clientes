-- Regras de relevância (RR)
-- Aqui só se decide o que entra ou não na migração, com o motivo.
-- Nenhuma regra de transformação é aplicada nesta etapa.
-- A primeira regra que se aplica define o motivo (ordem do CASE).
-- digitos() é uma função registrada pelo pipeline em Python.

INSERT INTO rr_clientes (cod_cli, dentro_escopo, motivo)
WITH base AS (
    SELECT
        c.cod_cli,
        UPPER(TRIM(c.nome))          AS nome,
        c.status,
        digitos(c.documento)         AS doc,
        c.tipo,
        -- datas do legado vêm como dd/mm/aaaa ou aaaa-mm-dd
        CASE WHEN c.dt_ultima_compra LIKE '__/__/____'
             THEN substr(c.dt_ultima_compra, 7, 4) || '-' || substr(c.dt_ultima_compra, 4, 2) || '-' || substr(c.dt_ultima_compra, 1, 2)
             ELSE c.dt_ultima_compra END AS ultima_compra
    FROM stg_clientes c
),
doc_normalizado AS (
    SELECT *,
        CASE WHEN tipo = 'F' AND doc <> '' THEN substr('00000000000' || doc, -11)
             WHEN tipo = 'J' AND doc <> '' THEN substr('00000000000000' || doc, -14)
             ELSE NULL END AS doc_completo
    FROM base
),
ranking AS (
    -- para documentos repetidos, fica o cadastro com a compra mais recente
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY doc_completo ORDER BY ultima_compra DESC, cod_cli) AS ordem,
        FIRST_VALUE(cod_cli) OVER (PARTITION BY doc_completo ORDER BY ultima_compra DESC, cod_cli) AS cod_mantido
    FROM doc_normalizado
)
SELECT
    cod_cli,
    CASE
        WHEN nome LIKE 'TESTE%' THEN 0
        WHEN status = 'B' THEN 0
        WHEN status = 'I' AND ultima_compra < date(:data_corte, '-5 years') THEN 0
        WHEN doc_completo IS NOT NULL AND ordem > 1 THEN 0
        ELSE 1
    END AS dentro_escopo,
    CASE
        WHEN nome LIKE 'TESTE%' THEN 'Cadastro de teste'
        WHEN status = 'B' THEN 'Cliente bloqueado no legado'
        WHEN status = 'I' AND ultima_compra < date(:data_corte, '-5 years') THEN 'Inativo sem compras há mais de 5 anos'
        WHEN doc_completo IS NOT NULL AND ordem > 1 THEN 'Documento duplicado (mantido ' || cod_mantido || ')'
        ELSE 'Dentro do escopo'
    END AS motivo
FROM ranking;
