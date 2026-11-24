-- Estrutura do banco usado na migração (SQLite).
-- stg_*  : dados brutos do legado, exatamente como vieram
-- ref_*  : tabelas de check (valores aceitos no sistema de destino)
-- rr_*   : resultado das regras de relevância (dentro ou fora do escopo)
-- trf_*  : dados transformados no layout de destino
-- val_*  : erros encontrados na validação
-- bp_cliente : tabela final, só com registros válidos

DROP TABLE IF EXISTS stg_clientes;
CREATE TABLE stg_clientes (
    cod_cli TEXT, nome TEXT, tipo TEXT, documento TEXT, email TEXT, telefone TEXT,
    dt_cadastro TEXT, dt_ultima_compra TEXT, status TEXT
);

DROP TABLE IF EXISTS stg_enderecos;
CREATE TABLE stg_enderecos (
    cod_cli TEXT, logradouro TEXT, numero TEXT, bairro TEXT, cidade TEXT, uf TEXT, cep TEXT, pais TEXT
);

DROP TABLE IF EXISTS ref_uf;
CREATE TABLE ref_uf (uf TEXT PRIMARY KEY, nome TEXT, regiao TEXT);

DROP TABLE IF EXISTS ref_pais;
CREATE TABLE ref_pais (pais TEXT PRIMARY KEY, nome TEXT);

DROP TABLE IF EXISTS ref_grupo_conta;
CREATE TABLE ref_grupo_conta (grupo TEXT PRIMARY KEY, descricao TEXT);

DROP TABLE IF EXISTS rr_clientes;
CREATE TABLE rr_clientes (cod_cli TEXT PRIMARY KEY, dentro_escopo INTEGER NOT NULL, motivo TEXT);

DROP TABLE IF EXISTS trf_clientes;
CREATE TABLE trf_clientes (
    cod_cli TEXT PRIMARY KEY,
    grupo_conta TEXT, tipo_pessoa TEXT, nome TEXT, cpf TEXT, cnpj TEXT, email TEXT, telefone TEXT,
    dt_cadastro TEXT, logradouro TEXT, numero TEXT, bairro TEXT, cidade TEXT, uf TEXT, cep TEXT, pais TEXT
);

DROP TABLE IF EXISTS val_erros;
CREATE TABLE val_erros (cod_cli TEXT, regra TEXT, valor TEXT);

DROP TABLE IF EXISTS bp_cliente;
CREATE TABLE bp_cliente (
    id_bp INTEGER PRIMARY KEY AUTOINCREMENT,
    cod_legado TEXT UNIQUE NOT NULL,
    grupo_conta TEXT NOT NULL REFERENCES ref_grupo_conta(grupo),
    tipo_pessoa TEXT NOT NULL,
    nome TEXT NOT NULL,
    cpf TEXT, cnpj TEXT, email TEXT, telefone TEXT,
    dt_cadastro TEXT NOT NULL,
    logradouro TEXT, numero TEXT, bairro TEXT, cidade TEXT,
    uf TEXT REFERENCES ref_uf(uf),
    cep TEXT,
    pais TEXT NOT NULL REFERENCES ref_pais(pais)
);
