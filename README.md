# Migração de Dados: Cadastro de Clientes

Pipeline ETL que migra o cadastro de clientes de um sistema legado para um modelo de destino no formato de Business Partner, como acontece em projetos de migração para ERP. O projeto segue as etapas usadas nesse tipo de trabalho: extração, regras de relevância, transformação, validação contra tabelas de check, carga e reconciliação entre origem e destino.

> Todos os dados são **fictícios**, gerados pelo script `gerar_dados.py`. Nenhum dado real de empresa ou cliente é usado.

## Fluxo

```
CSV do legado ──► Extração (stg_*) ──► Regras de relevância (rr_clientes)
                                              │ dentro do escopo
                                              ▼
           bp_cliente ◄── Carga ◄── Validação (val_erros) ◄── Transformação (trf_clientes)
                │
                └──► Reconciliação: legado = fora do escopo + rejeitados + carregados
```

| Etapa | Onde | O que faz |
|---|---|---|
| Extração | `etl/pipeline.py` | Lê os CSVs do legado e as tabelas de check para o staging, sem alterar nada |
| Regras de relevância | `sql/relevancia.sql` | Classifica cada cliente como dentro ou fora do escopo e registra o motivo (cadastro de teste, bloqueado, inativo há mais de 5 anos, documento duplicado). Nenhuma transformação é feita aqui |
| Transformação | `etl/transformacao.py` | Leva o registro para o layout de destino: CPF/CNPJ com máscara e zeros à esquerda recuperados, datas em ISO, nomes padronizados, de-para de país e de tipo de cliente para grupo de contas, CEP e telefone formatados |
| Validação | `sql/validacao.sql` | Confere os dados transformados contra as tabelas de check (UF, país, grupo de contas) e regras de qualidade em **uma única query** |
| Carga | `etl/pipeline.py` | Insere em `bp_cliente` só os registros sem erro |
| Reconciliação | `sql/reconciliacao.sql` | Garante que todo registro do legado terminou em exatamente um destino |

## Problemas que a base legada simula

- CPF e CNPJ com e sem máscara, com espaços e com zeros à esquerda perdidos
- Dígito verificador inválido
- Clientes duplicados pelo mesmo documento
- Cadastros de teste, clientes bloqueados e inativos antigos
- Datas em `dd/mm/aaaa` e `aaaa-mm-dd` misturadas
- País escrito de vários jeitos (`BR`, `BRA`, `Brasil`, `USA`)
- UF em minúsculas ou inexistente (`XX`), CEP incompleto, e-mail inválido e cliente sem endereço

## Como executar

Requer Python 3.10 ou superior. O pipeline usa só a biblioteca padrão (SQLite); o pytest é necessário apenas para os testes.

```bash
pip install -r requirements.txt

python gerar_dados.py          # opcional: gera uma nova base legada (500 clientes)
python main.py --data-corte 2026-11-01
python -m pytest -q
```

A execução cria a pasta `output/` com:

- `migracao.db`: banco SQLite com todas as etapas (staging, RR, transformação, erros e destino)
- `relatorio.md`: reconciliação e contagem por motivo e por regra
- `rejeitados.csv`: cada erro de validação com o cliente, a regra e o valor

## Exemplo de resultado

| Etapa | Registros |
|---|---:|
| Total no legado | 500 |
| Fora do escopo (RR) | 49 |
| Rejeitados na validação | 84 |
| Carregados em bp_cliente | 367 |
| Sem destino | 0 |

## Estrutura

```
├── data/
│   ├── legado/          # clientes.csv e enderecos.csv (fictícios)
│   └── referencia/      # tabelas de check: uf, pais, grupo_conta
├── etl/
│   ├── documentos.py    # validação de CPF, CNPJ, CEP e telefone
│   ├── transformacao.py # regras de transformação e de-paras
│   └── pipeline.py      # orquestra as etapas
├── sql/                 # schema, relevância, validação e reconciliação
├── tests/               # testes unitários e do pipeline completo
├── gerar_dados.py
└── main.py
```

## Tecnologias

Python, SQL (SQLite com CTEs e funções de janela), pytest e GitHub Actions.
