"""Gera planilhas sintéticas de Koncili e Omie para demo/testes.

Importante: isso existe porque dados reais de conciliação financeira de
uma empresa NUNCA devem ir para um repositório público. Este script cria
dados fictícios (via Faker) que reproduzem a mesma estrutura e os mesmos
tipos de caso (conciliado, divergente, órfão em cada lado) sem expor
nada sensível.
"""

import random
from datetime import timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

fake = Faker("pt_BR")
random.seed(42)
Faker.seed(42)

N_CONCILIADOS = 60
N_DIVERGENTES_VALOR = 10
N_SOMENTE_KONCILI = 8
N_SOMENTE_OMIE = 8
N_FUZZY = 10  # mesmo lançamento, descrição com pequenas diferenças

STATUS_KONCILI = ["PENDENTE", "CONCILIADO", "CANCELADO"]
CATEGORIAS_OMIE = ["VENDAS", "SERVICOS", "FORNECEDORES", "TARIFAS BANCARIAS"]


def _empresa_e_documento():
    cnpj = fake.cnpj()
    descricao = f"PAGTO {fake.company().upper()}"
    numero_documento = str(fake.unique.random_number(digits=8, fix_len=True))
    return cnpj, descricao, numero_documento


def gerar_dados(output_dir: Path) -> None:
    koncili_rows = []
    omie_rows = []

    data_base = fake.date_between(start_date="-60d", end_date="-1d")

    # 1. Casos conciliados perfeitamente (match exato)
    for _ in range(N_CONCILIADOS):
        cnpj, descricao, doc = _empresa_e_documento()
        data = data_base + timedelta(days=random.randint(0, 59))
        valor = round(random.uniform(150, 25000), 2)

        koncili_rows.append(
            {
                "codigo_transacao": f"KC{fake.unique.random_number(digits=10, fix_len=True)}",
                "data_pagamento": data,
                "valor_pago": valor,
                "cpf_cnpj_pagador": cnpj,
                "numero_documento": doc,
                "descricao": descricao,
                "status_conciliacao": "CONCILIADO",
            }
        )
        omie_rows.append(
            {
                "codigo_lancamento": f"OM{fake.unique.random_number(digits=10, fix_len=True)}",
                "data_lancamento": data,
                "valor_lancamento": valor,
                "cpf_cnpj": cnpj,
                "numero_documento": doc,
                "categoria": random.choice(CATEGORIAS_OMIE),
                "descricao": descricao,
                "conta_bancaria": fake.iban(),
            }
        )

    # 2. Mesmo documento, valor divergente (ex: taxa não refletida em um dos lados)
    for _ in range(N_DIVERGENTES_VALOR):
        cnpj, descricao, doc = _empresa_e_documento()
        data = data_base + timedelta(days=random.randint(0, 59))
        valor_koncili = round(random.uniform(150, 25000), 2)
        valor_omie = round(valor_koncili + random.uniform(5, 150), 2)

        koncili_rows.append(
            {
                "codigo_transacao": f"KC{fake.unique.random_number(digits=10, fix_len=True)}",
                "data_pagamento": data,
                "valor_pago": valor_koncili,
                "cpf_cnpj_pagador": cnpj,
                "numero_documento": doc,
                "descricao": descricao,
                "status_conciliacao": "CONCILIADO",
            }
        )
        omie_rows.append(
            {
                "codigo_lancamento": f"OM{fake.unique.random_number(digits=10, fix_len=True)}",
                "data_lancamento": data,
                "valor_lancamento": valor_omie,
                "cpf_cnpj": cnpj,
                "numero_documento": doc,
                "categoria": random.choice(CATEGORIAS_OMIE),
                "descricao": descricao,
                "conta_bancaria": fake.iban(),
            }
        )

    # 3. Só existe na Koncili (ex: pagamento ainda não lançado no ERP)
    for _ in range(N_SOMENTE_KONCILI):
        cnpj, descricao, doc = _empresa_e_documento()
        koncili_rows.append(
            {
                "codigo_transacao": f"KC{fake.unique.random_number(digits=10, fix_len=True)}",
                "data_pagamento": data_base + timedelta(days=random.randint(0, 59)),
                "valor_pago": round(random.uniform(150, 25000), 2),
                "cpf_cnpj_pagador": cnpj,
                "numero_documento": doc,
                "descricao": descricao,
                "status_conciliacao": random.choice(STATUS_KONCILI),
            }
        )

    # 4. Só existe na Omie (ex: lançamento manual sem contrapartida na Koncili)
    for _ in range(N_SOMENTE_OMIE):
        cnpj, descricao, doc = _empresa_e_documento()
        omie_rows.append(
            {
                "codigo_lancamento": f"OM{fake.unique.random_number(digits=10, fix_len=True)}",
                "data_lancamento": data_base + timedelta(days=random.randint(0, 59)),
                "valor_lancamento": round(random.uniform(150, 25000), 2),
                "cpf_cnpj": cnpj,
                "numero_documento": doc,
                "categoria": random.choice(CATEGORIAS_OMIE),
                "descricao": descricao,
                "conta_bancaria": fake.iban(),
            }
        )

    # 5. Mesmo lançamento, documento diferente, descrição parecida -> exige fuzzy match
    for _ in range(N_FUZZY):
        cnpj, descricao, _ = _empresa_e_documento()
        data = data_base + timedelta(days=random.randint(0, 59))
        valor = round(random.uniform(150, 25000), 2)

        koncili_rows.append(
            {
                "codigo_transacao": f"KC{fake.unique.random_number(digits=10, fix_len=True)}",
                "data_pagamento": data,
                "valor_pago": valor,
                "cpf_cnpj_pagador": cnpj,
                "numero_documento": str(fake.unique.random_number(digits=8, fix_len=True)),
                "descricao": descricao,
                "status_conciliacao": "CONCILIADO",
            }
        )
        omie_rows.append(
            {
                "codigo_lancamento": f"OM{fake.unique.random_number(digits=10, fix_len=True)}",
                "data_lancamento": data,
                "valor_lancamento": valor,
                "cpf_cnpj": cnpj,
                # numero_documento diferente de propósito -> não casa no match exato
                "numero_documento": str(fake.unique.random_number(digits=8, fix_len=True)),
                "categoria": random.choice(CATEGORIAS_OMIE),
                "descricao": descricao + " LTDA",  # pequena variação textual
                "conta_bancaria": fake.iban(),
            }
        )

    df_koncili = pd.DataFrame(koncili_rows).sample(frac=1, random_state=42).reset_index(drop=True)
    df_omie = pd.DataFrame(omie_rows).sample(frac=1, random_state=42).reset_index(drop=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    df_koncili.to_excel(output_dir / "koncili.xlsx", index=False)
    df_omie.to_excel(output_dir / "omie.xlsx", index=False)

    print(f"Gerado: {output_dir / 'koncili.xlsx'} ({len(df_koncili)} linhas)")
    print(f"Gerado: {output_dir / 'omie.xlsx'} ({len(df_omie)} linhas)")


if __name__ == "__main__":
    projeto_raiz = Path(__file__).resolve().parents[1]
    gerar_dados(projeto_raiz / "data" / "raw")
