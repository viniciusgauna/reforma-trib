"""Testes de fumaça do app via streamlit.testing.v1.AppTest: garantem que
a UI roda sem exceção nos principais fluxos de busca. Não checam pixel a
pixel (isso foi validado manualmente com screenshots), só que o script
não quebra e que o conteúdo esperado aparece na árvore de elementos.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def _novo_app():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def test_carrega_sem_excecao():
    _novo_app()


def test_busca_por_servico_sem_acento_encontra_resultado():
    at = _novo_app()
    at.text_input(key="query_servico").input("saude").run()
    assert not at.exception
    assert any("encontrado" in m.value for m in at.markdown)


def test_busca_por_servico_sem_match_sugere_cclasstrib():
    at = _novo_app()
    at.text_input(key="query_servico").input("FGTS").run()
    assert not at.exception
    assert any("Nenhum item LC116" in w.value for w in at.warning)
    assert any("Encontrei" in i.value for i in at.info)


def test_busca_por_cclasstrib_sem_acento():
    at = _novo_app()
    at.text_input(key="query_cclasstrib").input("saude").run()
    assert not at.exception
    assert len(at.dataframe) > 0


def test_busca_por_indop():
    at = _novo_app()
    at.text_input(key="query_indop").input("demais").run()
    assert not at.exception


def test_busca_por_nbs():
    at = _novo_app()
    at.text_input(key="query_nbs").input("saude").run()
    assert not at.exception


def test_busca_por_issqn():
    at = _novo_app()
    at.text_input(key="query_issqn").input("101").run()
    assert not at.exception


# --- Testes adversariais (bug/seguranca) --------------------------------

CAMPOS_DE_BUSCA = [
    "query_servico", "query_nbs", "query_indop", "query_cclasstrib", "query_issqn",
]

PAYLOADS_MALICIOSOS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "' OR '1'='1'; DROP TABLE users;--",
    "../../../../etc/passwd",
    "a" * 1_000_000,  # gatilho do bug de "pattern too large" (ja corrigido)
    "(a+)+" + "a" * 50 + "!",  # tentativa classica de ReDoS
    "{{7*7}}${7*7}<%= 7*7 %>",  # tentativa de template injection
    "saude\x00.txt",
]


def test_campos_de_busca_resistem_a_payloads_maliciosos():
    for campo in CAMPOS_DE_BUSCA:
        for payload in PAYLOADS_MALICIOSOS:
            at = _novo_app()
            at.text_input(key=campo).input(payload).run()
            assert not at.exception, f"campo={campo} payload={payload[:50]!r} causou excecao"
            # o payload nunca deve ser refletido sem escape no HTML renderizado
            for m in at.markdown:
                assert payload not in str(m.value), (
                    f"payload refletido sem escape: campo={campo} payload={payload[:50]!r}"
                )
