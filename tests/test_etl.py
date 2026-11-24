import sqlite3
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import gerar_dados  # noqa: E402
from etl.documentos import cnpj_valido, cpf_valido, formatar_cep, formatar_telefone  # noqa: E402
from etl.pipeline import executar  # noqa: E402
from etl.transformacao import converter_data, converter_documento, normalizar_nome, transformar  # noqa: E402


# ---------- documentos ----------

def test_cpf_valido_e_invalido():
    assert cpf_valido("529.982.247-25")
    assert not cpf_valido("529.982.247-24")
    assert not cpf_valido("111.111.111-11")


def test_cnpj_valido_e_invalido():
    assert cnpj_valido("11.222.333/0001-81")
    assert not cnpj_valido("11.222.333/0001-82")


def test_cep_e_telefone():
    assert formatar_cep("70640058") == "70640-058"
    assert formatar_cep("7064005") is None
    assert formatar_telefone("+55 61 99814-7046") == "(61) 99814-7046"
    assert formatar_telefone("6133251234") == "(61) 3325-1234"


# ---------- transformação ----------

def test_recupera_zeros_a_esquerda_do_cpf():
    cpf, cnpj = converter_documento("F", "1234567890")  # CPF 01234567890 sem o zero
    assert cpf == "012.345.678-90" and cnpj is None


def test_normaliza_nome():
    assert normalizar_nome("  MARIA DA SILVA  ") == "Maria da Silva"
    assert normalizar_nome("costa transportes ltda") == "Costa Transportes LTDA"


@pytest.mark.parametrize("entrada,esperado", [("05/03/2021", "2021-03-05"), ("2021-03-05", "2021-03-05"), ("31/02/2021", None)])
def test_converte_datas(entrada, esperado):
    assert converter_data(entrada) == esperado


def test_transformar_aplica_de_para_de_pais_e_uf():
    cliente = {"cod_cli": "C1", "nome": "ana souza", "tipo": "F", "documento": "52998224725",
               "email": "ANA@EMAIL.COM", "telefone": "61998147046", "dt_cadastro": "01/02/2020"}
    endereco = {"logradouro": "rua das flores", "numero": "10", "bairro": "centro", "cidade": "brasília",
                "uf": "df", "cep": "70640058", "pais": "Brasil"}
    t = transformar(cliente, endereco)
    assert t["pais"] == "BR" and t["uf"] == "DF" and t["cep"] == "70640-058"
    assert t["grupo_conta"] == "PF01" and t["cpf"] == "529.982.247-25"
    assert t["email"] == "ana@email.com" and t["dt_cadastro"] == "2020-02-01"


# ---------- pipeline completo ----------

@pytest.fixture(scope="module")
def migracao(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("dados")
    clientes, enderecos = gerar_dados.gerar(300, semente=7)
    gerar_dados.salvar(clientes, pasta / "clientes.csv")
    gerar_dados.salvar(enderecos, pasta / "enderecos.csv")
    conn, res = executar(pasta / "teste.db", pasta, RAIZ / "data" / "referencia", "2026-11-01")
    yield conn, res
    conn.close()


def test_reconciliacao_fecha(migracao):
    _, res = migracao
    assert res.total_legado == 300
    assert res.fecha
    assert res.carregados > 0 and res.fora_escopo > 0 and res.rejeitados > 0


def test_destino_respeita_tabelas_de_check(migracao):
    conn, _ = migracao
    fora = conn.execute(
        """SELECT COUNT(*) FROM bp_cliente b
           LEFT JOIN ref_uf u ON u.uf = b.uf
           LEFT JOIN ref_pais p ON p.pais = b.pais
           WHERE p.pais IS NULL OR (b.uf IS NOT NULL AND u.uf IS NULL)""").fetchone()[0]
    assert fora == 0


def test_sem_documento_duplicado_no_destino(migracao):
    conn, _ = migracao
    dup = conn.execute(
        """SELECT COUNT(*) FROM (SELECT COALESCE(cpf, cnpj) d FROM bp_cliente
           WHERE COALESCE(cpf, cnpj) IS NOT NULL GROUP BY d HAVING COUNT(*) > 1)""").fetchone()[0]
    assert dup == 0


def test_cadastros_de_teste_ficam_fora(migracao):
    conn, _ = migracao
    assert conn.execute("SELECT COUNT(*) FROM bp_cliente WHERE UPPER(nome) LIKE 'TESTE%'").fetchone()[0] == 0
