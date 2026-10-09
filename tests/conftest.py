import pandas as pd
import pytest


@pytest.fixture
def koncili_raw_df():
    return pd.DataFrame(
        [
            {
                "codigo_transacao": "KC1",
                "data_pagamento": "2026-01-10",
                "valor_pago": 1000.00,
                "cpf_cnpj_pagador": "12.345.678/0001-99",
                "numero_documento": "00000001",
                "descricao": "pagto fornecedor a",
                "status_conciliacao": "CONCILIADO",
            },
            {
                "codigo_transacao": "KC2",
                "data_pagamento": "2026-01-11",
                "valor_pago": 500.00,
                "cpf_cnpj_pagador": "98.765.432/0001-11",
                "numero_documento": "00000002",
                "descricao": "pagto fornecedor b",
                "status_conciliacao": "PENDENTE",
            },
        ]
    )


@pytest.fixture
def omie_raw_df():
    return pd.DataFrame(
        [
            {
                "codigo_lancamento": "OM1",
                "data_lancamento": "2026-01-10",
                "valor_lancamento": 1000.00,
                "cpf_cnpj": "12.345.678/0001-99",
                "numero_documento": "00000001",
                "categoria": "FORNECEDORES",
                "descricao": "PAGTO FORNECEDOR A",
                "conta_bancaria": "BR0000000000",
            },
            {
                "codigo_lancamento": "OM2",
                "data_lancamento": "2026-01-11",
                "valor_lancamento": 550.00,  # divergente de propósito
                "cpf_cnpj": "98.765.432/0001-11",
                "numero_documento": "00000002",
                "categoria": "FORNECEDORES",
                "descricao": "PAGTO FORNECEDOR B",
                "conta_bancaria": "BR0000000001",
            },
        ]
    )
