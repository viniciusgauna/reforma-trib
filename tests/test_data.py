import pandas as pd
import pytest

from data import (
    CST_DESCRICOES,
    _fix_mojibake,
    _restaurar_bytes_invisiveis_perdidos,
    load_classificacoes_tributarias,
    load_incidencia_issqn,
    load_indop,
    load_tabela_geral,
)


def _mojibake(texto_correto: str) -> str:
    """Gera mojibake genuíno a partir de texto correto (o mesmo tipo de
    corrupção que o arquivo real sofreu: UTF-8 lido como Latin-1),
    evitando digitar bytes invisíveis à mão nos testes."""
    return texto_correto.encode("utf-8").decode("latin-1")


def test_fix_mojibake_corrige_texto_corrompido():
    assert _fix_mojibake(_mojibake("Situações tributadas")) == "Situações tributadas"
    assert _fix_mojibake(_mojibake("Áreas de livre comércio")) == "Áreas de livre comércio"


def test_fix_mojibake_preserva_texto_ja_correto():
    assert _fix_mojibake("Situações tributadas") == "Situações tributadas"
    assert _fix_mojibake("simples sem acento") == "simples sem acento"


def test_restaurar_bytes_perdidos_caso_nbsp_antes_de_a_craseado():
    # "Ã" seguido de espaço ASCII simples é sinal de NBSP perdido antes do
    # "à" (o texto de origem realmente tem 2 espaços depois do "à" aqui —
    # peculiaridade do dado oficial, preservada de propósito).
    bruto = "destinado Ã  mistura"
    reparado = _restaurar_bytes_invisiveis_perdidos(bruto)
    assert _fix_mojibake(reparado) == "destinado à  mistura"


def test_restaurar_bytes_perdidos_caso_areas():
    # Mesma ideia, mas para o byte de controle (0x81) perdido antes de
    # "reas" em "Áreas".
    mojibake_correto = _mojibake("Áreas de livre comércio")
    bruto = mojibake_correto.replace("\x81", "")
    reparado = _restaurar_bytes_invisiveis_perdidos(bruto)
    assert _fix_mojibake(reparado) == "Áreas de livre comércio"


def test_restaurar_bytes_perdidos_caso_agua():
    bruto = "Nota Fiscal da Ãgua e Saneamento"
    reparado = _restaurar_bytes_invisiveis_perdidos(bruto)
    assert _fix_mojibake(reparado) == "Nota Fiscal da Água e Saneamento"


class TestLoadClassificacoesTributarias:
    """Suíte para o detalhamento de cClassTrib (Portal da Conformidade Fácil).

    Esta é a tabela transcrita manualmente a partir de um PDF/JSON — os
    testes abaixo existem principalmente para pegar regressões de
    transcrição (registros perdidos, encoding quebrado, código duplicado).
    """

    @staticmethod
    @pytest.fixture(scope="class")
    def df():
        return load_classificacoes_tributarias()

    def test_tem_164_registros_unicos(self, df):
        assert len(df) == 164
        assert df["codigo"].is_unique

    def test_codigos_tem_6_digitos(self, df):
        assert (df["codigo"].str.len() == 6).all()
        assert df["codigo"].str.isdigit().all()

    def test_cst_derivado_do_codigo_e_conhecido(self, df):
        assert (df["cst"] == df["codigo"].str[:3]).all()
        assert set(df["cst"]).issubset(set(CST_DESCRICOES))

    def test_grupo_220_aliquota_fixa_presente(self, df):
        # grupo que faltou na primeira transcrição (161 vs 164 registros)
        codigos_220 = df[df["cst"] == "220"]["codigo"].tolist()
        assert sorted(codigos_220) == ["220001", "220002", "220003"]

    def test_sem_mojibake_residual(self, df):
        campos_texto = ["descricao", "tratamento_tributario", "tipo_aliquota", "cst_descricao"]
        for campo in campos_texto:
            quebrados = df[df[campo].str.contains("Ã", na=False, regex=False)]
            assert quebrados.empty, f"mojibake residual em '{campo}': {quebrados['codigo'].tolist()}"

    def test_percentuais_de_reducao_sao_numericos_e_no_intervalo(self, df):
        for col in ["percentual_reducao_cbs", "percentual_reducao_ibs_uf", "percentual_reducao_ibs_mun"]:
            assert pd.api.types.is_numeric_dtype(df[col])
            assert df[col].between(0, 100).all()


def test_load_indop_carrega_sem_erro():
    df = load_indop()
    assert not df.empty
    assert {"indop", "tipo_operacao"}.issubset(df.columns)
    assert (df["indop"].str.len() == 6).all()


def test_load_tabela_geral_carrega_sem_erro():
    df = load_tabela_geral()
    assert not df.empty
    assert {"item_lc116", "cclasstrib", "nbs"}.issubset(df.columns)
    # forward-fill não deve deixar buracos nas colunas hierárquicas
    assert df["item_lc116"].notna().all()
    assert df["cclasstrib"].notna().all()


def test_load_incidencia_issqn_carrega_sem_erro():
    df = load_incidencia_issqn()
    assert not df.empty
    assert "codigo_tributacao_nacional" in df.columns
