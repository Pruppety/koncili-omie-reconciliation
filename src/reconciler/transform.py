"""Normalização das duas fontes para um schema canônico único.

Cada fonte tem nomes de coluna e formatos próprios; aqui elas convergem
para o mesmo formato (datas, valores, documentos, CPF/CNPJ) antes de
qualquer tentativa de casamento (match.py), que assim não precisa saber
nada sobre a origem dos dados.
"""

import re

import pandas as pd
from loguru import logger

from reconciler.schemas import canonical_schema


def _limpar_documento(valor: str) -> str:
    """Mantém só dígitos — remove pontuação de CPF/CNPJ e máscaras de documento."""
    return re.sub(r"\D", "", str(valor or ""))


def normalize_koncili(df: pd.DataFrame) -> pd.DataFrame:
    canonical = pd.DataFrame(
        {
            "id_origem": df["codigo_transacao"],
            "origem": "KONCILI",
            "data": pd.to_datetime(df["data_pagamento"]).dt.normalize(),
            "valor": df["valor_pago"].round(2),
            "cpf_cnpj": df["cpf_cnpj_pagador"].map(_limpar_documento),
            "numero_documento": df["numero_documento"].map(_limpar_documento),
            "descricao": df["descricao"].fillna("").str.strip().str.upper(),
        }
    )
    logger.debug(f"Koncili normalizada: {len(canonical)} linhas")
    return canonical_schema.validate(canonical)


def normalize_omie(df: pd.DataFrame) -> pd.DataFrame:
    canonical = pd.DataFrame(
        {
            "id_origem": df["codigo_lancamento"],
            "origem": "OMIE",
            "data": pd.to_datetime(df["data_lancamento"]).dt.normalize(),
            "valor": df["valor_lancamento"].round(2),
            "cpf_cnpj": df["cpf_cnpj"].map(_limpar_documento),
            "numero_documento": df["numero_documento"].map(_limpar_documento),
            "descricao": df["descricao"].fillna("").str.strip().str.upper(),
        }
    )
    logger.debug(f"Omie normalizada: {len(canonical)} linhas")
    return canonical_schema.validate(canonical)
