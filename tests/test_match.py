from reconciler.match import reconciliar
from reconciler.transform import normalize_koncili, normalize_omie


def test_reconciliar_identifica_match_exato_e_divergencia(koncili_raw_df, omie_raw_df):
    koncili = normalize_koncili(koncili_raw_df)
    omie = normalize_omie(omie_raw_df)

    resultado = reconciliar(koncili, omie)

    status_contagem = resultado["status_match"].value_counts().to_dict()

    assert status_contagem.get("CONCILIADO") == 1
    assert status_contagem.get("DIVERGENTE_VALOR") == 1


def test_reconciliar_preserva_total_de_linhas_sem_perder_registros(
    koncili_raw_df, omie_raw_df
):
    koncili = normalize_koncili(koncili_raw_df)
    omie = normalize_omie(omie_raw_df)

    resultado = reconciliar(koncili, omie)

    # nenhum registro de entrada pode "desaparecer": todo KC/OM original
    # deve estar representado em exatamente uma linha do resultado
    assert len(resultado) == max(len(koncili), len(omie))
