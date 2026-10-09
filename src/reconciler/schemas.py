"""Contratos de dados (data contracts) usando pandera.

Por que isso existe: pipelines financeiros que leem planilhas externas
quebram silenciosamente quando alguém muda o nome de uma coluna ou o
formato de uma data. Validar o schema ANTES de transformar é a primeira
linha de defesa — se a Koncili ou a Omie mudar o layout de exportação,
o pipeline falha de forma explícita e legível, em vez de gerar um
relatório de conciliação errado sem ninguém notar.
"""

import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

koncili_raw_schema = DataFrameSchema(
    {
        "codigo_transacao": Column(str, unique=True),
        "data_pagamento": Column(pa.dtypes.DateTime),
        "valor_pago": Column(float, Check.gt(0)),
        "cpf_cnpj_pagador": Column(str),
        "numero_documento": Column(str),
        "descricao": Column(str, nullable=True),
        "status_conciliacao": Column(
            str, Check.isin(["PENDENTE", "CONCILIADO", "CANCELADO"])
        ),
    },
    strict=False,
    coerce=True,
)

omie_raw_schema = DataFrameSchema(
    {
        "codigo_lancamento": Column(str, unique=True),
        "data_lancamento": Column(pa.dtypes.DateTime),
        "valor_lancamento": Column(float, Check.gt(0)),
        "cpf_cnpj": Column(str),
        "numero_documento": Column(str),
        "categoria": Column(str, nullable=True),
        "descricao": Column(str, nullable=True),
        "conta_bancaria": Column(str, nullable=True),
    },
    strict=False,
    coerce=True,
)

canonical_schema = DataFrameSchema(
    {
        "id_origem": Column(str),
        "origem": Column(str, Check.isin(["KONCILI", "OMIE"])),
        "data": Column(pa.dtypes.DateTime),
        "valor": Column(float, Check.gt(0)),
        "cpf_cnpj": Column(str),
        "numero_documento": Column(str),
        "descricao": Column(str, nullable=True),
    },
    strict=False,
    coerce=True,
)

resultado_schema = DataFrameSchema(
    {
        "status_match": Column(
            str,
            Check.isin(
                [
                    "CONCILIADO",
                    "DIVERGENTE_VALOR",
                    "SOMENTE_KONCILI",
                    "SOMENTE_OMIE",
                ]
            ),
        ),
        "score_confianca": Column(float, Check.in_range(0, 100), nullable=True),
    },
    strict=False,
    coerce=True,
)
