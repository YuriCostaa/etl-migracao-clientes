"""Pipeline de migração: extração → relevância → transformação → validação → carga."""

import csv
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from .documentos import somente_digitos
from .transformacao import transformar

RAIZ = Path(__file__).resolve().parent.parent
SQL = RAIZ / "sql"

COLUNAS_DESTINO = [
    "grupo_conta", "tipo_pessoa", "nome", "cpf", "cnpj", "email", "telefone", "dt_cadastro",
    "logradouro", "numero", "bairro", "cidade", "uf", "cep", "pais",
]


@dataclass
class Resultado:
    total_legado: int = 0
    fora_escopo: int = 0
    rejeitados: int = 0
    carregados: int = 0
    sem_destino: int = 0
    motivos_fora: dict = field(default_factory=dict)
    erros_por_regra: dict = field(default_factory=dict)

    @property
    def fecha(self) -> bool:
        """A migração fecha quando todo registro do legado tem um destino."""
        return self.sem_destino == 0 and self.total_legado == self.fora_escopo + self.rejeitados + self.carregados


def conectar(caminho: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    conn.create_function("digitos", 1, somente_digitos, deterministic=True)
    return conn


def ler_csv(caminho: Path, separador: str) -> list[dict]:
    with open(caminho, encoding="utf-8", newline="") as f:
        return [{k.lower(): v for k, v in linha.items()} for linha in csv.DictReader(f, delimiter=separador)]


def inserir(conn, tabela: str, linhas: list[dict]) -> None:
    if not linhas:
        return
    cols = list(linhas[0])
    conn.executemany(
        f"INSERT INTO {tabela} ({', '.join(cols)}) VALUES ({', '.join(':' + c for c in cols)})", linhas
    )


def extrair(conn, pasta_legado: Path, pasta_ref: Path) -> None:
    """Carrega os arquivos do legado e as tabelas de check sem alterar nada."""
    inserir(conn, "stg_clientes", ler_csv(pasta_legado / "clientes.csv", ";"))
    inserir(conn, "stg_enderecos", ler_csv(pasta_legado / "enderecos.csv", ";"))
    inserir(conn, "ref_uf", ler_csv(pasta_ref / "uf.csv", ","))
    inserir(conn, "ref_pais", ler_csv(pasta_ref / "pais.csv", ","))
    inserir(conn, "ref_grupo_conta", ler_csv(pasta_ref / "grupo_conta.csv", ","))


def aplicar_relevancia(conn, data_corte: str) -> None:
    conn.execute((SQL / "relevancia.sql").read_text(encoding="utf-8"), {"data_corte": data_corte})


def aplicar_transformacao(conn) -> None:
    enderecos = {e["cod_cli"]: dict(e) for e in conn.execute("SELECT * FROM stg_enderecos")}
    clientes = conn.execute(
        "SELECT s.* FROM stg_clientes s JOIN rr_clientes r ON r.cod_cli = s.cod_cli WHERE r.dentro_escopo = 1"
    ).fetchall()
    inserir(conn, "trf_clientes", [transformar(dict(c), enderecos.get(c["cod_cli"])) for c in clientes])


def aplicar_validacao(conn) -> None:
    conn.executescript((SQL / "validacao.sql").read_text(encoding="utf-8"))


def carregar(conn) -> None:
    cols = ", ".join(COLUNAS_DESTINO)
    conn.execute(
        f"""INSERT INTO bp_cliente (cod_legado, {cols})
            SELECT cod_cli, {cols} FROM trf_clientes t
            WHERE NOT EXISTS (SELECT 1 FROM val_erros v WHERE v.cod_cli = t.cod_cli)
            ORDER BY cod_cli"""
    )


def reconciliar(conn) -> Resultado:
    linha = conn.execute((SQL / "reconciliacao.sql").read_text(encoding="utf-8")).fetchone()
    res = Resultado(**dict(linha))
    res.motivos_fora = {
        m: q for m, q in conn.execute(
            """SELECT CASE WHEN motivo LIKE 'Documento duplicado%' THEN 'Documento duplicado' ELSE motivo END m,
                      COUNT(*) FROM rr_clientes WHERE dentro_escopo = 0 GROUP BY m ORDER BY 2 DESC""")
    }
    res.erros_por_regra = {
        r: q for r, q in conn.execute("SELECT regra, COUNT(*) FROM val_erros GROUP BY regra ORDER BY 2 DESC")
    }
    return res


def executar(banco: Path | str, pasta_legado: Path, pasta_ref: Path, data_corte: str) -> tuple[sqlite3.Connection, Resultado]:
    conn = conectar(banco)
    conn.executescript((SQL / "schema.sql").read_text(encoding="utf-8"))
    with conn:
        extrair(conn, pasta_legado, pasta_ref)
        aplicar_relevancia(conn, data_corte)
        aplicar_transformacao(conn)
        aplicar_validacao(conn)
        carregar(conn)
    return conn, reconciliar(conn)
