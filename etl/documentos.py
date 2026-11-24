"""Validação e formatação de CPF, CNPJ, CEP e telefone."""

import re


def somente_digitos(valor: str | None) -> str:
    return re.sub(r"\D", "", valor or "")


def _digito(numeros: list[int], pesos: list[int]) -> int:
    resto = sum(n * p for n, p in zip(numeros, pesos)) % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf: str | None) -> bool:
    d = somente_digitos(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    nums = [int(c) for c in d]
    dv1 = _digito(nums[:9], list(range(10, 1, -1)))
    dv2 = _digito(nums[:9] + [dv1], list(range(11, 1, -1)))
    return nums[9] == dv1 and nums[10] == dv2


def cnpj_valido(cnpj: str | None) -> bool:
    d = somente_digitos(cnpj)
    if len(d) != 14 or d == d[0] * 14:
        return False
    nums = [int(c) for c in d]
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    dv1 = _digito(nums[:12], pesos1)
    dv2 = _digito(nums[:12] + [dv1], pesos2)
    return nums[12] == dv1 and nums[13] == dv2


def formatar_documento(doc: str | None) -> str | None:
    """Devolve o CPF ou CNPJ formatado, ou None se não for válido."""
    d = somente_digitos(doc)
    if cpf_valido(d):
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if cnpj_valido(d):
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return None


def formatar_cep(cep: str | None) -> str | None:
    d = somente_digitos(cep)
    return f"{d[:5]}-{d[5:]}" if len(d) == 8 else None


def formatar_telefone(tel: str | None) -> str | None:
    d = somente_digitos(tel)
    if d.startswith("55") and len(d) in (12, 13):
        d = d[2:]
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return None
