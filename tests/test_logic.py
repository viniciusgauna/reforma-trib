import pandas as pd

from logic import contains, normalizar, resumo_reducao


def test_normalizar_remove_acentos():
    assert normalizar("saúde") == "saude"
    assert normalizar("Água") == "Agua"
    assert normalizar("informação") == "informacao"


def test_normalizar_texto_sem_acento_fica_igual():
    assert normalizar("saude") == "saude"


def test_contains_encontra_com_ou_sem_acento():
    serie = pd.Series(["Planos de assistência à saúde", "Serviços de informática"])

    # a query sem acento deve encontrar o dado acentuado
    assert contains(serie, "saude").tolist() == [True, False]
    # a query acentuada continua funcionando
    assert contains(serie, "saúde").tolist() == [True, False]


def test_contains_ignora_maiusculas_minusculas():
    serie = pd.Series(["Fornecimento de Serviços"])
    assert bool(contains(serie, "SERVIÇOS").iloc[0]) is True


def test_contains_trata_valores_nulos_sem_erro():
    serie = pd.Series(["saúde", None, float("nan")])
    resultado = contains(serie, "saude")
    assert resultado.tolist() == [True, False, False]


def test_resumo_reducao_sem_reducao():
    linha = pd.Series({"possui_reducao": False})
    assert resumo_reducao(linha) == "—"


def test_resumo_reducao_percentual_unico_quando_iguais():
    linha = pd.Series({
        "possui_reducao": True,
        "percentual_reducao_cbs": 60,
        "percentual_reducao_ibs_uf": 60,
        "percentual_reducao_ibs_mun": 60,
    })
    assert resumo_reducao(linha) == "60%"


def test_resumo_reducao_detalhado_quando_diferentes():
    linha = pd.Series({
        "possui_reducao": True,
        "percentual_reducao_cbs": 100,
        "percentual_reducao_ibs_uf": 60,
        "percentual_reducao_ibs_mun": 60,
    })
    resumo = resumo_reducao(linha)
    assert "CBS 100%" in resumo
    assert "IBS-UF 60%" in resumo
    assert "IBS-Mun 60%" in resumo
