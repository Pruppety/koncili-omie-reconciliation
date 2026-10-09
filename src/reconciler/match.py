"""Lógica de casamento (matching) e classificação das reconciliações.

Estratégia em duas etapas, nunca silenciosa:
1. Match exato por chave composta (cpf_cnpj + numero_documento), com
   tolerância configurável de valor e de data.
2. Fallback fuzzy (RapidFuzz) na descrição, só para o que não casou no
   passo 1 — e sempre registrando o score de confiança na saída, para
   que nenhum match fuzzy seja aceito "no escuro".

Tudo que não casa em nenhuma das duas etapas é preservado como
SOMENTE_KONCILI / SOMENTE_OMIE — nunca descartado.
"""

import pandas as pd
from loguru import logger
from rapidfuzz import fuzz

from reconciler.config import settings
from reconciler.schemas import resultado_schema


def _match_exato(koncili: pd.DataFrame, omie: pd.DataFrame) -> pd.DataFrame:
    pares = koncili.merge(
        omie,
        on=["cpf_cnpj", "numero_documento"],
        suffixes=("_koncili", "_omie"),
        how="inner",
    )

    dentro_tolerancia_valor = (
        pares["valor_koncili"] - pares["valor_omie"]
    ).abs() <= settings.valor_tolerancia
    dentro_tolerancia_data = (
        pares["data_koncili"] - pares["data_omie"]
    ).abs().dt.days <= settings.data_tolerancia_dias

    pares = pares[dentro_tolerancia_data].copy()
    pares["status_match"] = "CONCILIADO"
    pares.loc[~dentro_tolerancia_valor[pares.index], "status_match"] = "DIVERGENTE_VALOR"
    pares["score_confianca"] = 100.0
    pares["metodo_match"] = "EXATO"
    return pares


def _match_fuzzy(
    koncili_restante: pd.DataFrame, omie_restante: pd.DataFrame
) -> pd.DataFrame:
    """Compara descrição + proximidade de valor/data para o que não casou no match exato."""
    candidatos = []
    omie_usados = set()

    for _, linha_k in koncili_restante.iterrows():
        melhor_score = 0
        melhor_omie = None

        candidatos_omie = omie_restante[
            (omie_restante["id_origem"].isin(omie_usados) == False)
            & ((omie_restante["data"] - linha_k["data"]).abs().dt.days <= settings.data_tolerancia_dias)
            & ((omie_restante["valor"] - linha_k["valor"]).abs() <= max(5.0, linha_k["valor"] * 0.02))
        ]

        for _, linha_o in candidatos_omie.iterrows():
            score = fuzz.token_sort_ratio(linha_k["descricao"], linha_o["descricao"])
            if score > melhor_score:
                melhor_score = score
                melhor_omie = linha_o

        if melhor_omie is not None and melhor_score >= settings.fuzzy_score_minimo:
            omie_usados.add(melhor_omie["id_origem"])
            registro = {
                **{f"{c}_koncili": v for c, v in linha_k.items()},
                **{f"{c}_omie": v for c, v in melhor_omie.items()},
                "status_match": "CONCILIADO",
                "score_confianca": float(melhor_score),
                "metodo_match": "FUZZY",
            }
            candidatos.append(registro)

    return pd.DataFrame(candidatos)


def reconciliar(koncili: pd.DataFrame, omie: pd.DataFrame) -> pd.DataFrame:
    exatos = _match_exato(koncili, omie)
    logger.info(f"Match exato: {len(exatos)} pares encontrados")

    koncili_restante = koncili[~koncili["id_origem"].isin(exatos.get("id_origem_koncili", []))]
    omie_restante = omie[~omie["id_origem"].isin(exatos.get("id_origem_omie", []))]

    fuzzy = _match_fuzzy(koncili_restante, omie_restante)
    logger.info(f"Match fuzzy: {len(fuzzy)} pares encontrados")

    conciliados = pd.concat([exatos, fuzzy], ignore_index=True) if len(fuzzy) else exatos

    ids_koncili_conciliados = set(conciliados.get("id_origem_koncili", []))
    ids_omie_conciliados = set(conciliados.get("id_origem_omie", []))

    somente_koncili = koncili[~koncili["id_origem"].isin(ids_koncili_conciliados)].copy()
    somente_koncili.columns = [f"{c}_koncili" for c in somente_koncili.columns]
    somente_koncili["status_match"] = "SOMENTE_KONCILI"
    somente_koncili["score_confianca"] = None
    somente_koncili["metodo_match"] = "SEM_PAR"

    somente_omie = omie[~omie["id_origem"].isin(ids_omie_conciliados)].copy()
    somente_omie.columns = [f"{c}_omie" for c in somente_omie.columns]
    somente_omie["status_match"] = "SOMENTE_OMIE"
    somente_omie["score_confianca"] = None
    somente_omie["metodo_match"] = "SEM_PAR"

    resultado = pd.concat(
        [conciliados, somente_koncili, somente_omie], ignore_index=True
    )

    logger.info(
        f"Resultado final: {len(resultado)} linhas "
        f"({resultado['status_match'].value_counts().to_dict()})"
    )

    return resultado_schema.validate(resultado)
