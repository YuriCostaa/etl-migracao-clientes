-- Reconciliação origem x destino
-- Todo registro do legado precisa terminar em exatamente um destes grupos:
-- fora do escopo, rejeitado na validação ou carregado em bp_cliente.

SELECT
    (SELECT COUNT(*) FROM stg_clientes)                                       AS total_legado,
    (SELECT COUNT(*) FROM rr_clientes WHERE dentro_escopo = 0)                AS fora_escopo,
    (SELECT COUNT(DISTINCT cod_cli) FROM val_erros)                           AS rejeitados,
    (SELECT COUNT(*) FROM bp_cliente)                                         AS carregados,
    (SELECT COUNT(*) FROM stg_clientes s
       WHERE NOT EXISTS (SELECT 1 FROM rr_clientes r WHERE r.cod_cli = s.cod_cli AND r.dentro_escopo = 0)
         AND NOT EXISTS (SELECT 1 FROM val_erros v WHERE v.cod_cli = s.cod_cli)
         AND NOT EXISTS (SELECT 1 FROM bp_cliente b WHERE b.cod_legado = s.cod_cli)) AS sem_destino;
