"""Regras de transformação: levam o registro do layout legado para o layout de destino.

Todas as regras de transformação ficam aqui, separadas das regras de relevância.
Quando um valor não pode ser convertido, ele fica vazio (None) e a validação
registra o erro depois.
"""

import re
from datetime import datetime

from .documentos import cnpj_valido, cpf_valido, formatar_cep, formatar_telefone, somente_digitos

# De-para de país: o legado usa vários jeitos de escrever o mesmo país
DE_PARA_PAIS = {
    "BR": "BR", "BRA": "BR", "BRASIL": "BR",
    "AR": "AR", "ARGENTINA": "AR",
    "PT": "PT", "PORTUGAL": "PT",
    "US": "US", "USA": "US", "EUA": "US", "ESTADOS UNIDOS": "US",
}

# De-para de tipo de cliente do legado para tipo de pessoa e grupo de contas
DE_PARA_TIPO = {
    "F": ("PF", "PF01"),
    "J": ("PJ", "PJ01"),
    "E": ("EX", "EX01"),
}

PARTICULAS = {"da", "de", "do", "das", "dos", "e"}
SIGLAS = {"LTDA", "ME", "EPP", "SA", "S/A", "EIRELI"}
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


def normalizar_nome(nome: str | None) -> str | None:
    """Tira espaços extras e aplica caixa de título, mantendo partículas e siglas."""
    partes = (nome or "").split()
    if not partes:
        return None
    saida = []
    for i, p in enumerate(partes):
        if p.upper() in SIGLAS:
            saida.append(p.upper())
        elif i > 0 and p.lower() in PARTICULAS:
            saida.append(p.lower())
        else:
            saida.append(p.capitalize())
    return " ".join(saida)


def converter_data(valor: str | None) -> str | None:
    """Aceita dd/mm/aaaa ou aaaa-mm-dd e devolve aaaa-mm-dd."""
    valor = (valor or "").strip()
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(valor, formato).date().isoformat()
        except ValueError:
            pass
    return None


def converter_documento(tipo: str, documento: str | None) -> tuple[str | None, str | None]:
    """Devolve (cpf, cnpj) formatados. Recupera zeros à esquerda perdidos no legado."""
    d = somente_digitos(documento)
    if not d:
        return None, None
    if tipo == "F":
        d = d.zfill(11)
        return (f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if cpf_valido(d) else None), None
    if tipo == "J":
        d = d.zfill(14)
        return None, (f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}" if cnpj_valido(d) else None)
    return None, None


def converter_email(email: str | None) -> str | None:
    email = (email or "").strip().lower()
    return email if EMAIL_RE.match(email) else None


def transformar(cliente: dict, endereco: dict | None) -> dict:
    """Recebe as linhas do legado (cliente e endereço) e devolve a linha de destino."""
    tipo = (cliente.get("tipo") or "").strip().upper()
    tipo_pessoa, grupo = DE_PARA_TIPO.get(tipo, (None, None))
    cpf, cnpj = converter_documento(tipo, cliente.get("documento"))

    linha = {
        "cod_cli": cliente["cod_cli"],
        "grupo_conta": grupo,
        "tipo_pessoa": tipo_pessoa,
        "nome": normalizar_nome(cliente.get("nome")),
        "cpf": cpf,
        "cnpj": cnpj,
        "email": converter_email(cliente.get("email")),
        "telefone": formatar_telefone(cliente.get("telefone")),
        "dt_cadastro": converter_data(cliente.get("dt_cadastro")),
        "logradouro": None, "numero": None, "bairro": None, "cidade": None,
        "uf": None, "cep": None,
        "pais": "BR" if tipo in ("F", "J") else None,
    }

    if endereco:
        pais = DE_PARA_PAIS.get((endereco.get("pais") or "").strip().upper())
        uf = (endereco.get("uf") or "").strip().upper() or None
        linha.update({
            "logradouro": normalizar_nome(endereco.get("logradouro")),
            "numero": (endereco.get("numero") or "").strip() or None,
            "bairro": normalizar_nome(endereco.get("bairro")),
            "cidade": normalizar_nome(endereco.get("cidade")),
            "uf": uf if pais == "BR" else None,
            "cep": formatar_cep(endereco.get("cep")) if pais == "BR" else None,
            "pais": pais or (endereco.get("pais") or "").strip().upper() or None,
        })
    return linha

