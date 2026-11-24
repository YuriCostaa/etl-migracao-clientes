"""Gera a base legada fictícia usada pelo pipeline.

Os dados são inventados e vêm com os problemas comuns de um sistema antigo:
documentos sem padrão, datas em formatos diferentes, duplicidades, cadastros
de teste, UFs inválidas e clientes inativos há anos.

Uso: python gerar_dados.py [quantidade]
"""

import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

SEMENTE = 42
PASTA = Path(__file__).parent / "data" / "legado"

NOMES = ["Ana", "Bruno", "Carla", "Diego", "Eduarda", "Felipe", "Gabriela", "Heitor", "Isabela", "João",
         "Larissa", "Marcos", "Natália", "Otávio", "Paula", "Rafael", "Sabrina", "Thiago", "Vitória", "Yuri"]
SOBRENOMES = ["Silva", "Souza", "Oliveira", "Santos", "Pereira", "Costa", "Rodrigues", "Almeida", "Lima",
              "Carvalho", "Gomes", "Ribeiro", "Martins", "Rocha", "Barbosa"]
EMPRESAS = ["Comércio", "Distribuidora", "Transportes", "Tecnologia", "Alimentos", "Construtora", "Serviços"]
CIDADES = [("Brasília", "DF"), ("Goiânia", "GO"), ("São Paulo", "SP"), ("Campinas", "SP"), ("Belo Horizonte", "MG"),
           ("Rio de Janeiro", "RJ"), ("Curitiba", "PR"), ("Porto Alegre", "RS"), ("Salvador", "BA"),
           ("Recife", "PE"), ("Fortaleza", "CE"), ("Manaus", "AM")]
RUAS = ["Rua das Flores", "Avenida Brasil", "Rua Sete de Setembro", "Quadra 104", "Avenida Paulista",
        "Rua do Comércio", "Travessa São José", "Alameda Santos"]
BAIRROS = ["Centro", "Asa Norte", "Asa Sul", "Jardim América", "Vila Nova", "Boa Vista", "Setor Bueno"]


def _dv(nums, pesos):
    r = sum(n * p for n, p in zip(nums, pesos)) % 11
    return 0 if r < 2 else 11 - r


def gerar_cpf(rnd):
    n = [rnd.randint(0, 9) for _ in range(9)]
    n.append(_dv(n, range(10, 1, -1)))
    n.append(_dv(n, range(11, 1, -1)))
    return "".join(map(str, n))


def gerar_cnpj(rnd):
    n = [rnd.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    n.append(_dv(n, p1))
    n.append(_dv(n, [6] + p1))
    return "".join(map(str, n))


def baguncar_documento(rnd, doc):
    """Simula a falta de padrão do legado: com ou sem máscara, espaços, zeros perdidos."""
    estilo = rnd.random()
    if estilo < 0.4:
        return doc
    if estilo < 0.7:
        if len(doc) == 11:
            return f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"
        return f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"
    if estilo < 0.85:
        return f" {doc} "
    return doc.lstrip("0") or doc


def data_legado(rnd, d):
    return d.strftime("%d/%m/%Y") if rnd.random() < 0.8 else d.isoformat()


def gerar(qtd=500, semente=SEMENTE):
    rnd = random.Random(semente)
    hoje = date(2026, 11, 1)
    clientes, enderecos = [], []
    documentos_usados = []

    for i in range(1, qtd + 1):
        cod = f"C{i:06d}"
        sorteio = rnd.random()
        if sorteio < 0.62:
            tipo = "F"
            nome = f"{rnd.choice(NOMES)} {rnd.choice(SOBRENOMES)} {rnd.choice(SOBRENOMES)}"
            doc = gerar_cpf(rnd)
        elif sorteio < 0.95:
            tipo = "J"
            nome = f"{rnd.choice(SOBRENOMES)} {rnd.choice(EMPRESAS)} Ltda"
            doc = gerar_cnpj(rnd)
        else:
            tipo = "E"
            nome = f"{rnd.choice(['John', 'Maria', 'Lucas', 'Sofia'])} {rnd.choice(['Smith', 'García', 'Ferreira'])}"
            doc = ""

        # problemas propositais
        problema = rnd.random()
        if problema < 0.04 and documentos_usados:
            doc = rnd.choice(documentos_usados)            # duplicidade
        elif problema < 0.07 and tipo != "E":
            doc = doc[:-1] + str((int(doc[-1]) + 1) % 10)  # dígito verificador errado
        elif problema < 0.09:
            nome = "TESTE " + nome.upper()                  # cadastro de teste
        if doc:
            documentos_usados.append(doc)

        if rnd.random() < 0.3:
            nome = nome.upper()
        elif rnd.random() < 0.1:
            nome = "  " + nome.lower() + " "

        cadastro = hoje - timedelta(days=rnd.randint(30, 4000))
        ultima = cadastro + timedelta(days=rnd.randint(0, (hoje - cadastro).days))
        status = rnd.choices(["A", "I", "B"], weights=[80, 15, 5])[0]
        email = "" if rnd.random() < 0.1 else (
            nome.strip().split()[-1].lower() + str(i) + rnd.choices(["@email.com", "@empresa.com.br", "#email.com", "@email"], weights=[60, 34, 3, 3])[0])
        ddd = rnd.choice(["61", "62", "11", "21", "31", "41", "51"])
        tel = rnd.choice([
            f"{ddd}9{rnd.randint(10000000, 99999999)}",
            f"({ddd}) 9{rnd.randint(1000, 9999)}-{rnd.randint(1000, 9999)}",
            f"+55 {ddd} 3{rnd.randint(100, 999)}-{rnd.randint(1000, 9999)}",
            "",
        ])

        clientes.append({
            "COD_CLI": cod, "NOME": nome, "TIPO": tipo, "DOCUMENTO": baguncar_documento(rnd, doc) if doc else "",
            "EMAIL": email, "TELEFONE": tel, "DT_CADASTRO": data_legado(rnd, cadastro),
            "DT_ULTIMA_COMPRA": data_legado(rnd, ultima), "STATUS": status,
        })

        if rnd.random() < 0.05:
            continue  # cliente sem endereço
        cidade, uf = rnd.choice(CIDADES)
        pais = "BR"
        if tipo == "E":
            cidade, uf, pais = rnd.choice([("Buenos Aires", "", "AR"), ("Lisboa", "", "PT"), ("Miami", "", "US")])
        if rnd.random() < 0.15:
            uf = uf.lower()
        if rnd.random() < 0.03:
            uf = "XX"
        pais_legado = {"BR": rnd.choice(["BR", "BRA", "Brasil", "brasil"]), "AR": "AR", "PT": "Portugal", "US": "USA"}[pais]
        cep = f"{rnd.randint(10000, 99999)}{rnd.randint(0, 999):03d}" if pais == "BR" else ""
        if cep and rnd.random() < 0.5:
            cep = f"{cep[:5]}-{cep[5:]}"
        if cep and rnd.random() < 0.03:
            cep = cep[:-2]
        enderecos.append({
            "COD_CLI": cod, "LOGRADOURO": rnd.choice(RUAS), "NUMERO": str(rnd.randint(1, 2000)),
            "BAIRRO": rnd.choice(BAIRROS), "CIDADE": cidade, "UF": uf, "CEP": cep, "PAIS": pais_legado,
        })

    return clientes, enderecos


def salvar(linhas, caminho):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]), delimiter=";")
        w.writeheader()
        w.writerows(linhas)


if __name__ == "__main__":
    qtd = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    clientes, enderecos = gerar(qtd)
    salvar(clientes, PASTA / "clientes.csv")
    salvar(enderecos, PASTA / "enderecos.csv")
    print(f"{len(clientes)} clientes e {len(enderecos)} endereços gerados em {PASTA}")
