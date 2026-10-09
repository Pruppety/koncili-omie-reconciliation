import pandas as pd

from reconciler.transform import normalize_koncili, normalize_omie


def test_normalize_koncili_limpa_documento_e_upper_descricao(koncili_raw_df):
    resultado = normalize_koncili(koncili_raw_df)

    assert resultado.loc[0, "cpf_cnpj"] == "12345678000199"
    assert resultado.loc[0, "numero_documento"] == "00000001"
    assert resultado.loc[0, "descricao"] == "PAGTO FORNECEDOR A"
    assert resultado.loc[0, "origem"] == "KONCILI"
    assert pd.api.types.is_datetime64_any_dtype(resultado["data"])


def test_normalize_omie_mantem_mesma_quantidade_de_linhas(omie_raw_df):
    resultado = normalize_omie(omie_raw_df)

    assert len(resultado) == len(omie_raw_df)
    assert set(resultado["origem"]) == {"OMIE"}
