# Classificação Tributária IBS/CBS

Painel de consulta para a Reforma Tributária do Consumo (IBS/CBS): a partir de uma descrição de serviço, um Item da LC 116, um código NBS ou um cClassTrib, mostra a classificação tributária completa — alíquota, percentuais de redução, indicadores de crédito, documentos fiscais relacionados e regras de incidência do ISSQN.

**App no ar:** https://rtc-12.streamlit.app/

## Fontes dos dados

- **Anexo VI** (leiaute NFS-e Nacional / RTC) — regras de incidência do ISSQN por subitem da lista de serviços.
- **Anexo VII** (indOp) — indicadores de operação.
- **Anexo VIII** — correlação entre Item LC 116, NBS, indOp e cClassTrib.
- **Portal da Conformidade Fácil** (SVRS/gov.br) — detalhamento oficial de cada cClassTrib: percentuais de redução de IBS/CBS, indicadores de crédito, tipo de alíquota e DFes relacionados.

## Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`.

## Estrutura do projeto

| Arquivo | Conteúdo |
|---|---|
| `app.py` | Interface (Streamlit) — busca e apresentação dos dados. |
| `data.py` | Carregamento e normalização das planilhas/JSON oficiais (com cache). |
| `logic.py` | Funções puras (busca sem acento, resumo de percentuais) — sem depender do Streamlit, para poderem ser testadas isoladamente. |
| `classificacoes_tributarias.json` | Detalhamento de cada cClassTrib, transcrito do Portal da Conformidade Fácil. |
| `plain.css` | Estilo visual do app (inspirado no [plain-css](https://github.com/ilyadzh/plain-css)). |
| `.streamlit/config.toml` | Força o tema claro (o `plain.css` não foi pensado para modo escuro). |

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest -v
```

Cobre: correção de encoding (mojibake) dos dados transcritos, carregamento e integridade das tabelas (164 cClassTrib únicos), busca tolerante a acento, e testes de fumaça de todos os fluxos de busca da UI (via `streamlit.testing.v1.AppTest`).

## Deploy

Hospedado no [Streamlit Community Cloud](https://share.streamlit.io), conectado diretamente a este repositório — qualquer push na branch `master` atualiza o app automaticamente.
