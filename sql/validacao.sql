-- Validação dos dados transformados
-- Todas as verificações contra as tabelas de check ficam em uma única query:
-- trf_clientes é lida uma vez, cruzada com a lista de regras, e cada regra
-- devolve o valor com problema (ou NULL quando está tudo certo).

INSERT INTO val_erros (cod_cli, regra, valor)
SELECT cod_cli, regra, valor
FROM (
    SELECT
        t.cod_cli,
        r.regra,
        CASE r.regra
            WHEN 'DOCUMENTO_INVALIDO' THEN
                CASE WHEN t.tipo_pessoa IN ('PF', 'PJ') AND t.cpf IS NULL AND t.cnpj IS NULL
                     THEN COALESCE(NULLIF(TRIM(s.documento), ''), '(vazio)') END
            WHEN 'UF_NAO_CADASTRADA' THEN
                CASE WHEN t.pais = 'BR' AND t.uf IS NOT NULL AND u.uf IS NULL THEN t.uf END
            WHEN 'PAIS_NAO_CADASTRADO' THEN
                CASE WHEN p.pais IS NULL THEN COALESCE(t.pais, '(vazio)') END
            WHEN 'GRUPO_NAO_CADASTRADO' THEN
                CASE WHEN g.grupo IS NULL THEN COALESCE(t.grupo_conta, '(vazio)') END
            WHEN 'CEP_OBRIGATORIO' THEN
                CASE WHEN t.pais = 'BR' AND t.logradouro IS NOT NULL AND t.cep IS NULL
                     THEN COALESCE(NULLIF(TRIM(e.cep), ''), '(vazio)') END
            WHEN 'EMAIL_INVALIDO' THEN
                CASE WHEN t.email IS NULL AND NULLIF(TRIM(s.email), '') IS NOT NULL THEN s.email END
            WHEN 'SEM_ENDERECO' THEN
                CASE WHEN t.logradouro IS NULL THEN '(sem endereço no legado)' END
        END AS valor
    FROM trf_clientes t
    JOIN stg_clientes s            ON s.cod_cli = t.cod_cli
    LEFT JOIN stg_enderecos e      ON e.cod_cli = t.cod_cli
    LEFT JOIN ref_uf u             ON u.uf = t.uf
    LEFT JOIN ref_pais p           ON p.pais = t.pais
    LEFT JOIN ref_grupo_conta g    ON g.grupo = t.grupo_conta
    CROSS JOIN (
        SELECT 'DOCUMENTO_INVALIDO' AS regra UNION ALL
        SELECT 'UF_NAO_CADASTRADA'           UNION ALL
        SELECT 'PAIS_NAO_CADASTRADO'         UNION ALL
        SELECT 'GRUPO_NAO_CADASTRADO'        UNION ALL
        SELECT 'CEP_OBRIGATORIO'             UNION ALL
        SELECT 'EMAIL_INVALIDO'              UNION ALL
        SELECT 'SEM_ENDERECO'
    ) r
)
WHERE valor IS NOT NULL;
