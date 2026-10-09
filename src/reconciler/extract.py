"""Camada de extração: lê os arquivos brutos e valida o schema de entrada.

Mantida separada da transformação de propósito — se amanhã a fonte
mudar de Excel para uma API ou um banco, só este módulo muda.
"""

from pathlib import Path

import pandas as pd
from loguru import logger

from reconciler.schemas import koncili_raw_schema, omie_raw_schema


def extract_koncili(path: Path) -> pd.DataFrame:
    logger.info(f"Lendo exportação Koncili de {path}")
    df = pd.read_excel(path, dtype={"cpf_cnpj_pagador": str, "numero_documento": str})
    df = koncili_raw_schema.validate(df)
    logger.info(f"Koncili: {len(df)} linhas lidas e validadas")
    return df


def extract_omie(path: Path) -> pd.DataFrame:
    logger.info(f"Lendo exportação Omie de {path}")
    df = pd.read_excel(path, dtype={"cpf_cnpj": str, "numero_documento": str})
    df = omie_raw_schema.validate(df)
    logger.info(f"Omie: {len(df)} linhas lidas e validadas")
    return df
