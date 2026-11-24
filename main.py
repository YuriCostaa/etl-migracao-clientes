"""Executa a migração e gera o relatório.

Uso: python main.py [--data-corte AAAA-MM-DD]
"""

import argparse
import csv
from datetime import date
from pathlib import Path

from etl.pipeline import executar

RAIZ = Path(__file__).resolve().parent
SAIDA = RAIZ / "output"


def escrever_relatorio(res, caminho: Path, data_corte: str) -> None:
    linhas = [
        "# Relatório da migração de clientes",
        "",
        f"Data de corte das regras de relevância: {data_corte}",
        "",
        "## Reconciliação",
        "",
        "| Etapa | Registros |",
        "|---|---:|",
        f"| Total no legado | {res.total_legado} |",
        f"| Fora do escopo (RR) | {res.fora_escopo} |",
        f"| Rejeitados na validação | {res.rejeitados} |",
        f"| Carregados em bp_cliente | {res.carregados} |",
        f"| Sem destino | {res.sem_destino} |",
        "",
        f"**Status:** {'fecha (todo registro do legado tem destino)' if res.fecha else 'NÃO FECHA, verificar'}",
        "",
        "## Fora do escopo, por motivo",
        "",
        "| Motivo | Registros |",
        "|---|---:|",
        *[f"| {m} | {q} |" for m, q in res.motivos_fora.items()],
        "",
        "## Erros de validação, por regra",
        "",
        "| Regra | Ocorrências |",
        "|---|---:|",
        *[f"| {r} | {q} |" for r, q in res.erros_por_regra.items()],
        "",
    ]
    caminho.write_text("\n".join(linhas), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migração de cadastro de clientes (dados fictícios)")
    parser.add_argument("--data-corte", default=date.today().isoformat(),
                        help="data usada nas regras de relevância (padrão: hoje)")
    args = parser.parse_args()

    SAIDA.mkdir(exist_ok=True)
    banco = SAIDA / "migracao.db"
    banco.unlink(missing_ok=True)

    conn, res = executar(banco, RAIZ / "data" / "legado", RAIZ / "data" / "referencia", args.data_corte)

    with open(SAIDA / "rejeitados.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["cod_cli", "regra", "valor"])
        w.writerows(conn.execute("SELECT cod_cli, regra, valor FROM val_erros ORDER BY cod_cli, regra"))
    escrever_relatorio(res, SAIDA / "relatorio.md", args.data_corte)
    conn.close()

    print(f"Legado: {res.total_legado} | Fora do escopo: {res.fora_escopo} | "
          f"Rejeitados: {res.rejeitados} | Carregados: {res.carregados}")
    print("Reconciliação:", "OK" if res.fecha else "NÃO FECHA")
    print(f"Saída em {SAIDA}")
    return 0 if res.fecha else 1


if __name__ == "__main__":
    raise SystemExit(main())
